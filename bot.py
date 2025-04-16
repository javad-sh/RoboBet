import json
import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
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

def format_odds_match(match):
    """Format odds match data for Telegram message."""
    odds = match.get("odds", {})
    return (
        f"مسابقه: {match['home_team']} vs {match['away_team']}\n"
        f"ضرایب:\n"
        f"برد میزبان: {odds.get('home_win', 'N/A')}\n"
        f"مساوی: {odds.get('draw', 'N/A')}\n"
        f"برد میهمان: {odds.get('away_win', 'N/A')}\n"
        f"آخرین به‌روزرسانی: {match.get('last_updated', 'N/A')}"
    )

def format_results_match(match):
    """Format results match data for Telegram message."""
    score = match.get("score", {})
    return (
        f"مسابقه: {match['team1']} vs {match['team2']}\n"
        f"امتیاز: {score.get('team1', 'N/A')} - {score.get('team2', 'N/A')}\n"
        f"دقیقه: {match.get('minute', 'N/A')}\n"
        f"وضعیت: {match.get('status', 'N/A')}\n"
        f"آخرین به‌روزرسانی: {match.get('last_updated', 'N/A')}"
    )

def get_keyboard():
    """Return the persistent inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("لیست ضرایب", callback_data="odds"),
            InlineKeyboardButton("نتایج زنده", callback_data="results"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any incoming message and display the keyboard."""
    await update.message.reply_text(
        "لطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=get_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks and send JSON file contents."""
    query = update.callback_query
    await query.answer()

    if query.data == "odds":
        odds = load_json_file("betforward_odds.json")
        if odds:
            for match in odds:
                await query.message.reply_text(format_odds_match(match), parse_mode=ParseMode.MARKDOWN)
        else:
            await query.message.reply_text("هیچ داده‌ای برای ضرایب موجود نیست.", parse_mode=ParseMode.MARKDOWN)
    elif query.data == "results":
        results = load_json_file("betforward_results.json")
        if results:
            for match in results:
                await query.message.reply_text(format_results_match(match), parse_mode=ParseMode.MARKDOWN)
        else:
            await query.message.reply_text("هیچ داده‌ای برای نتایج زنده موجود نیست.", parse_mode=ParseMode.MARKDOWN)

    # Re-display the keyboard after sending data
    await query.message.reply_text(
        "لطفاً گزینه دیگری انتخاب کنید:",
        reply_markup=get_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

def main():
    """Run the Telegram bot."""
    if not BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start the bot
    logging.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()