import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    filters, ContextTypes
)
import anthropic
import base64
import httpx

# ─── Настройки ────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY")

# Системный промпт — личность и роль ассистента
SYSTEM_PROMPT = """Ты — дружелюбный и умный личный ассистент по имени Алекс.

Твои черты:
- Общаешься на русском языке (если пользователь не пишет на другом)
- Отвечаешь чётко, структурированно, без лишней воды
- Умеешь пошутить, но остаёшься профессиональным
- Если не знаешь ответа — честно говоришь об этом
- Помогаешь с любыми задачами: от кода до рецептов

При анализе изображений или файлов — описывай детально, что видишь.
"""

MAX_HISTORY = 20  # Максимум сообщений в памяти на пользователя

# ─── Инициализация ────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Хранилище истории: {user_id: [{"role": ..., "content": ...}]}
user_history: dict[int, list] = {}


def get_history(user_id: int) -> list:
    return user_history.setdefault(user_id, [])


def add_to_history(user_id: int, role: str, content):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    # Обрезаем историю, сохраняя MAX_HISTORY последних сообщений
    if len(history) > MAX_HISTORY:
        user_history[user_id] = history[-MAX_HISTORY:]


def ask_claude(user_id: int) -> str:
    """Отправить историю в Claude и получить ответ."""
    response = client.messages.create(
        model="claude-haiku-3-20240307",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=get_history(user_id),
    )
    return response.content[0].text


# ─── Команды ──────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"Привет, {user}! 👋 Я Алекс — твой личный ассистент.\n\n"
        "Можешь писать мне что угодно — текст, вопросы, задачи.\n"
        "Также умею анализировать изображения и документы!\n\n"
        "Команды:\n"
        "/start — начать заново\n"
        "/clear — очистить память диалога\n"
        "/help — помощь"
    )


async def clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_history[user_id] = []
    await update.message.reply_text("🧹 Память очищена! Начинаем с чистого листа.")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 *Что я умею:*\n\n"
        "• Отвечать на любые вопросы\n"
        "• Помнить контекст нашего разговора\n"
        "• Анализировать фото и изображения\n"
        "• Читать документы (PDF, TXT и др.)\n"
        "• Помогать с кодом, текстом, задачами\n\n"
        "Просто напиши или отправь файл!",
        parse_mode="Markdown"
    )


# ─── Обработка текста ─────────────────────────────────────────
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    await update.message.chat.send_action("typing")

    add_to_history(user_id, "user", text)
    reply = ask_claude(user_id)
    add_to_history(user_id, "assistant", reply)

    await update.message.reply_text(reply)


# ─── Обработка изображений ────────────────────────────────────
async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    caption = update.message.caption or "Опиши это изображение подробно."

    await update.message.chat.send_action("typing")

    # Скачиваем фото
    photo = update.message.photo[-1]  # Берём наилучшее качество
    file = await ctx.bot.get_file(photo.file_id)
    
    async with httpx.AsyncClient() as http:
        response = await http.get(file.file_path)
    image_data = base64.standard_b64encode(response.content).decode("utf-8")

    # Формируем сообщение с изображением
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
        {"type": "text", "text": caption}
    ]

    add_to_history(user_id, "user", content)
    reply = ask_claude(user_id)
    add_to_history(user_id, "assistant", reply)

    await update.message.reply_text(reply)


# ─── Обработка документов ─────────────────────────────────────
async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    caption = update.message.caption or "Проанализируй этот документ и кратко опиши его содержимое."

    await update.message.chat.send_action("typing")

    file = await ctx.bot.get_file(doc.file_id)
    
    async with httpx.AsyncClient() as http:
        response = await http.get(file.file_path)
    file_bytes = response.content

    # Определяем тип файла
    mime = doc.mime_type or ""
    
    if "pdf" in mime:
        # PDF — отправляем как документ
        b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
        content = [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
            {"type": "text", "text": caption}
        ]
    elif "text" in mime or doc.file_name.endswith((".txt", ".md", ".csv", ".json", ".py", ".js")):
        # Текстовый файл — просто читаем
        text_content = file_bytes.decode("utf-8", errors="replace")
        content = f"Файл «{doc.file_name}»:\n\n{text_content}\n\n{caption}"
    else:
        await update.message.reply_text(
            f"⚠️ Формат файла «{doc.file_name}» не поддерживается напрямую.\n"
            "Попробуй прислать PDF, TXT, изображение или код."
        )
        return

    add_to_history(user_id, "user", content)
    reply = ask_claude(user_id)
    add_to_history(user_id, "assistant", reply)

    await update.message.reply_text(reply)


# ─── Запуск ───────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Бот запущен ✅")
    app.run_polling()


if __name__ == "__main__":
    main()
