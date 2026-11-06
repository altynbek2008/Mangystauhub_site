import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ─── Admin IDs (через запятую в .env, например: ADMIN_IDS=123456,789012) ─────
_raw_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [int(x.strip()) for x in _raw_admins.split(",") if x.strip()]

# ─── AI Provider ─────────────────────────────────────────────────────────────
# Поддерживаются: "gemini" или "openai"
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")

# Google Gemini (бесплатный тариф)
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# OpenAI-совместимый (опционально)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# ─── Knowledge Base ───────────────────────────────────────────────────────────
KB_FILE_PATH: str = os.path.join(os.path.dirname(__file__), "knowledge_base.md")

# ─── Scraper ──────────────────────────────────────────────────────────────────
ASTANA_HUB_EVENTS_URL: str = os.getenv(
    "ASTANA_HUB_EVENTS_URL",
    "https://astanahub.com/ru/event/?city=Aktau",
)

# ─── Bot settings ─────────────────────────────────────────────────────────────
# Максимальная длина истории диалога (кол-во пар user/assistant)
MAX_HISTORY_PAIRS: int = int(os.getenv("MAX_HISTORY_PAIRS", "5"))
