import json
import os
import logging
from datetime import datetime
import pytz
import jdatetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
from telegram.constants import ParseMode

# ============================================================
# تنظیمات
# ============================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# مخفی کردن لاگ‌های HTTP تلگرام و خطاهای شبکه
logging.getLogger('httpx').setLevel(logging.CRITICAL)  # فقط خطاهای بحرانی
logging.getLogger('telegram').setLevel(logging.ERROR)  # فقط خطاهای مهم
logging.getLogger('httpcore').setLevel(logging.CRITICAL)

BOT_TOKEN = "7697466323:AAFXXszQt_lAPn4qCefx3VnnZYVhTuQiuno"

# ============================================================
# توابع کمکی
# ============================================================
def load_json(filename):
    """بارگذاری فایل JSON"""
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        logging.warning(f"File {filename} not found")
    except Exception as e:
        logging.error(f"Error loading {filename}: {e}")
    return []

def save_json(data, filename):
    """ذخیره داده در JSON"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving {filename}: {e}")

def add_chat_id(chat_id):
    """افزودن chat ID به لیست مشترکین"""
    chat_ids = load_json("chat_ids.json")
    chat_id_str = str(chat_id)
    if chat_id_str not in chat_ids:
        chat_ids.append(chat_id_str)
        save_json(chat_ids, "chat_ids.json")
        logging.info(f"➕ New subscriber: {chat_id} (Total: {len(chat_ids)})")
    else:
        logging.info(f"ℹ️ Already subscribed: {chat_id}")

def to_persian_time(iso_str):
    """تبدیل ISO time به زمان شمسی"""
    try:
        dt = datetime.fromisoformat(iso_str).astimezone(pytz.timezone("Asia/Tehran"))
        return jdatetime.datetime.fromgregorian(datetime=dt).strftime("%m/%d - %H:%M")
    except Exception as e:
        logging.warning(f"Time parse error: {iso_str} - {e}")
        return "N/A"

def format_odds(match):
    """فرمت ضرایب برای نمایش"""
    odds = match.get("odds", {})
    return (
        f"🏟 {match['home_team']} vs {match['away_team']}\n"
        f"🎲 ضرایب:\n"
        f"▫️ برد میزبان: {odds.get('home_win', 'N/A')}\n"
        f"▫️ مساوی: {odds.get('draw', 'N/A')}\n"
        f"▫️ برد میهمان: {odds.get('away_win', 'N/A')}\n"
        f"🕓 {to_persian_time(match.get('last_updated', ''))}"
    )

def format_results(match):
    """فرمت نتایج برای نمایش"""
    score = match.get("score", {})
    return (
        f"🏟 {match['team1']} vs {match['team2']}\n"
        f"🌍 {match.get('country', 'N/A')} | 🏆 {match.get('league', 'N/A')}\n"
        f"🔢 {score.get('team1', 'N/A')} - {score.get('team2', 'N/A')}\n"
        f"⏱ دقیقه: {match.get('minute', 'N/A')} | 📊 {match.get('status', 'N/A')}\n"
        f"🕓 {to_persian_time(match.get('last_updated', ''))}"
    )

def get_keyboard():
    """صفحه کلید دائمی"""
    return ReplyKeyboardMarkup([["لیست ضرایب", "نتایج زنده"]], resize_keyboard=True, one_time_keyboard=False)

# ============================================================
# Handler ها
# ============================================================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت خطاهای ربات"""
    error = context.error
    
    # خطاهای شبکه‌ای که نیاز به لاگ ندارند
    if isinstance(error, Exception):
        error_name = type(error).__name__
        if any(x in error_name for x in ['Network', 'Timeout', 'RemoteProtocol', 'Connection']):
            # این خطاها طبیعی هستند و خودکار retry می‌شوند
            return
    
    # فقط خطاهای مهم را لاگ کن
    logging.error(f"⚠️ Bot error: {error}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "Unknown"
    
    logging.info(f"\n{'='*60}\n👤 /start from: {chat_id} (@{username})\n{'='*60}")
    
    add_chat_id(chat_id)
    await update.message.reply_text("سلام! یکی از گزینه‌های زیر را انتخاب کن:", reply_markup=get_keyboard())
    logging.info(f"✅ Welcome sent to {chat_id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های دریافتی"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "Unknown"
    text = update.message.text
    
    logging.info(f"\n{'='*60}\n📩 Message from @{username} ({chat_id}): '{text}'\n{'='*60}")
    
    add_chat_id(chat_id)
    keyboard = get_keyboard()
    
    if text == "لیست ضرایب":
        logging.info(f"🎲 Processing odds request for {chat_id}")
        odds = load_json("betforward_odds.json")
        if odds:
            logging.info(f"📊 Sending {len(odds)} odds to {chat_id}")
            for idx, match in enumerate(odds, 1):
                logging.info(f"   [{idx}/{len(odds)}] {match['home_team']} vs {match['away_team']}")
                await update.message.reply_text(format_odds(match), parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            logging.info(f"✅ All odds sent to {chat_id}")
        else:
            logging.warning(f"⚠️ No odds for {chat_id}")
            await update.message.reply_text("هیچ داده‌ای برای ضرایب موجود نیست.", parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    
    elif text == "نتایج زنده":
        logging.info(f"⚽ Processing results request for {chat_id}")
        results = load_json("betforward_results.json")
        if results:
            logging.info(f"📊 Sending {len(results)} results to {chat_id}")
            for idx, match in enumerate(results, 1):
                logging.info(f"   [{idx}/{len(results)}] {match['team1']} vs {match['team2']}")
                await update.message.reply_text(format_results(match), parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            logging.info(f"✅ All results sent to {chat_id}")
        else:
            logging.warning(f"⚠️ No results for {chat_id}")
            await update.message.reply_text("هیچ داده‌ای برای نتایج زنده موجود نیست.", parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    
    else:
        logging.info(f"❓ Unknown message from {chat_id}")
        await update.message.reply_text("لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ============================================================
# نقطه ورود
# ============================================================
def main():
    """اجرای ربات"""
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN not set")
        return
    
    logging.info("\n" + "#"*60 + "\n# 🤖 Telegram Bot Starting 🤖\n" + "#"*60 + "\n")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # اضافه کردن error handler
    app.add_error_handler(error_handler)
    
    logging.info("🚀 Bot polling started\n✅ Ready for messages\n")
    
    # تنظیمات polling برای کاهش درخواست‌ها
    # poll_interval: فاصله بین درخواست‌ها (پیش‌فرض: 0 ثانیه)
    # timeout: زمان انتظار برای پاسخ تلگرام (پیش‌فرض: 10 ثانیه)
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        poll_interval=2.0,  # هر 2 ثانیه یکبار چک می‌کند
        timeout=30  # 30 ثانیه صبر می‌کند تا پیام جدید بیاید
    )

if __name__ == "__main__":
    main()
