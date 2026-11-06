"""
handlers/ai_chat.py — режим свободного диалога с ИИ.

Пользователь нажимает «🤖 Задать вопрос ИИ», бот переходит в режим диалога.
История сохраняется в FSM-состоянии. Выход — кнопка «Отмена».
"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from handlers.keyboards import MENU_KZ, MENU_RU, cancel_keyboard, main_menu_keyboard
from services.ai_service import ask_ai
from services.formatter import send_safe_message

logger = logging.getLogger(__name__)
router = Router()


class AIChatStates(StatesGroup):
    waiting_for_question = State()


# ──────────────────────────────────────────────────────────────────────────────
# Вход в режим диалога
# ──────────────────────────────────────────────────────────────────────────────

@router.message(F.text.in_({MENU_RU["ask_ai"], MENU_KZ["ask_ai"]}))
async def enter_ai_chat(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")

    # Сохраняем текущий язык и сбрасываем историю
    await state.set_state(AIChatStates.waiting_for_question)
    await state.update_data(lang=lang, history=[])

    if lang == "ru":
        text = (
            "🤖 Режим вопросов к ИИ активирован.\n\n"
            "Задайте любой вопрос о Mangystau Hub, и я постараюсь ответить.\n"
            "Для выхода нажмите «❌ Отмена»."
        )
    else:
        text = (
            "🤖 ЖИ сұрақ режимі іске қосылды.\n\n"
            "Mangystau Hub туралы кез келген сұрақ қойыңыз, жауап беруге тырысамын.\n"
            "Шығу үшін «❌ Бас тарту» түймесін басыңыз."
        )

    await message.answer(text, reply_markup=cancel_keyboard(lang))


# ──────────────────────────────────────────────────────────────────────────────
# Обработка вопроса
# ──────────────────────────────────────────────────────────────────────────────

@router.message(AIChatStates.waiting_for_question)
async def handle_ai_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    history: list[dict] = data.get("history", [])

    user_text = message.text or ""

    # Проверка на нажатие кнопки «Отмена»
    cancel_labels = {"❌ Отмена", "❌ Бас тарту"}
    if user_text in cancel_labels:
        await state.set_state(None)
        await state.update_data(history=[])
        farewell = "↩️ Возврат в главное меню." if lang == "ru" else "↩️ Басты мәзірге оралу."
        await message.answer(farewell, reply_markup=main_menu_keyboard(lang))
        return

    # Пустое сообщение
    if not user_text.strip():
        prompt = "Пожалуйста, введите текстовый вопрос." if lang == "ru" else "Мәтіндік сұрақ енгізіңіз."
        await message.answer(prompt)
        return

    wait_msg = await message.answer("⏳ Думаю..." if lang == "ru" else "⏳ Ойлап жатырмын...")

    answer = await ask_ai(user_text, history)

    # Обновляем историю диалога
    history.append({"user": user_text, "assistant": answer})
    await state.update_data(history=history)

    await wait_msg.delete()
    await send_safe_message(message, answer)
