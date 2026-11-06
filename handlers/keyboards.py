from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


# ──────────────────────────────────────────────────────────────────────────────
# Выбор языка (первый экран)
# ──────────────────────────────────────────────────────────────────────────────

def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang:kz"),
        ]
    ])


# ──────────────────────────────────────────────────────────────────────────────
# Главное меню
# ──────────────────────────────────────────────────────────────────────────────

MENU_RU = {
    "about":    "🏢 О хабе",
    "events":   "📅 Мероприятия",
    "contacts": "📞 Контакты",
    "ask_ai":   "🤖 Задать вопрос ИИ",
    "whatsapp": "💬 Связаться в WhatsApp",
    "lang":     "🌐 Сменить язык",
}

MENU_KZ = {
    "about":    "🏢 Хаб туралы",
    "events":   "📅 Іс-шаралар",
    "contacts": "📞 Байланыстар",
    "ask_ai":   "🤖 ЖИ-ға сұрақ қою",
    "whatsapp": "💬 WhatsApp-пен байланысу",
    "lang":     "🌐 Тілді өзгерту",
}


def main_menu_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    labels = MENU_RU if lang == "ru" else MENU_KZ
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=labels["about"]), KeyboardButton(text=labels["events"])],
            [KeyboardButton(text=labels["contacts"]), KeyboardButton(text=labels["ask_ai"])],
            [KeyboardButton(text=labels["whatsapp"])],
            [KeyboardButton(text=labels["lang"])],
        ],
        resize_keyboard=True,
    )


def whatsapp_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    btn_text = "Перейти в WhatsApp" if lang == "ru" else "WhatsApp-қа өту"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=btn_text,
                url="https://wa.me/77789807454",
            )
        ]
    ])


def cancel_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    text = "❌ Отмена" if lang == "ru" else "❌ Бас тарту"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text)]],
        resize_keyboard=True,
    )
