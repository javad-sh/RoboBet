from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Bot token
BOT_TOKEN = "7697466323:AAFXXszQt_lAPn4qCefx3VnnZYVhTuQiuno"


def normalize_string(s):
    """Normalize a string by removing extra spaces and trimming."""
    if not s:
        return ""
    return " ".join(s.split()).strip()


# Define whitelist as a dictionary mapping countries to allowed leagues
WHITELIST = {
    normalize_string("انگلیس"): [
        normalize_string("لیگ برتر انگلیس"),
        normalize_string("جام حذفی انگلیس"),
        normalize_string("چمپیونشیپ انگلیس"),
        normalize_string("جام اتحادیه انگلیس"),
        normalize_string("سوپرجام انگلیس (جام خیریه)"),
        
    ],
    normalize_string("اروپا"): [
        normalize_string("لیگ قهرمانان اروپا"),
        normalize_string("لیگ اروپا"),
        normalize_string("لیگ کنفرانس اروپا"),
        normalize_string("سوپر جام اروپا"),
    ],
    normalize_string("آسیا"): [
        normalize_string("لیگ نخبگان آسیا"),
        normalize_string("لیگ قهرمانان آسیا ۲"),
    ],
    normalize_string("ایتالیا"): [
        normalize_string("سری آ ایتالیا"),
        normalize_string("جام حذفی ایتالیا"),
        normalize_string("سوپر جام ایتالیا"),
    ],
    normalize_string("اسپانیا"): [
        normalize_string("لالیگا اسپانیا"),
        normalize_string("کوپا دل ری اسپانیا"),
    ],
    normalize_string("آلمان"): [
        normalize_string("بوندس‌لیگا آلمان"),
        normalize_string("جام حذفی آلمان"),
    ],
    normalize_string("فرانسه"): [
        normalize_string("لیگ ۱ فرانسه"),
        normalize_string("جام حذفی فرانسه"),
    ],
    normalize_string("برزیل"): [normalize_string("سری آ برزیل")],
    normalize_string("عربستان سعودی"): [normalize_string("لیگ حرفه‌ای عربستان سعودی")],
    normalize_string("ترکیه"): [normalize_string("سوپر لیگ ترکیه")],
    normalize_string("هلند"): [
        normalize_string("لیگ برتر هلند"),
        normalize_string("جام حذفی هلند"),
    ],
    normalize_string("پرتغال"): [
        normalize_string("لیگ برتر پرتغال"),
        normalize_string("جام حذفی پرتغال"),
    ],
}


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    chrome_options.add_argument("accept-language=fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_experimental_option(
        "prefs",
        {"profile.default_content_setting_values": {"images": 2, "stylesheets": 2}},
    )

    chrome_options.binary_location = "/usr/bin/google-chrome"
    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {"urls": ["*.css", "*.jpg", "*.jpeg", "*.png", "*.gif"]},
    )

    return driver


def load_json_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading {filename}: {e}")
            return []
    return []


async def send_all_alerts(messages):
    """Send all alert messages to subscribed chat IDs with a 5-second delay between each."""
    bot = telegram.Bot(token=BOT_TOKEN)
    chat_ids = load_json_file("chat_ids.json")
    for message in messages:
        for chat_id in chat_ids:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=telegram.constants.ParseMode.MARKDOWN,
                )
                logging.info(f"Sent alert to chat ID {chat_id}: {message[:50]}...")
                await asyncio.sleep(2)
            except Exception as e:
                logging.error(f"Error sending message to chat ID {chat_id}: {e}")


