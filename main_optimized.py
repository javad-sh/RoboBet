from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import re
import logging
import schedule
import time
from datetime import datetime, timedelta
import os
import telegram
import asyncio

# ============================================================
# تنظیمات و متغیرهای سراسری
# ============================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
BOT_TOKEN = "7697466323:AAFXXszQt_lAPn4qCefx3VnnZYVhTuQiuno"

# لیست سفید کشورها و لیگ‌ها
WHITELIST = {
    "انگلیس": ["لیگ برتر انگلیس", "جام حذفی انگلیس", "چمپیونشیپ انگلیس", "جام اتحادیه انگلیس", "سوپرجام انگلیس (جام خیریه)"],
    "اروپا": ["لیگ قهرمانان اروپا", "لیگ اروپا", "لیگ کنفرانس اروپا", "سوپر جام اروپا"],
    "آسیا": ["لیگ نخبگان آسیا", "لیگ قهرمانان آسیا ۲"],
    "ایتالیا": ["سری آ ایتالیا", "جام حذفی ایتالیا", "سوپر جام ایتالیا"],
    "اسپانیا": ["لالیگا اسپانیا", "کوپا دل ری اسپانیا"],
    "آلمان": ["بوندس‌لیگا آلمان", "جام حذفی آلمان"],
    "فرانسه": ["لیگ ۱ فرانسه", "جام حذفی فرانسه"],
    "برزیل": ["سری آ برزیل"],
    "عربستان سعودی": ["لیگ حرفه‌ای عربستان سعودی"],
    "ترکیه": ["سوپر لیگ ترکیه"],
    "هلند": ["لیگ برتر هلند", "جام حذفی هلند"],
    "پرتغال": ["لیگ برتر پرتغال", "جام حذفی پرتغال"],
    "اندونزی": ["سوپر لیگ اندونزی"],
}

# نرمال سازی WHITELIST
WHITELIST = {k.strip(): [l.strip() for l in v] for k, v in WHITELIST.items()}

# ============================================================
# توابع کمکی
# ============================================================
def normalize(s):
    """حذف فاصله‌های اضافی"""
    return " ".join(s.split()).strip() if s else ""

def get_circle_color(odds):
    """تعیین رنگ دایره بر اساس ضریب"""
    if odds <= 1.2: return "🟢"
    if odds <= 1.4: return "🟡"
    if odds <= 1.6: return "🟠"
    return "⚪"

def get_score_circle(score_diff):
    """تعیین رنگ دایره بر اساس اختلاف گل"""
    if score_diff > 1: return "🟢"
    if score_diff == 1: return "🟡"
    return "⚪"

def is_whitelisted(country, league):
    """بررسی اینکه مسابقه در لیست سفید است یا خیر"""
    country_norm = normalize(country)
    league_norm = normalize(league)
    return country_norm in WHITELIST and league_norm in WHITELIST.get(country_norm, [])

def load_json(filename):
    """بارگذاری فایل JSON"""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading {filename}: {e}")
    return []

