"""
handlers/menu.py — обработка кнопок главного меню: О хабе, Мероприятия, Контакты, Смена языка.
"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from handlers.keyboards import MENU_KZ, MENU_RU, language_keyboard, main_menu_keyboard, whatsapp_keyboard
from services.ai_service import ask_ai
from services.formatter import send_safe_message

logger = logging.getLogger(__name__)
router = Router()


def _all_menu_labels() -> set[str]:
    return set(MENU_RU.values()) | set(MENU_KZ.values())


# ──────────────────────────────────────────────────────────────────────────────
# О хабе
# ──────────────────────────────────────────────────────────────────────────────

@router.message(F.text.in_({MENU_RU["about"], MENU_KZ["about"]}))
async def menu_about(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")

    query = (
        "Расскажи о Mangystau Hub: что это такое, миссия, направления работы, режим работы."
        if lang == "ru"
        else "Mangystau Hub туралы айтып бер: бұл не, миссиясы, жұмыс бағыттары, жұмыс уақыты."
    )
    wait_msg = await message.answer("⏳ Загружаю информацию..." if lang == "ru" else "⏳ Ақпарат жүктелуде...")
    answer = await ask_ai(query)
    await wait_msg.delete()
    await send_safe_message(message, answer, reply_markup=main_menu_keyboard(lang))


# ──────────────────────────────────────────────────────────────────────────────
# Мероприятия
# ──────────────────────────────────────────────────────────────────────────────

@router.message(F.text.in_({MENU_RU["events"], MENU_KZ["events"]}))
async def menu_events(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")

    query = (
        "Перечисли все предстоящие мероприятия Mangystau Hub: текущую неделю, следующую неделю и далее. "
        "Укажи даты, время и название каждого мероприятия."
        if lang == "ru"
        else "Mangystau Hub алдағы іс-шараларының толық тізімін бер: осы апта, келесі апта және одан кейін. "
             "Әрбір іс-шараның күнін, уақытын және атауын көрсет."
    )
    wait_msg = await message.answer("⏳ Загружаю мероприятия..." if lang == "ru" else "⏳ Іс-шаралар жүктелуде...")
    answer = await ask_ai(query, include_events=True)
    await wait_msg.delete()
    await send_safe_message(message, answer, reply_markup=main_menu_keyboard(lang))


# ──────────────────────────────────────────────────────────────────────────────
# Контакты
# ──────────────────────────────────────────────────────────────────────────────

@router.message(F.text.in_({MENU_RU["contacts"], MENU_KZ["contacts"]}))
async def menu_contacts(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")

    query = (
        "Перечисли все контакты Mangystau Hub: адрес, телефон, email, сайт, соцсети."
        if lang == "ru"
        else "Mangystau Hub байланыстарын атап бер: мекенжай, телефон, email, сайт, әлеуметтік желілер."
    )
    wait_msg = await message.answer("⏳ Загружаю контакты..." if lang == "ru" else "⏳ Байланыстар жүктелуде...")
    answer = await ask_ai(query)
    await wait_msg.delete()
    await send_safe_message(message, answer, reply_markup=main_menu_keyboard(lang))


# ──────────────────────────────────────────────────────────────────────────────
# Связаться в WhatsApp
# ──────────────────────────────────────────────────────────────────────────────

@router.message(F.text.in_({MENU_RU["whatsapp"], MENU_KZ["whatsapp"]}))
async def menu_whatsapp(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")

    text = (
        "💬 Для связи с нами в <b>WhatsApp</b> нажмите кнопку ниже:"
        if lang == "ru"
        else "💬 Бізбен <b>WhatsApp</b> арқылы байланысу үшін төмендегі түймені басыңыз:"
    )
    await message.answer(text, reply_markup=whatsapp_keyboard(lang))


# ──────────────────────────────────────────────────────────────────────────────
# Смена языка
# ──────────────────────────────────────────────────────────────────────────────

@router.message(F.text.in_({MENU_RU["lang"], MENU_KZ["lang"]}))
async def menu_change_lang(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Выберите язык / Тілді таңдаңыз:",
        reply_markup=language_keyboard(),
    )
