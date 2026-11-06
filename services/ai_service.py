import logging
import pathlib
from datetime import datetime
from typing import Optional

import aiofiles

from config import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    KB_FILE_PATH,
    MAX_HISTORY_PAIRS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)

from services.scraper import clear_events_cache, get_events_text

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Knowledge Base loader
# ──────────────────────────────────────────────────────────────────────────────

_kb_cache: Optional[str] = None


async def load_knowledge_base(force: bool = False) -> str:
    """Читает knowledge_base.md и возвращает его содержимое.

    Использует кэш в памяти; при force=True или первом вызове перечитывает файл.
    """
    global _kb_cache
    if _kb_cache is None or force:
        kb_path = pathlib.Path(KB_FILE_PATH)
        if not kb_path.exists():
            logger.warning("knowledge_base.md не найден по пути: %s", KB_FILE_PATH)
            _kb_cache = "База знаний пока не заполнена."
        else:
            async with aiofiles.open(kb_path, encoding="utf-8") as f:
                _kb_cache = await f.read()
            logger.info("knowledge_base.md загружен (%d символов).", len(_kb_cache))
    return _kb_cache


def reload_knowledge_base_sync() -> None:
    """Сбрасывает кэш базы знаний и мероприятий."""
    global _kb_cache
    _kb_cache = None
    clear_events_cache()
    logger.info("Кэш knowledge_base.md и мероприятий сброшен.")