def save_json(data, filename):
    """ذخیره داده در فایل JSON"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}")
    except IOError as e:
        logging.error(f"Error saving {filename}: {e}")

# ============================================================
# راه‌اندازی مرورگر
# ============================================================
def setup_driver():
    """راه‌اندازی Chrome با تنظیمات بهینه"""
    opts = Options()
    for arg in ["--headless", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                "--disable-extensions", "--disable-software-rasterizer", "--disable-background-networking",
                "--window-size=1920x1080", "--blink-settings=imagesEnabled=false",
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "accept-language=fa-IR,fa;q=0.9"]:
        opts.add_argument(arg)
    
    opts.add_experimental_option("prefs", {"profile.default_content_setting_values": {"images": 2, "stylesheets": 2}})
    
    try:
        driver = webdriver.Chrome(options=opts)
    except Exception as e:
        logging.error(f"Failed to init Chrome: {e}")
        opts.binary_location = "/data/data/com.termux/files/usr/bin/chromium-browser"
        driver = webdriver.Chrome(options=opts)
    
    try:
        driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*.css", "*.jpg", "*.jpeg", "*.png", "*.gif"]})
    except Exception as e:
        logging.warning(f"Could not block URLs: {e}")
    
    return driver

# ============================================================
# ارسال هشدار به تلگرام
# ============================================================
async def send_alerts(messages):
    """ارسال پیام‌های هشدار به کاربران"""
    bot = telegram.Bot(token=BOT_TOKEN)
    chat_ids = load_json("chat_ids.json")
    logging.info(f"📤 Sending {len(messages)} alert(s) to {len(chat_ids)} chat(s)")
    
    for idx, msg in enumerate(messages, 1):
        logging.info(f"\n{'='*60}\n📨 Alert {idx}/{len(messages)}:\n{'='*60}\n{msg}\n{'='*60}")
        for chat_id in chat_ids:
            try:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")
                logging.info(f"✅ Sent to {chat_id}")
                await asyncio.sleep(2)
            except Exception as e:
                logging.error(f"❌ Error sending to {chat_id}: {e}")

# ============================================================
# اسکرپ کردن ضرایب
# ============================================================
def scrape_odds(driver, url):
    """استخراج ضرایب مسابقات"""
    try:
        driver.get(url)
        WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CLASS_NAME, "c-segment-holder-bc")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        matches = []
        
        for match in soup.find_all("div", class_="c-segment-holder-bc single-g-info-bc"):
            try:
                teams = match.find_all("span", class_="c-team-info-team-bc team")
                if len(teams) < 2: continue
                
                odds_elems = match.find_all("span", class_="market-odd-bc")
                if len(odds_elems) < 3: continue
                
                matches.append({
                    "home_team": teams[0].text.strip(),
                    "away_team": teams[1].text.strip(),
                    "odds": {
                        "home_win": odds_elems[0].text.strip(),
                        "draw": odds_elems[1].text.strip(),
                        "away_win": odds_elems[2].text.strip()
                    },
                    "last_updated": datetime.now().isoformat()
                })
            except Exception as e:
                logging.error(f"Error processing match: {e}")
        
        return matches
    except Exception as e:
        logging.error(f"Error scraping odds: {e}")
        return []

# ============================================================
# اسکرپ کردن نتایج زنده
# ============================================================
def scrape_results(driver, url):
    """استخراج نتایج مسابقات زنده"""
    try:
        driver.get(url)
        WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CLASS_NAME, "c-team-info-scores-bc")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        matches = []
        
        for comp in soup.find_all("div", class_="competition-bc"):
            try:
                titles = comp.find_all("span", class_="c-title-bc ellipsis")
                country = titles[0].text.strip() if len(titles) > 0 else "Unknown"
                league = titles[1].text.strip() if len(titles) > 1 else "Unknown"
                
                for match in comp.find_all("div", class_="c-segment-holder-bc single-g-info-bc"):
                    try:
                        teams = match.find_all("span", class_="c-team-info-team-bc team")
                        scores = match.find_all("b", class_="c-team-info-scores-bc")
                        time_info = match.find("span", class_="c-info-score-bc fixed-direction")
                        
                        if len(teams) < 2 or len(scores) < 2: continue
                        
                        minute, status = None, "Unknown"
                        if time_info:
                            time_text = time_info.text.strip()
                            minute_match = re.search(r"(\d+)(?:\s*\+\s*(\d+))?\s*`", time_text)
                            if minute_match:
                                base = int(minute_match.group(1))
                                extra = int(minute_match.group(2)) if minute_match.group(2) else 0
                                minute = f"{base}+{extra}" if extra else str(base)
                                status = "وقت اضافه" if base > 90 or extra else "در جریان"
                            else:
                                sibling = match.find("span", class_="c-info-score-bc")
                                status = sibling.text.strip() if sibling else "Unknown"
                        else:
                            status = "شروع نشده"
                        
                        matches.append({
                            "team1": teams[0].text.strip(),
                            "team2": teams[1].text.strip(),
                            "score": {"team1": scores[0].text.strip(), "team2": scores[1].text.strip()},
                            "minute": minute,
                            "status": status,
                            "country": country,
                            "league": league,
                            "last_updated": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logging.error(f"Error processing match: {e}")
            except Exception as e:
                logging.error(f"Error processing competition: {e}")
        
        return matches
    except Exception as e:
        logging.error(f"Error scraping results: {e}")
        return []

# ============================================================
# به‌روزرسانی فایل‌های JSON
# ============================================================
def update_odds_file(new_odds, filename="betforward_odds.json"):
    """به‌روزرسانی فایل ضرایب"""
    current = load_json(filename)
    updated = []
    current_time = datetime.now()
    new_set = {(m["home_team"], m["away_team"]) for m in new_odds}
    
    for new_m in new_odds:
        match_id = (new_m["home_team"], new_m["away_team"])
        existing = next((m for m in current if (m["home_team"], m["away_team"]) == match_id), None)
        
        if existing and existing["odds"] != new_m["odds"]:
            new_m["last_updated"] = current_time.isoformat()
            logging.info(f"Updated odds: {match_id[0]} vs {match_id[1]}")
        updated.append(new_m if not existing or existing["odds"] != new_m["odds"] else existing)
    
    for old_m in current:
        match_id = (old_m["home_team"], old_m["away_team"])
        if match_id not in new_set:
            last = datetime.fromisoformat(old_m["last_updated"])
            if current_time - last <= timedelta(hours=3):
                updated.append(old_m)
    
    save_json(updated, filename)

def update_results_file(new_results, filename="betforward_results.json"):
    """به‌روزرسانی فایل نتایج"""
    current = load_json(filename)
    updated = []
    current_time = datetime.now()
    new_set = {(m["team1"], m["team2"]) for m in new_results}
    
    for new_m in new_results:
        updated.append(new_m)
    
    for old_m in current:
        match_id = (old_m["team1"], old_m["team2"])
        if match_id not in new_set:
            last = datetime.fromisoformat(old_m["last_updated"])
            if current_time - last <= timedelta(minutes=30):
                updated.append(old_m)
    
    save_json(updated, filename)

# ============================================================
# تولید هشدارها
# ============================================================
def generate_alert(match, home_odds, away_odds, team_key, team_name, opponent_name, team_odds, team_score, opp_score, minute):
    """تولید پیام هشدار برای یک تیم"""
    circle1 = get_circle_color(team_odds)
    circle2 = get_score_circle(opp_score - team_score)
    opp_odds = away_odds if team_key == "team1" else home_odds
    
    return (
        f"{circle1}{circle2} هشدار: در کشور <b>{match['country']}</b> در لیگ <b>{match['league']}</b> "
        f"{team_name} (ضریب: {team_odds}) در دقیقه {minute or match['status']} "
        f"با نتیجه {team_score}-{opp_score} از {opponent_name} (ضریب: {opp_odds}) عقب است!\n"
        f"📝 پیشنهاد: 1- کرنر یا شوت زدن قوی 2- کرنر یا شوت نزدن ضعیف 3- گل زدن قوی"
    )

def check_alerts(match, odds_data):
    """بررسی و تولید هشدارها برای یک مسابقه"""
    if not is_whitelisted(match["country"], match["league"]):
        return []
    
    if match["status"] not in ["در جریان", "وقت اضافه", "بین دو نیمه", "تایم اوت"]:
        return []
    
    odds_match = next((m for m in odds_data if (m["home_team"], m["away_team"]) == (match["team1"], match["team2"])), None)
    if not odds_match:
        return []
    
    alerts = []
    try:
        home_odds = float(odds_match["odds"]["home_win"]) if odds_match["odds"]["home_win"] != "N/A" else float("inf")
        away_odds = float(odds_match["odds"]["away_win"]) if odds_match["odds"]["away_win"] != "N/A" else float("inf")
        score1 = int(match["score"]["team1"]) if match["score"]["team1"].isdigit() else 0
        score2 = int(match["score"]["team2"]) if match["score"]["team2"].isdigit() else 0
        minute = match["minute"]
        
        base_minute = 30 if not minute or not minute.strip() else int(minute.split("+")[0])
        
        # شرط 1: دقیقه 60+ و تیم با ضریب پایین عقب است
        if base_minute >= 60:
            if home_odds <= 1.6 and score1 < score2:
                alerts.append(generate_alert(match, home_odds, away_odds, "team1", match["team1"], match["team2"], home_odds, score1, score2, minute))
            if away_odds <= 1.6 and score2 < score1:
                alerts.append(generate_alert(match, home_odds, away_odds, "team2", match["team2"], match["team1"], away_odds, score2, score1, minute))
        
        # شرط 2: بین دو نیمه و مساوی
        if match["status"] == "بین دو نیمه" and score1 == score2:
            if home_odds <= 1.6 or away_odds <= 1.6:
                circle1 = get_circle_color(min(home_odds, away_odds))
                circle2 = "🟢" if score1 == 0 and score2 == 0 else "🟡"
                alerts.append(
                    f"{circle1}{circle2} هشدار: در کشور {match['country']} در لیگ {match['league']} "
                    f"مسابقه بین {match['team1']} (ضریب: {home_odds}) و {match['team2']} (ضریب: {away_odds}) "
                    f"در نیمه اول با نتیجه {score1}-{score2} مساوی است!\n"
                    f"📝 پیشنهاد: 1_گل داشتن بازی 2_گل زدن تیم قوی"
                )
        
        # شرط 3: بین دو نیمه، ضریب کمتر از 1.4، گل نزده و عقب است
        if match["status"] == "بین دو نیمه":
            checks = [
                ("team1", home_odds, score1, score2, match["team1"], match["team2"], away_odds),
                ("team2", away_odds, score2, score1, match["team2"], match["team1"], home_odds),
            ]
            for team_key, team_odd, team_score, opp_score, team_name, opp_name, opp_odd in checks:
                if team_odd < 1.4 and team_score == 0 and team_score < opp_score:
                    circle = "🟢" if team_odd < 1.2 else "🟡"
                    alerts.append(
                        f"{circle} هشدار: در کشور <b>{match['country']}</b> در لیگ <b>{match['league']}</b> "
                        f"{team_name} (ضریب: {team_odd}) در وضعیت <b>{match['status']}</b> "
                        f"با نتیجه {team_score}-{opp_score} از {opp_name} (ضریب: {opp_odd}) عقب است و هنوز گلی نزده!\n"
                        f"📝 پیشنهاد: گل داشتن بازی تا دقیقه ۷۰"
                    )
    except (ValueError, KeyError) as e:
        logging.warning(f"Error processing match data: {e}")
    
    return alerts

# ============================================================
# Job ها
# ============================================================
def scrape_odds_job():
    """وظیفه اسکرپ ضرایب"""
    logging.info("\n" + "="*60 + "\n🎲 Starting ODDS job\n" + "="*60)
    driver = setup_driver()
    try:
        odds = scrape_odds(driver, "https://m.betforward.com/fa/sports/pre-match/event-view/Soccer?specialSection=upcoming-matches")
        if odds:
            logging.info(f"📊 Retrieved {len(odds)} odds")
            update_odds_file(odds)
            logging.info("✅ Odds updated")
        else:
            logging.warning("⚠️ No odds retrieved")
    except Exception as e:
        logging.error(f"❌ Error in odds job: {e}")
    finally:
        driver.quit()
        logging.info("🏁 Odds job completed\n")

def scrape_results_job():
    """وظیفه اسکرپ نتایج"""
    logging.info("\n" + "="*60 + "\n⚽ Starting RESULTS job\n" + "="*60)
    driver = setup_driver()
    try:
        results = scrape_results(driver, "https://m.betforward.com/fa/sports/live/event-view/Soccer")
        if results:
            logging.info(f"📊 Retrieved {len(results)} live matches")
            odds_data = load_json("betforward_odds.json")
            
            alerts = []
            for match in results:
                alerts.extend(check_alerts(match, odds_data))
            
            if alerts:
                logging.info(f"\n🚨 Generated {len(alerts)} alerts")
                asyncio.run(send_alerts(alerts))
                logging.info("\n✅ All alerts sent")
            else:
                logging.info("ℹ️ No alerts generated")
            
            update_results_file(results)
            logging.info("✅ Results updated")
        else:
            logging.warning("⚠️ No results retrieved")
    except Exception as e:
        logging.error(f"❌ Error in results job: {e}")
    finally:
        driver.quit()
        logging.info("🏁 Results job completed\n")

def run_schedule():
    """اجرای زمان‌بند"""
    schedule.every(20).minutes.do(scrape_odds_job)
    schedule.every(5).minutes.do(scrape_results_job)
    logging.info("\n" + "="*60 + "\n⏰ Scheduler started\n📅 Odds: Every 20min | Results: Every 5min\n" + "="*60 + "\n")
    while True:
        schedule.run_pending()
        time.sleep(60)

# ============================================================
# نقطه ورود برنامه
# ============================================================
if __name__ == "__main__":
    try:
        logging.info("\n" + "#"*60 + "\n# 🤖 RoboBet Started 🤖\n" + "#"*60 + "\n")
        scrape_odds_job()
        scrape_results_job()
        run_schedule()
    except KeyboardInterrupt:
        logging.info("\n\n🛑 Stopped by user")
    except Exception as e:
        logging.error(f"\n\n❌ Fatal error: {e}")
