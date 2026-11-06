"""
app.py — Веб-сайт и API чат-бота Mangystau Hub на базе фреймворка Flask (Python).

Напрямую переиспользует логику из services/ai_service.py и services/scraper.py.
Поддерживает асинхронные обработчики запросов (Flask 2.0+ / Flask[async] с asgiref),
интеграцию актуальных спарсенных мероприятий Astana Hub, перевод на оператора
в WhatsApp и соблюдение политики конфиденциальности.
"""
import asyncio
import logging
import os
import sys

from flask import Flask, jsonify, render_template, request

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import ask_ai, is_event_related, load_knowledge_base
from services.scraper import get_events

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger("mangystau_hub_web")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "mangystau-hub-secret-key-2026")


@app.route("/")
def index():
    """Главная страница веб-интерфейса чат-бота Mangystau Hub."""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
async def chat_api():
    """API-эндпоинт для отправки сообщения пользователя и получения ответа от ИИ.

    Принимает JSON:
    {
        "message": "Вопрос пользователя",
        "history": [{"user": "...", "assistant": "..."}, ...],
        "lang": "ru" или "kz"
    }

    Возвращает JSON:
    {
        "status": "ok",
        "response": "Ответ ассистента",
        "is_event_related": true/false
    }
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({
            "status": "error",
            "error": "Сообщение не может быть пустым."
        }), 400

    logger.info("Получен запрос к чату: '%s' (история: %d сообщений)", user_message[:60], len(history))

    try:
        # ask_ai автоматически определяет вопросы о мероприятиях
        # и подключает парсер Astana Hub по Актау
        response_text = await ask_ai(user_message=user_message, history=history)

        return jsonify({
            "status": "ok",
            "response": response_text,
            "is_event_related": is_event_related(user_message, history)
        })

    except Exception as exc:
        logger.exception("Ошибка при обработке запроса в ask_ai: %s", exc)
        return jsonify({
            "status": "error",
            "error": "Внутренняя ошибка сервиса.",
            "response": (
                "⚠️ Не удалось получить ответ из-за временной ошибки соединения с сервисом ИИ.\n\n"
                "Вы можете напрямую обратиться к сотрудникам Mangystau Hub:\n"
                "👉 <a href=\"https://wa.me/77789807454\" target=\"_blank\" class=\"whatsapp-inline-link\">"
                "Написать оператору в WhatsApp</a> или позвонить по номеру <b>+7 (778) 980-74-54</b>."
            )
        }), 500


@app.route("/api/events", methods=["GET"])
async def events_api():
    """API-эндпоинт для получения списка актуальных спарсенных мероприятий."""
    try:
        events = await get_events()
        return jsonify({
            "status": "ok",
            "count": len(events),
            "events": events
        })
    except Exception as exc:
        logger.exception("Ошибка при получении списка мероприятий: %s", exc)
        return jsonify({
            "status": "error",
            "count": 0,
            "events": []
        }), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Проверка жизнеспособности сервиса."""
    return jsonify({
        "status": "healthy",
        "service": "Mangystau Hub Web Assistant",
        "version": "1.0.0"
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    logger.info("Запуск Flask веб-сервера Mangystau Hub на http://localhost:%d", port)
    app.run(host="0.0.0.0", port=port, debug=debug)
