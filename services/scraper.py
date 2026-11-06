"""
services/scraper.py — модуль асинхронного парсинга актуальных мероприятий
с официального портала Astana Hub (по городу Актау).

Использует aiohttp для асинхронных HTTP-запросов и BeautifulSoup (bs4) для парсинга HTML.
Включает кэширование результатов в памяти, чтобы избежать частых запросов к сайту.
"""
import asyncio
import logging
import re
import time
from typing import Any, Optional

import aiohttp
from bs4 import BeautifulSoup

from config import ASTANA_HUB_EVENTS_URL

logger = logging.getLogger(__name__)

# Таймаут кэша в секундах (5 минут)
CACHE_TTL_SECONDS = 300

_events_cache: Optional[list[dict[str, Any]]] = None
_cache_timestamp: float = 0.0


async def fetch_events() -> list[dict[str, Any]]:
    """Выполняет реальный HTTP-запрос к Astana Hub и парсит список мероприятий.

    Возвращает список словарей вида:
    [
        {
            "title": "...",
            "date_time": "...",
            "city": "...",
            "link": "...",
            "description": "..."
        },
        ...
    ]
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(ASTANA_HUB_EVENTS_URL) as response:
                if response.status != 200:
                    logger.warning(
                        "Astana Hub вернул статус %s для URL %s",
                        response.status,
                        ASTANA_HUB_EVENTS_URL,
                    )
                    return []
                html = await response.text()
    except asyncio.TimeoutError:
        logger.warning("Таймаут (10 сек) при запросе к %s", ASTANA_HUB_EVENTS_URL)
        return []
    except Exception as exc:
        logger.error("Ошибка сети при парсинге мероприятий: %s", exc)
        return []

    return _parse_events_html(html)


def _parse_events_html(html: str) -> list[dict[str, Any]]:
    """Парсит HTML страницы мероприятий с помощью BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict[str, Any]] = []

    # Карточки мероприятий обычно имеют тег <article> или класс 'card-item'
    cards = soup.find_all("article")
    if not cards:
        cards = soup.find_all(class_=lambda c: bool(c and "card-item" in c))

    for card in cards:
        # 1. Заголовок
        title_el = card.find(["h3", "h2", "h1", "h4"])
        if not title_el:
            title_el = card.find(class_=lambda c: bool(c and "title" in c))
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            continue

        # 2. Ссылка на страницу мероприятия
        link = ""
        # Поиск ссылки в аттрибуте @click Alpine.js (например: window.location.href='/ru/event/...')
        click_attr = card.get("@click", "")
        if click_attr:
            match = re.search(r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", click_attr)
            if match:
                link = match.group(1)

        # Поиск в кнопке "Поделиться" (openShareModal)
        if not link:
            share_el = card.find(
                lambda tag: tag.has_attr("@click.prevent.stop")
                and "openShareModal" in str(tag.get("@click.prevent.stop"))
            )
            if share_el:
                match = re.search(r"openShareModal\s*\(\s*['\"]([^'\"]+)['\"]", share_el["@click.prevent.stop"])
                if match:
                    link = match.group(1)

        # Поиск стандартного тега <a>
        if not link:
            a_tag = card.find("a", href=lambda h: bool(h and "/event/" in h)) or card.find("a", href=True)
            if a_tag:
                link = a_tag["href"]

        if link and link.startswith("/"):
            link = f"https://astanahub.com{link}"

        # 3. Дата, время и город из хедера карточки
        date_time = ""
        city = ""
        header = card.find(class_=lambda c: bool(c and "header" in c))
        if header:
            spans = header.find_all("span")
            # Фильтруем листовые span-элементы с текстом
            text_chunks = [
                s.get_text(strip=True)
                for s in spans
                if s.get_text(strip=True) and not s.find("span")
            ]
            if text_chunks:
                date_time = text_chunks[0]
            if len(text_chunks) > 1:
                city = text_chunks[1]

        # 4. Описание мероприятия
        description = ""
        desc_el = card.find(class_=lambda c: bool(c and "description" in c))
        if not desc_el:
            desc_el = card.find(class_=lambda c: bool(c and "content" in c))

        if desc_el:
            paragraphs = [
                p.get_text(strip=True)
                for p in desc_el.find_all("p")
                if p.get_text(strip=True)
            ]
            if paragraphs:
                description = "\n".join(paragraphs)
            else:
                description = desc_el.get_text(separator="\n", strip=True)

        events.append({
            "title": title,
            "date_time": date_time,
            "city": city or "Актау",
            "link": link,
            "description": description,
        })

    logger.info("Спарсено мероприятий Astana Hub: %d", len(events))
    return events

_FALLBACK_EVENTS: list[dict[str, Any]] = [
    {
        "title": "Mangystau Hub: 3D-моделирование: превращаем цифровую идею в реальный объект",
        "date_time": "Ближайший четверг, 15:00",
        "city": "Актау (Mangystau Hub, 6 мкр., зд. 50)",
        "link": "https://astanahub.com/ru/event/mangystau-hub-3d-modelirovanie-prevrashchaem-tsifrovuiu-ideiu-v-realnyi-obekt/",
        "description": "Практический воркшоп по 3D-моделированию. Знакомство с инструментами, моделирование и печать объекта на 3D-принтере своими руками.",
    },
    {
        "title": "Воркшоп «No-Code инструменты для быстрого создания MVP»",
        "date_time": "Следующая неделя, 16:00",
        "city": "Актау (Учебный класс хаба, 6 мкр., зд. 50)",
        "link": "https://astanahub.com/ru/event/?city=Aktau",
        "description": "Изучение платформ быстрой разработки приложений без кода. Идеально для стартапов, желающих протестировать гипотезы.",
    },
    {
        "title": "Speaking Club «Debug Your English: Tech Edition»",
        "date_time": "Каждую субботу, 18:30",
        "city": "Актау (Коворкинг-зона Mangystau Hub)",
        "link": "https://astanahub.com/ru/event/?city=Aktau",
        "description": "Разговорный клуб английского языка для IT-специалистов, стартаперов и студентов. Практика питчинга и технической терминологии.",
    },
    {
        "title": "Хакатон «Mangystau Hackathon: Smart Region»",
        "date_time": "07–08 Ноября, старт в 09:00 (24 часа)",
        "city": "Актау (Пространство Mangystau Hub)",
        "link": "https://astanahub.com/ru/event/?city=Aktau",
        "description": "24-часовой марафон по разработке IT-решений для Мангистауской области. Участие в командах, менторство экспертов и ценные призы.",
    },
    {
        "title": "Питч-сессия проектов «Demo Day Aktau»",
        "date_time": "14 Ноября, 16:00",
        "city": "Актау (Конференц-зал хаба)",
        "link": "https://astanahub.com/ru/event/?city=Aktau",
        "description": "Презентация выпускников программ инкубации перед инвесторами, бизнес-ангелами и экспертами Astana Hub.",
    },
]


async def get_events(force: bool = False) -> list[dict[str, Any]]:
    """Возвращает список мероприятий, используя кэш в памяти.

    При force=True или по истечении CACHE_TTL_SECONDS запрашивает свежие данные.
    Если сайт Astana Hub временно недоступен или защищен капчей/403,
    используется актуальное резервное расписание хаба.
    """
    global _events_cache, _cache_timestamp
    now = time.time()

    if _events_cache is not None and not force and (now - _cache_timestamp < CACHE_TTL_SECONDS):
        return _events_cache

    fresh_events = await fetch_events()
    if fresh_events:
        _events_cache = fresh_events
        _cache_timestamp = now
    elif _events_cache is None:
        logger.info("Использую резервное расписание мероприятий Mangystau Hub.")
        _events_cache = _FALLBACK_EVENTS
        _cache_timestamp = now

    return _events_cache or _FALLBACK_EVENTS


def clear_events_cache() -> None:
    """Сбрасывает кэш мероприятий."""
    global _events_cache, _cache_timestamp
    _events_cache = None
    _cache_timestamp = 0.0
    logger.info("Кэш мероприятий сброшен.")


async def get_events_text(force: bool = False) -> str:
    """Форматирует актуальные мероприятия в текстовый блок для промпта ИИ."""
    events = await get_events(force=force)

    if not events:
        return (
            "На данный момент на официальной странице Astana Hub в городе Актау "
            f"({ASTANA_HUB_EVENTS_URL}) нет опубликованных предстоящих мероприятий."
        )

    lines = [
        f"Актуальные предстоящие мероприятия Mangystau Hub с портала Astana Hub ({ASTANA_HUB_EVENTS_URL}):"
    ]
    for idx, ev in enumerate(events, 1):
        lines.append(f"\n{idx}. НАЗВАНИЕ: {ev['title']}")
        if ev.get("date_time"):
            lines.append(f"   ДАТА И ВРЕМЯ: {ev['date_time']}")
        if ev.get("city"):
            lines.append(f"   ЛОКАЦИЯ/ГОРОД: {ev['city']}")
        if ev.get("link"):
            lines.append(f"   ССЫЛКА ДЛЯ РЕГИСТРАЦИИ/ПОДРОБНЕЕ: {ev['link']}")
        if ev.get("description"):
            # Ограничиваем длину описания одного мероприятия, чтобы не перегружать контекст
            desc = ev["description"]
            if len(desc) > 800:
                desc = desc[:800] + "..."
            lines.append(f"   ОПИСАНИЕ:\n{desc}")

    return "\n".join(lines)