def scrape_betforward_odds(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-segment-holder-bc"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        matches = []
        match_elements = soup.find_all(
            "div", class_="c-segment-holder-bc single-g-info-bc"
        )

        for match in match_elements:
            try:
                teams = match.find_all("span", class_="c-team-info-team-bc team")
                if len(teams) < 2:
                    logging.warning("Number of teams is less than 2")
                    continue
                home_team = teams[0].text.strip()
                away_team = teams[1].text.strip()

                odds_elements = match.find_all("span", class_="market-odd-bc")
                odds = {"home_win": "N/A", "draw": "N/A", "away_win": "N/A"}
                if len(odds_elements) >= 3:
                    odds["home_win"] = odds_elements[0].text.strip()
                    odds["draw"] = odds_elements[1].text.strip()
                    odds["away_win"] = odds_elements[2].text.strip()
                else:
                    logging.warning(f"Insufficient odds for {home_team} vs {away_team}")
                    continue

                match_info = {
                    "home_team": home_team,
                    "away_team": away_team,
                    "odds": odds,
                    "last_updated": datetime.now().isoformat(),
                }
                matches.append(match_info)
            except Exception as e:
                logging.error(f"Error processing match: {e}")
                continue

        return matches

    except Exception as e:
        logging.error(f"Error scraping odds: {e}")
        return []


def scrape_betforward_results(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-team-info-scores-bc"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        matches = []
        competition_elements = soup.find_all("div", class_="competition-bc")

        for competition in competition_elements:
            try:
                title_elements = competition.find_all(
                    "span", class_="c-title-bc ellipsis"
                )
                if len(title_elements) < 2:
                    logging.warning("Insufficient title elements for competition")
                    country = "Unknown"
                    league = "Unknown"
                else:
                    country = title_elements[0].text.strip()
                    league = title_elements[1].text.strip()

                match_elements = competition.find_all(
                    "div", class_="c-segment-holder-bc single-g-info-bc"
                )

                for match in match_elements:
                    try:
                        team_names = match.find_all(
                            "span", class_="c-team-info-team-bc team"
                        )
                        scores = match.find_all("b", class_="c-team-info-scores-bc")
                        time_info = match.find(
                            "span", class_="c-info-score-bc fixed-direction"
                        )

                        if len(team_names) < 2 or len(scores) < 2:
                            logging.warning("Insufficient number of teams or scores")
                            continue

                        team1 = team_names[0].text.strip()
                        team2 = team_names[1].text.strip()
                        score1 = scores[0].text.strip()
                        score2 = scores[1].text.strip()

                        minute = None
                        match_status = "Unknown"
                        extra_info = None

                        if time_info:
                            time_text = time_info.text.strip()
                            minute_match = re.search(
                                r"(\d+)(?:\s*\+\s*(\d+))?\s*`", time_text
                            )
                            if minute_match:
                                base_minute = int(minute_match.group(1))
                                extra_minute = (
                                    int(minute_match.group(2))
                                    if minute_match.group(2)
                                    else 0
                                )
                                minute = (
                                    f"{base_minute}+{extra_minute}"
                                    if extra_minute
                                    else str(base_minute)
                                )
                                if base_minute > 90 or extra_minute:
                                    match_status = "وقت اضافه"
                                else:
                                    match_status = "در جریان"
                            else:
                                sibling_status_tag = match.find(
                                    "span", class_="c-info-score-bc"
                                )
                                if sibling_status_tag:
                                    match_status = sibling_status_tag.text.strip()
                                else:
                                    match_status = "Unknown"

                            extra_info_match = re.search(r"\((\d+):(\d+)\)", time_text)
                            if extra_info_match:
                                extra_info = [
                                    {
                                        "team1": int(extra_info_match.group(1)),
                                        "team2": int(extra_info_match.group(2)),
                                    }
                                ]
                        else:
                            match_status = "شروع نشده"

                        match_info = {
                            "team1": team1,
                            "team2": team2,
                            "score": {"team1": score1, "team2": score2},
                            "minute": minute,
                            "status": match_status,
                            "extra_info": extra_info,
                            "country": country,
                            "league": league,
                            "last_updated": datetime.now().isoformat(),
                        }
                        matches.append(match_info)
                    except Exception as e:
                        logging.error(f"Error processing match: {e}")
                        continue
            except Exception as e:
                logging.error(f"Error processing competition: {e}")
                continue

        return matches

    except Exception as e:
        logging.error(f"Error scraping results: {e}")
        return []


def save_to_file(data, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}")
    except IOError as e:
        logging.error(f"Error saving data: {e}")


def update_odds_file(new_odds, filename="betforward_odds.json"):
    current_odds = load_json_file(filename)
    updated_odds = []
    current_time = datetime.now()

    new_matches = {(match["home_team"], match["away_team"]) for match in new_odds}

    for new_match in new_odds:
        match_id = (new_match["home_team"], new_match["away_team"])
        existing_match = next(
            (m for m in current_odds if (m["home_team"], m["away_team"]) == match_id),
            None,
        )

        if existing_match:
            if existing_match["odds"] != new_match["odds"]:
                new_match["last_updated"] = current_time.isoformat()
                updated_odds.append(new_match)
                logging.info(f"Updated odds for {match_id[0]} vs {match_id[1]}")
            else:
                updated_odds.append(existing_match)
        else:
            updated_odds.append(new_match)
            logging.info(f"Added new match: {match_id[0]} vs {match_id[1]}")

    for existing_match in current_odds:
        match_id = (existing_match["home_team"], existing_match["away_team"])
        if match_id not in new_matches:
            last_updated = datetime.fromisoformat(existing_match["last_updated"])
            if current_time - last_updated > timedelta(hours=3):
                logging.info(f"Removing old match: {match_id[0]} vs {match_id[1]}")
                continue
            updated_odds.append(existing_match)

    save_to_file(updated_odds, filename)


def update_results_file(new_results, filename="betforward_results.json"):
    current_results = load_json_file(filename)
    updated_results = []
    new_matches = {(match["team1"], match["team2"]) for match in new_results}
    current_time = datetime.now()

    for new_match in new_results:
        match_id = (new_match["team1"], new_match["team2"])
        existing_match = next(
            (m for m in current_results if (m["team1"], m["team2"]) == match_id), None
        )

        if existing_match:
            updated_results.append(new_match)
            if (
                existing_match["score"] != new_match["score"]
                or existing_match["status"] != new_match["status"]
                or existing_match["minute"] != new_match["minute"]
            ):
                logging.info(f"Updated result for {match_id[0]} vs {match_id[1]}")
        else:
            updated_results.append(new_match)
            logging.info(f"Added new result: {match_id[0]} vs {match_id[1]}")

    for existing_match in current_results:
        match_id = (existing_match["team1"], existing_match["team2"])
        if match_id not in new_matches:
            last_updated = datetime.fromisoformat(existing_match["last_updated"])
            if current_time - last_updated > timedelta(minutes=30):
                logging.info(f"Removing old match: {match_id[0]} vs {match_id[1]}")
                continue
            updated_results.append(existing_match)

    save_to_file(updated_results, filename)


def scrape_odds_job():
    odds_url = "https://m.betforward.com/fa/sports/pre-match/event-view/Soccer?specialSection=upcoming-matches"
    driver = setup_driver()
    try:
        odds = scrape_betforward_odds(driver, odds_url)
        if odds:
            update_odds_file(odds, "betforward_odds.json")
            logging.info("Odds updated successfully")
        else:
            logging.warning("No odds retrieved.")
    finally:
        driver.quit()


def scrape_results_job():
    results_url = "https://m.betforward.com/fa/sports/live/event-view/Soccer"
    driver = setup_driver()
    try:
        results = scrape_betforward_results(driver, results_url)
        if results:
            odds_data = load_json_file("betforward_odds.json")
            alert_messages = []

            for match in results:
                match_id = (match["team1"], match["team2"])
                odds_match = next(
                    (
                        m
                        for m in odds_data
                        if (m["home_team"], m["away_team"]) == match_id
                    ),
                    None,
                )

                if odds_match:
                    try:
                        home_odds = (
                            float(odds_match["odds"]["home_win"])
                            if odds_match["odds"]["home_win"] != "N/A"
                            else float("inf")
                        )
                        away_odds = (
                            float(odds_match["odds"]["away_win"])
                            if odds_match["odds"]["away_win"] != "N/A"
                            else float("inf")
                        )
                        score1 = (
                            int(match["score"]["team1"])
                            if match["score"]["team1"].isdigit()
                            else 0
                        )
                        score2 = (
                            int(match["score"]["team2"])
                            if match["score"]["team2"].isdigit()
                            else 0
                        )
                        minute = match["minute"]
                        logging.info(match["status"])
                        alert_messages.append(match["status"])

                        if True:
                            try:
                                if not minute or minute.strip() == "":
                                    base_minute = 30
                                else:
                                    base_minute = int(minute.split("+")[0])

                                if base_minute >= 5:
                                    # if normalize_string(
                                    #     match["country"]
                                    # ) in WHITELIST and normalize_string(
                                    #     match["league"]
                                    # ) in WHITELIST.get(
                                    #     normalize_string(match["country"]), []
                                    # ):
                                        # دایره اول بر اساس ضریب
                                        circle_color = "⚪"
                                        if 1.4 < home_odds <= 1.6:
                                            circle_color = "🟠"
                                        elif 1.2 < home_odds <= 1.4:
                                            circle_color = "🟡"
                                        elif home_odds <= 1.2:
                                            circle_color = "🟢"

                                        # دایره دوم بر اساس اختلاف گل برای تیم میزبان
                                        circle_color_diff = "⚪"
                                        score_diff = (
                                            score2 - score1
                                        )  # اختلاف گل (میهمان - میزبان)
                                        if score_diff == 1:
                                            circle_color_diff = "🟡"  # یک گل عقب
                                        elif score_diff > 1:
                                            circle_color_diff = "🟢"  # بیش از یک گل عقب

                                        if home_odds >= 1.6 and score1 < score2:
                                            alert_message = (
                                                f"{circle_color}{circle_color_diff} هشدار: در کشور **{match['country']}** در لیگ **{match['league']}** "
                                                f"{match['team1']} (ضریب: {home_odds}) در دقیقه {minute or match['status']} "
                                                f"با نتیجه {score1}-{score2} از {match['team2']} (ضریب: {away_odds}) عقب است!\n"
                                                f"📝 پیشنهاد: 1_کرنر یا شوت زدن قوی 2_کرنر یا شوت نزدن ضعیف 3_گل زدن قوی"
                                            )
                                            logging.info(alert_message)
                                            alert_messages.append(alert_message)

                                        # دایره اول بر اساس ضریب برای تیم میهمان
                                        circle_color = "⚪"
                                        if 1.4 < away_odds <= 1.6:
                                            circle_color = "🟠"
                                        elif 1.2 < away_odds <= 1.4:
                                            circle_color = "🟡"
                                        elif away_odds <= 1.2:
                                            circle_color = "🟢"

                                        # دایره دوم بر اساس اختلاف گل برای تیم میهمان
                                        circle_color_diff = "⚪"
                                        score_diff = (
                                            score1 - score2
                                        )  # اختلاف گل (میزبان - میهمان)
                                        if score_diff == 1:
                                            circle_color_diff = "🟡"  # یک گل عقب
                                        elif score_diff > 1:
                                            circle_color_diff = "🟢"  # بیش از یک گل عقب

                                        if away_odds >= 1.6 and score2 < score1:
                                            alert_message = (
                                                f"{circle_color}{circle_color_diff} هشدار: در کشور **{match['country']}** در لیگ **{match['league']}** "
                                                f"{match['team2']} (ضریب: {away_odds}) در دقیقه {minute or match['status']} "
                                                f"با نتیجه {score2}-{score1} از {match['team1']} (ضریب: {home_odds}) عقب است!\n"
                                                f"📝 پیشنهاد: 1_کرنر یا شوت زدن قوی 2_کرنر یا شوت نزدن ضعیف 3_گل زدن قوی"
                                            )
                                            logging.info(alert_message)
                                            alert_messages.append(alert_message)

                                # New condition: Halftime, tied score, and low odds
                                if match["status"] == "بین دو نیمه" and score1 == score2:
                                    if normalize_string(
                                        match["country"]
                                    ) in WHITELIST and normalize_string(
                                        match["league"]
                                    ) in WHITELIST.get(
                                        normalize_string(match["country"]), []
                                    ):
                                        if home_odds <= 1.6 or away_odds <= 1.6:
                                            # Determine which team has low odds
                                            low_odds_team = None
                                            low_odds_value = None
                                            if home_odds <= 1.6:
                                                low_odds_team = match["team1"]
                                                low_odds_value = home_odds
                                            elif away_odds <= 1.6:
                                                low_odds_team = match["team2"]
                                                low_odds_value = away_odds

                                            if low_odds_team:
                                                # دایره اول بر اساس ضریب
                                                circle_color = "⚪"
                                                if 1.4 < low_odds_value <= 1.6:
                                                    circle_color = "🟠"
                                                elif 1.2 < low_odds_value <= 1.4:
                                                    circle_color = "🟡"
                                                elif low_odds_value <= 1.2:
                                                    circle_color = "🟢"

                                                # دایره دوم بر اساس نتیجه
                                                circle_color_diff = "⚪"
                                                if score1 == 0 and score2 == 0:
                                                    circle_color_diff = "🟢"  # 0-0
                                                elif score1 > 0 and score2 > 0:
                                                    circle_color_diff = "🟡"  # Tied with goals

                                                alert_message = (
                                                    f"{circle_color}{circle_color_diff} هشدار: در کشور **{match['country']}** در لیگ **{match['league']}** "
                                                    f"مسابقه بین {match['team1']} (ضریب: {home_odds}) و {match['team2']} (ضریب: {away_odds}) "
                                                    f"در نیمه اول با نتیجه {score1}-{score2} مساوی است!\n"
                                                    f"📝 پیشنهاد: 1_گل داشتن بازی 2_گل زدن تیم قوی"
                                                )
                                                logging.info(alert_message)
                                                alert_messages.append(alert_message)

                            except ValueError:
                                logging.warning(
                                    f"Invalid minute format for {match_id[0]} vs {match_id[1]}: {minute}"
                                )
                    except ValueError as e:
                        logging.warning(
                            f"Error processing odds or scores for {match_id[0]} vs {match_id[1]}: {e}"
                        )

            if alert_messages:
                asyncio.run(send_all_alerts(alert_messages))
                logging.info("All alerts sent successfully")

            update_results_file(results, "betforward_results.json")
            logging.info("Results updated successfully")
        else:
            logging.warning("No results retrieved.")
    finally:
        driver.quit()


def run_schedule():
    schedule.every(20).minutes.do(scrape_odds_job)
    schedule.every(5).minutes.do(scrape_results_job)
    logging.info("Scheduler started. Odds and Results every 3 minutes.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    try:
        scrape_odds_job()
        scrape_results_job()
        run_schedule()
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user.")