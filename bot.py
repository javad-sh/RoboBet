import json
import os
import logging
from datetime import datetime
import pytz
import jdatetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Bot token
BOT_TOKEN = "7697466323:AAFXXszQt_lAPn4qCefx3VnnZYVhTuQiuno"

def load_json_file(filename):
    """Load JSON file and return its contents."""
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logging.warning(f"File {filename} does not exist")
            return []
    except Exception as e:
        logging.error(f"Error loading {filename}: {e}")
        return []

def save_json_file(data, filename):
    """Save data to JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving {filename}: {e}")

def add_chat_id(chat_id):
    """Add a chat ID to the list of subscribers if not already present."""
    chat_ids_file = "chat_ids.json"
    chat_ids = load_json_file(chat_ids_file)
    if str(chat_id) not in chat_ids:
        chat_ids.append(str(chat_id))
        save_json_file(chat_ids, chat_ids_file)
        logging.info(f"Added chat ID {chat_id} to subscribers")
    else:
        logging.info(f"Chat ID {chat_id} already subscribed")

def convert_to_persian_time(iso_str):
    """Convert ISO time string to Persian (Jalali) datetime string in Iran timezone."""
    try:
        dt = datetime.fromisoformat(iso_str)
        tehran = pytz.timezone("Asia/Tehran")
        dt_tehran = dt.astimezone(tehran)
        jdt = jdatetime.datetime.fromgregorian(datetime=dt_tehran)
        return jdt.strftime("%m/%d - %H:%M")
    except Exception as e:
        logging.warning(f"Cannot parse time: {iso_str} — {e}")
        return "N/A"

def format_odds_match(match):
    """Format odds match data for Telegram message."""
    odds = match.get("odds", {})
    updated = convert_to_persian_time(match.get("last_updated", ""))
    return (
        f"🏟 مسابقه: {match['home_team']} vs {match['away_team']}\n"
        f"🌍 کشور: {match.get('country', 'N/A')}\n"
        f"🏆 لیگ: {match.get('league', 'N/A')}\n"
        f"🎲 ضرایب:\n"
        f"▫️ برد میزبان: {odds.get('home_win', 'N/A')}\n"
        f"▫️ مساوی: {odds.get('draw', 'N/A')}\n"
        f"▫️ برد میهمان: {odds.get('away_win', 'N/A')}\n"
        f"🕓 آخرین به‌روزرسانی: {updated}"
    )

def format_results_match(match):
    """Format results match data for Telegram message."""
    score = match.get("score", {})
    updated = convert_to_persian_time(match.get("last_updated", ""))
    return (
        f"🏟 مسابقه: {match['team1']} vs {match['team2']}\n"
        f"🌍 کشور: {match.get('country', 'N/A')}\n"
        f"🏆 لیگ: {match.get('league', 'N/A')}\n"
        f"🔢 امتیاز: {score.get('team1', 'N/A')} - {score.get('team2', 'N/A')}\n"
        f"⏱ دقیقه: {match.get('minute', 'N/A')}\n"
        f"📊 وضعیت: {match.get('status', 'N/A')}\n"
        f"🕓 آخرین به‌روزرسانی: {updated}"
    )

def get_reply_keyboard():
    """Return the persistent reply keyboard."""
    keyboard = [["لیست ضرایب", "نتایج زنده"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with keyboard on /start and store chat ID."""
    chat_id = update.effective_chat.id
    add_chat_id(chat_id)
    reply_markup = get_reply_keyboard()
    await update.message.reply_text(
        "سلام! یکی از گزینه‌های زیر را انتخاب کن:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages, store chat ID, and respond based on user input."""
    chat_id = update.effective_chat.id
    add_chat_id(chat_id)
    text = update.message.text
    reply_markup = get_reply_keyboard()

    if text == "لیست ضرایب":
        odds = load_json_file("betforward_odds.json")
        if odds:
            for match in odds:
                await update.message.reply_text(
                    format_odds_match(match),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                "هیچ داده‌ای برای ضرایب موجود نیست.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    elif text == "نتایج زنده":
        results = load_json_file("betforward_results.json")
        if results:
            for match in results:
                await update.message.reply_text(
                    format_results_match(match),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                "هیچ داده‌ای برای نتایج زنده موجود نیست.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

def main():
    """Run the Telegram bot."""
    if not BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    logging.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()