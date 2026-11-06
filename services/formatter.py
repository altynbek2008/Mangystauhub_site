import html
import re
from typing import Optional
from aiogram.types import Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove


def format_markdown_to_html(text: str) -> str:
    """Конвертирует базовую разметку Markdown от LLM в валидный безопасный HTML для Telegram.

    Обрабатывает:
    - Заголовки (###, ##, #) -> <b>...</b>
    - Жирный шрифт (**text**) -> <b>text</b>
    - Курсив (*text*) -> <i>text</i>
    - Списки с буллетами (*, -, •)
    - Инлайн-код (`code`) -> <code>code</code>
    - Экранирует опасные символы HTML (&, <, >), предотвращая ошибки парсера.
    """
    if not text:
        return ""

    # 1. Сохраняем блоки кода во временные плейсхолдеры
    placeholders = []

    def save_code(match: re.Match) -> str:
        code_content = match.group(1)
        escaped_code = html.escape(code_content)
        idx = len(placeholders)
        placeholders.append(f"<code>{escaped_code}</code>")
        return f"PHCODE{idx}END"

    text = re.sub(r"`([^`]+)`", save_code, text)

    # 2. Экранируем спецсимволы HTML во всем тексте
    text = html.escape(text)

    # 3. Преобразуем заголовки: ### Header или ## Header или # Header
    # В экранированном виде это всё ещё #
    text = re.sub(r"^(?:#{1,6})\s*(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # 4. Преобразуем жирный шрифт: **text** или __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text, flags=re.DOTALL)

    # 5. Преобразуем курсив: *text* (если не является частью буллета в начале строки)
    # Но осторожно со звёздочками:
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", text)

    # 6. Восстанавливаем сохраненный код
    for idx, code_html in enumerate(placeholders):
        text = text.replace(f"PHCODE{idx}END", code_html)

    return text.strip()


def strip_markdown(text: str) -> str:
    """Полностью очищает текст от Markdown спецсимволов (###, **, *, `).

    Гарантированно чистый простой текст.
    """
    if not text:
        return ""

    # Убираем заголовки ###
    text = re.sub(r"^(?:#{1,6})\s*", "", text, flags=re.MULTILINE)
    # Убираем **жирный**
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    # Убираем *курсив*
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    # Убираем `код`
    text = re.sub(r"`(.*?)`", r"\1", text)
    return text.strip()


async def send_safe_message(
    message: Message,
    text: str,
    reply_markup: Optional[ReplyKeyboardMarkup | InlineKeyboardMarkup | ReplyKeyboardRemove] = None,
) -> Message:
    """Безопасно отправляет сообщение:

    1. Сначала пробует отправить с красивым HTML форматированием.
    2. Если Telegram вернул ошибку форматирования (Can't parse entities и т.п.),
       перехватывает её и отправляет очищенный plain text без падения бота.
    """
    formatted_html = format_markdown_to_html(text)

    try:
        return await message.answer(
            formatted_html,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    except Exception:
        # Фоллбек: очищаем от Markdown и отправляем без parse_mode
        clean_text = strip_markdown(text)
        return await message.answer(
            clean_text,
            reply_markup=reply_markup,
            parse_mode=None,
        )
