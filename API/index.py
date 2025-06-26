import os
import logging
import aiohttp
import asyncio
from fastapi import Request
from fastapi.responses import JSONResponse
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Зчитування токенів
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENKEY = os.getenv("OPENROUTER_API_KEY")

# Логування
logging.basicConfig(level=logging.INFO)

# LLaMA через OpenRouter
async def ask_llama(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENKEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3",
        "messages": [{"role": "user", "content": prompt}]
    }
    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

# Старт-команда
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[KeyboardButton("💪 Хочу набрати масу")], [KeyboardButton("🏃 Хочу схуднути")]]
    await update.message.reply_text("Оберіть свою ціль:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# Обробка повідомлень
async def handle_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.text
    await update.message.reply_text("Генерую твій фітнес план, зачекай…")
    response = await ask_llama(f"Створи фітнес-план українською мовою для користувача з метою: {user}")
    await update.message.reply_text(response)

# Основна функція бота
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    # Не закриваємо бот після запуску
    while True:
        await asyncio.sleep(60)

# Vercel handler
async def handler(request: Request):
    asyncio.create_task(main())
    return JSONResponse(content={"status": "bot started"})
