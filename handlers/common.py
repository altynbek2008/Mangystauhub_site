"""
handlers/common.py — /start, /help, /reload_kb, выбор языка.
"""
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS
from handlers.keyboards import language_keyboard, main_menu_keyboard
from services.ai_service import load_knowledge_base, reload_knowledge_base_sync, reset_resolved_model

logger = logging.getLogger(__name__)
router = Router()

# ──────────────────────────────────────────────────────────────────────────────
# /start
# ──────────────────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    # Предварительно загружаем базу знаний в кэш
    await load_knowledge_base()

    await message.answer(
        "👋 Привет! Добро пожаловать в <b>Mangystau Hub Bot</b>.\n\n"
        "🔒 <i>Обратите внимание: использование бота означает согласие на обработку ваших запросов. "
        "Бот не собирает и не хранит ваши личные или персональные данные.</i>\n\n"
        "🔒 <i>Ескерту: ботты пайдалану сұрауларыңызды өңдеуге келісімді білдіреді. "
        "Бот пайдаланушылардың жеке деректерін жинамайды және сақтамайды.</i>\n\n"
        "Выберите язык / Тілді таңдаңыз:",
        reply_markup=language_keyboard(),
    )


# ──────────────────────────────────────────────────────────────────────────────
# /help
# ──────────────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")

    if lang == "ru":
        text = (
            "ℹ️ <b>Команды бота:</b>\n"
            "/start — перезапустить бота\n"
            "/help — справка\n\n"
            "Используйте кнопки меню для навигации.\n"
            "Нажмите «🤖 Задать вопрос ИИ», чтобы задать произвольный вопрос о хабе."
        )
    else:
        text = (
            "ℹ️ <b>Бот командалары:</b>\n"
            "/start — ботты қайта іске қосу\n"
            "/help — анықтама\n\n"
            "Шарлау үшін мәзір түймелерін пайдаланыңыз.\n"
            "«🤖 ЖИ-ға сұрақ қою» түймесін басыңыз."
        )

    await message.answer(text, reply_markup=main_menu_keyboard(lang))


# ──────────────────────────────────────────────────────────────────────────────
# /reload_kb — только для администраторов
# ──────────────────────────────────────────────────────────────────────────────

@router.message(Command("reload_kb"))
async def cmd_reload_kb(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0

    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await message.answer("🚫 У вас нет прав для выполнения этой команды.")
        return

    reload_knowledge_base_sync()
    reset_resolved_model()
    kb = await load_knowledge_base(force=True)
    await message.answer(
        f"✅ База знаний успешно перезагружена!\n"
        f"📄 Загружено символов: <b>{len(kb)}</b>\n"
        f"🤖 Кэш модели Gemini и кэш мероприятий сброшены."
    )
    logger.info("Администратор %d перезагрузил knowledge_base.md", user_id)


# ──────────────────────────────────────────────────────────────────────────────
# Выбор языка через inline-кнопки
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("lang:"))
async def handle_language_choice(callback: CallbackQuery, state: FSMContext) -> None:
    lang = callback.data.split(":")[1]  # "ru" или "kz"
    await state.update_data(lang=lang)

    if lang == "ru":
        greeting = (
            "✅ Выбран <b>русский язык</b>.\n\n"
            "Используйте кнопки ниже для навигации или задайте вопрос ИИ."
        )
    else:
        greeting = (
            "✅ <b>Қазақ тілі</b> таңдалды.\n\n"
            "Шарлау үшін төмендегі түймелерді пайдаланыңыз немесе ЖИ-ға сұрақ қойыңыз."
        )

    await callback.message.edit_text(greeting)
    await callback.message.answer("👇", reply_markup=main_menu_keyboard(lang))
    await callback.answer()
