import os
import logging
import aiohttp
import asyncio
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(level=logging.INFO)
users = {}

async def ask_llama(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[
        KeyboardButton("💪 Хочу набрати масу"),
        KeyboardButton("🏃‍♂️ Хочу схуднути")
    ]]
    await update.message.reply_text("Оберіть свою ціль:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.text
    await update.message.reply_text("Генерую твій фітнес план, зачекай…")
    response = await ask_llama(f"Створи фітнес-план українською мовою для користувача з метою: {user}")
    await update.message.reply_text(response)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
