import os
import logging
import aiohttp
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# — Токени з оточення —
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENKEY = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(level=logging.INFO)

async def ask_llama(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENKEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-2", "messages": [{"role": "user", "content": prompt}]}
    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
    return data["choices"][0]["message"]["content"]

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[KeyboardButton("💪 Хочу набрати масу"), [KeyboardButton("🏃 Хочу схуднути")]]]
    await update.message.reply_text("Оберіть свою ціль:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.text
    await update.message.reply_text("Генерую твій фітнес-план, зачекай...")
    plan = await ask_llama(user)
    await update.message.reply_text(plan)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.run_polling()

if __name__ == "__main__":
    main()
