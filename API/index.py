import os
import json
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Стани
(META, GENDER, AGE, WEIGHT, HEIGHT, LEVEL, MENU, REMINDER_TIME) = range(8)
user_data = {}
scheduler = AsyncIOScheduler()
scheduler.start()

meta_keyboard = ReplyKeyboardMarkup([["💪 Набір маси", "⚖️ Схуднення", "🎯 Інше"]], resize_keyboard=True)
gender_keyboard = ReplyKeyboardMarkup([["👨 Я чоловік", "👩 Я жінка"]], resize_keyboard=True)
level_keyboard = ReplyKeyboardMarkup([["📗 Початковий", "📘 Середній", "📕 Просунутий"]], resize_keyboard=True)
main_menu_keyboard = ReplyKeyboardMarkup([["📅 Додати нагадування"], ["🧠 Інше питання"]], resize_keyboard=True)

def get_user_profile(user_id):
    return user_data.get(user_id, {})

def save_user_profile(user_id, key, value):
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id][key] = value

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Я твій персональний фітнес-тренер. Обери мету:", reply_markup=meta_keyboard)
    return META

async def set_meta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_profile(update.effective_user.id, "meta", update.message.text)
    await update.message.reply_text("✅ Мета збережена. Обери стать:", reply_markup=gender_keyboard)
    return GENDER

async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_profile(update.effective_user.id, "gender", update.message.text)
    await update.message.reply_text("🎂 Введи свій вік:")
    return AGE

async def set_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_profile(update.effective_user.id, "age", update.message.text)
    await update.message.reply_text("⚖️ Введи свою вагу в кг:")
    return WEIGHT

async def set_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_profile(update.effective_user.id, "weight", update.message.text)
    await update.message.reply_text("📏 Введи свій зріст у см:")
    return HEIGHT

async def set_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_profile(update.effective_user.id, "height", update.message.text)
    await update.message.reply_text("🏋️‍♂️ Обери рівень підготовки:", reply_markup=level_keyboard)
    return LEVEL

async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_profile(update.effective_user.id, "level", update.message.text)
    await update.message.reply_text("✅ Дані збережено! Що хочеш зробити далі:", reply_markup=main_menu_keyboard)
    return MENU

async def ask_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏰ Введи час у форматі ГГ:ХХ (наприклад: 08:00):")
    return REMINDER_TIME

async def set_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    try:
        t = time.fromisoformat(update.message.text.strip())
        scheduler.add_job(
            lambda: context.bot.send_message(chat_id, "🏃‍♂️ Час тренуватись або харчуватись!"),
            trigger='cron', hour=t.hour, minute=t.minute, id=str(user_id), replace_existing=True
        )
        await update.message.reply_text(f"✅ Нагадування встановлено на {t.strftime('%H:%M')}")
    except ValueError:
        await update.message.reply_text("❌ Невірний формат. Введи щось типу 09:00")
        return REMINDER_TIME
    return MENU

async def handle_custom_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    prompt = (
        f"Ти — персональний фітнес-тренер. Відповідай українською мовою.\n"
        f"Користувач має такі дані:\n"
        f"вік: {profile.get('age')}, стать: {profile.get('gender')}, "
        f"вага: {profile.get('weight')} кг, зріст: {profile.get('height')} см,\n"
        f"мета: {profile.get('meta')}, рівень: {profile.get('level')}.\n"
        f"Питання: {update.message.text}"
    )
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3-8b-instruct",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
    except Exception as e:
        answer = f"⚠️ Помилка: {e}"
    await update.message.reply_text(answer)
    return MENU

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            META: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_meta)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_age)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_weight)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_height)],
            LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_level)],
            MENU: [
                MessageHandler(filters.Regex(".*нагадування.*"), ask_reminder_time),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_question)
            ],
            REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_reminder_time)],
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)
    print("✅ Бот запущено")
    app.run_polling()

if __name__ == '__main__':
    main()