# ──────────────────────────────────────────────────────────────────────────────
# System prompt builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_system_prompt(kb_content: str, events_content: str | None = None) -> str:
    today = datetime.now().strftime("%d %B %Y, %A")

    events_section = ""
    if events_content:
        events_section = (
            "\n\n=== АКТУАЛЬНЫЕ МЕРОПРИЯТИЯ (в реальном времени с официального портала Astana Hub по Актау) ===\n"
            f"{events_content}\n"
            "=== КОНЕЦ АКТУАЛЬНЫХ МЕРОПРИЯТИЙ ===\n\n"
            "ИНСТРУКЦИЯ ПО МЕРОПРИЯТИЯМ:\n"
            "1. При любых вопросах о предстоящих или ближайших мероприятиях (на этой неделе, на следующей неделе и далее) "
            "обязательно опирайся на блок «АКТУАЛЬНЫЕ МЕРОПРИЯТИЯ» выше (это самые свежие и достоверные спарсенные данные).\n"
            "2. Выводи список мероприятий с датами, временем, названиями, описанием и прямыми ссылками на регистрацию.\n"
            "3. Если в блоке актуальных мероприятий сказано, что запланированных мероприятий нет, прямо и вежливо сообщи "
            "об этом пользователю и порекомендуй следить за анонсами в Instagram @mangystau.hub или на astanahub.com.\n"
            "4. Регулярные форматы из общей базы знаний (Open Day, Speaking Club и др.) упоминай только как постоянные "
            "направления деятельности хаба, не путая их с разовыми предстоящими событиями."
        )

    return (
        f"Сегодняшняя дата: {today}.\n\n"
        "Ты — умный и вежливый AI-помощник регионального IT-хаба Mangystau Hub (город Актау, Казахстан).\n"
        "Твоя задача — консультировать посетителей о деятельности хаба, образовательных программах, стартапах, "
        "мероприятиях, адресе, графике работы и контактах на русском и казахском языках.\n\n"
        "ПРАВИЛА И СТАНДАРТЫ ОТВЕТОВ:\n"
        "1. ЯЗЫК: Отвечай строго на том языке, на котором обратился пользователь (русский или казахский).\n"
        "2. БАЗА ЗНАНИЙ: Отвечай достоверно на основе приведённой ниже базы знаний.\n"
        "3. ПЕРЕВОД НА ОПЕРАТОРА (ОЧЕНЬ ВАЖНО):\n"
        "   - Если пользователь просит позвать человека/оператора/сотрудника;\n"
        "   - Или если ответа на вопрос пользователя нет в базе знаний и данных о мероприятиях;\n"
        "   - Или вопрос требует индивидуального рассмотрения администрацией хаба:\n"
        "   Вежливо сообщи об этом и направь пользователя к сотруднику хаба с прямой кликабельной ссылкой на WhatsApp:\n"
        "   👉 [Связаться с сотрудником в WhatsApp](https://wa.me/77789807454) (номер: +7 (778) 980-74-54 / +7 (778) 030-41-70).\n"
        "4. ФОРМАТИРОВАНИЕ: Пиши красиво и структурированно. Используй списки с маркерами, выделяй важное полужирным шрифтом, "
        "добавляй уместные эмодзи. Ссылки делай кликабельными в markdown-формате [текст](url).\n\n"
        "=== БАЗА ЗНАНИЙ ===\n"
        f"{kb_content}\n"
        "=== КОНЕЦ БАЗЫ ЗНАНИЙ ==="
        f"{events_section}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Gemini model resolver с автоматическим фоллбеком
# ──────────────────────────────────────────────────────────────────────────────

# Приоритетный список моделей (от предпочтительной к запасной).
# Резолвер перебирает их по порядку, делая реальный probe-запрос.
# При 404 / PermissionDenied переходит к следующей.
_GEMINI_CANDIDATE_CHAIN = [
    # Быстрые и доступные модели на бесплатном тарифе
    "gemini-3.5-flash-lite",
    "gemini-1.5-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-flash-lite-latest",
    "gemini-pro-latest",
]

_resolved_model: Optional[str] = None  # кэш — probe делаем только 1 раз


def reset_resolved_model() -> None:
    """Сбрасывает кэш выбранной модели (вызывается при /reload_kb)."""
    global _resolved_model
    _resolved_model = None
    logger.info("Кэш выбранной модели Gemini сброшен.")


async def _probe_model(model_name: str, genai: object) -> bool:  # type: ignore[type-arg]
    """Делает минимальный реальный запрос к модели (таймаут 4 сек).

    Возвращает True если модель ответила, False при 404/403/timeout/другой ошибке.
    """
    import asyncio

    try:
        m = genai.GenerativeModel(model_name=model_name)  # type: ignore[attr-defined]
        await asyncio.wait_for(m.generate_content_async("ping"), timeout=4.0)
        return True
    except asyncio.TimeoutError:
        logger.warning("Probe '%s' превысил таймаут 4 сек.", model_name)
        return False
    except Exception as exc:
        msg = str(exc)
        if "404" in msg or "403" in msg or "not found" in msg.lower() or "no longer available" in msg.lower():
            logger.debug("Модель '%s' недоступна: %s", model_name, msg[:120])
            return False
        # Любая другая ошибка (сеть, rate-limit) — считаем модель рабочей,
        # чтобы не пропускать её из-за временных проблем
        logger.warning("Probe '%s' вернул неожиданную ошибку: %s", model_name, msg[:120])
        return True


async def _resolve_gemini_model_async() -> str:
    """Асинхронно определяет первую рабочую модель из цепочки кандидатов.

    Порядок:
    1. GEMINI_MODEL из .env (если задана явно)
    2. _GEMINI_CANDIDATE_CHAIN
    3. Возврат последнего кандидата «как есть» при полном провале
    """
    global _resolved_model
    if _resolved_model is not None:
        return _resolved_model

    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=GEMINI_API_KEY)

    # Строим список для перебора: сначала модель из конфига, потом стандартная цепочка
    configured = GEMINI_MODEL.removeprefix("models/").strip()
    candidates = []
    if configured:
        candidates.append(configured)
    for c in _GEMINI_CANDIDATE_CHAIN:
        if c not in candidates:
            candidates.append(c)

    logger.info("Подбираю рабочую модель Gemini из %d кандидатов...", len(candidates))
    for candidate in candidates:
        logger.info("  Проверяю: %s", candidate)
        if await _probe_model(candidate, genai):
            logger.info("Выбрана модель Gemini: %s", candidate)
            _resolved_model = candidate
            return _resolved_model

    # Ничего не нашли — возвращаем последний кандидат и пусть API сам ответит
    last = candidates[-1] if candidates else "gemini-flash-latest"
    logger.error("Ни одна модель не прошла probe. Используем '%s'.", last)
    _resolved_model = last
    return _resolved_model


