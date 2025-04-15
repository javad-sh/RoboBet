from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
import re

def scrape_betforward_results(url):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # فعال کن اگه نمی‌خوای مرورگر باز شه
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("accept-language=fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)

        time.sleep(20)  # صبر برای لود کامل صفحه

        soup = BeautifulSoup(driver.page_source, "html.parser")
        matches = []
        match_elements = soup.find_all("div", class_="competition-bc")

        for match in match_elements:
            try:
                team_names = match.find_all("span", class_="c-team-info-team-bc team")
                scores = match.find_all("b", class_="c-team-info-scores-bc")
                time_info = match.find("span", class_="c-info-score-bc fixed-direction")

                if len(team_names) < 2 or len(scores) < 2:
                    continue

                team1 = team_names[0].text.strip()
                team2 = team_names[1].text.strip()
                score1 = scores[0].text.strip()
                score2 = scores[1].text.strip()

                minute = None
                match_status = "نامشخص"

                if time_info:
                    minute_match = re.search(r"(\d+)\s*`", time_info.text)
                    if minute_match:
                        minute = minute_match.group(1)
                        match_status = "در حال برگزاری"
                    else:
                        match_status = "بین دو نیمه"
                else:
                    match_status = "شروع نشده"

                match_info = {
                    "team1": team1,
                    "team2": team2,
                    "score": {
                        "team1": score1,
                        "team2": score2
                    },
                    "minute": minute,
                    "status": match_status
                }
                matches.append(match_info)

            except Exception as e:
                print(f"خطا در پردازش یک مسابقه: {e}")
                continue

        driver.quit()
        return matches

    except Exception as e:
        print(f"خطا در اسکریپینگ: {e}")
        if 'driver' in locals():
            driver.quit()
        return []

def save_odds_to_file(data, filename="betforward_results.json"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"داده‌ها در {filename} ذخیره شدند")
    except IOError as e:
        print(f"خطا در ذخیره داده: {e}")

def main():
    url = "https://m.betforward.com/en/sports/live/event-view/Soccer"
    results = scrape_betforward_results(url)

    if results:
        for match in results:
            status = match['status']
            print(f"{match['team1']} {match['score']['team1']} - {match['score']['team2']} {match['team2']}", end="")
            if status == "در حال برگزاری":
                print(f"  ({match['minute']}')")
            elif status == "بین دو نیمه":
                print("  (بین دو نیمه)")
            elif status == "شروع نشده":
                print("  (هنوز شروع نشده)")
            else:
                print()
        save_odds_to_file(results)
    else:
        print("هیچ نتیجه‌ای دریافت نشد.")

if __name__ == "__main__":
    main()