# ──────────────────────────────────────────────────────────────────────────────
# Gemini backend
# ──────────────────────────────────────────────────────────────────────────────

async def _ask_gemini(system_prompt: str, history: list[dict], user_message: str) -> str:
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=GEMINI_API_KEY)
        model_name = await _resolve_gemini_model_async()
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
        )

        # Переводим историю в формат Gemini
        gemini_history = []
        for pair in history[-MAX_HISTORY_PAIRS:]:
            gemini_history.append({"role": "user", "parts": [pair["user"]]})
            gemini_history.append({"role": "model", "parts": [pair["assistant"]]})

        chat = model.start_chat(history=gemini_history)
        response = await chat.send_message_async(user_message)
        return response.text.strip()

    except Exception as exc:
        err_msg = str(exc)
        # Если даже выбранная модель вдруг дала 404 — сбрасываем кэш и сообщаем
        if "404" in err_msg or "no longer available" in err_msg.lower():
            logger.warning("Выбранная модель внезапно вернула 404, сброс кэша.")
            reset_resolved_model()
        logger.exception("Ошибка Gemini API: %s", exc)
        return "⚠️ Не удалось получить ответ от ИИ. Попробуйте позже."


# ──────────────────────────────────────────────────────────────────────────────
# OpenAI-compatible backend
# ──────────────────────────────────────────────────────────────────────────────

async def _ask_openai(system_prompt: str, history: list[dict], user_message: str) -> str:
    try:
        from openai import AsyncOpenAI  # type: ignore

        client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        for pair in history[-MAX_HISTORY_PAIRS:]:
            messages.append({"role": "user", "content": pair["user"]})
            messages.append({"role": "assistant", "content": pair["assistant"]})
        messages.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.exception("Ошибка OpenAI API: %s", exc)
        return "⚠️ Не удалось получить ответ от ИИ. Попробуйте позже."


# ──────────────────────────────────────────────────────────────────────────────
# Public interface
# ──────────────────────────────────────────────────────────────────────────────

def is_event_related(user_message: str, history: list[dict] | None = None) -> bool:
    """Определяет, связан ли вопрос с мероприятиями, событиями или афишей.

    Проверяет ключевые слова на русском и казахском языках как в текущем сообщении,
    так и в последних репликах диалога.
    """
    event_keywords = [
        "мероприят", "событи", "афиш", "расписани", "план", "воркшоп",
        "хакатон", "митап", "семинар", "мастер-класс", "мастеркласс",
        "вебинар", "тренинг", "лекци", "интенсив", "программ", "питчинг",
        "іс-шара", "ис-шара", "шаралар", "шарасы", "шара", "бағдарлама",
        "кесте", "кездесу", "жиын", "байқау", "event", "events", "workshop", "hackathon"
    ]
    current_lower = user_message.lower()
    if any(kw in current_lower for kw in event_keywords):
        return True

    if history:
        for pair in history[-2:]:
            user_prev = pair.get("user", "").lower()
            if any(kw in user_prev for kw in event_keywords):
                return True

    return False


async def ask_ai(
    user_message: str,
    history: list[dict] | None = None,
    include_events: bool | None = None,
) -> str:
    """Основная точка входа: принимает вопрос и диалоговую историю,
    возвращает ответ ИИ.

    history — список словарей вида [{"user": "...", "assistant": "..."}, ...]
    include_events — если True, парсит и передает актуальные мероприятия.
                     Если None, определяет автоматически по контексту вопроса.
    """
    if history is None:
        history = []

    if include_events is None:
        include_events = is_event_related(user_message, history)

    events_content = None
    if include_events:
        try:
            logger.info("Запрос связан с мероприятиями — получаю актуальные данные через scraper...")
            events_content = await get_events_text()
        except Exception as exc:
            logger.warning("Не удалось получить актуальные мероприятия: %s", exc)

    kb = await load_knowledge_base()
    system_prompt = _build_system_prompt(kb, events_content=events_content)

    if AI_PROVIDER == "openai":
        return await _ask_openai(system_prompt, history, user_message)
    else:
        return await _ask_gemini(system_prompt, history, user_message)
