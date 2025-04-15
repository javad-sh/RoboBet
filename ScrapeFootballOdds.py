from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time

def scrape_betforward_odds(url):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("accept-language=fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7")
    chrome_options.add_argument("--ignore-certificate-errors")

    try:
        # استفاده از webdriver_manager برای دانلود خودکار درایور
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get(url)
        time.sleep(20)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        matches = []
        match_elements = soup.find_all("div", class_="c-segment-holder-bc single-g-info-bc")

        for match in match_elements:
            try:
                teams = match.find_all("span", class_="c-team-info-team-bc team")
                if len(teams) < 2:
                    continue
                home_team = teams[0].text.strip()
                away_team = teams[1].text.strip()

                odds_elements = match.find_all("span", class_="market-odd-bc")
                if len(odds_elements) >= 3:
                    home_win = odds_elements[0].text.strip()
                    draw = odds_elements[1].text.strip()
                    away_win = odds_elements[2].text.strip()
                else:
                    continue

                match_info = {
                    "home_team": home_team,
                    "away_team": away_team,
                    "odds": {
                        "home_win": home_win,
                        "draw": draw,
                        "away_win": away_win
                    }
                }
                matches.append(match_info)

            except (AttributeError, IndexError):
                continue

        driver.quit()
        return matches

    except Exception as e:
        print(f"خطا در اسکریپینگ: {e}")
        if 'driver' in locals():
            driver.quit()
        return []

def save_odds_to_file(odds_data, filename="betforward_odds.json"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(odds_data, f, ensure_ascii=False, indent=4)
        print(f"داده‌ها در {filename} ذخیره شدند")
    except IOError as e:
        print(f"خطا در ذخیره داده: {e}")

def main():
    url = "https://m.betforward.com/en/sports/pre-match/event-view/Soccer?specialSection=upcoming-matches"
    odds = scrape_betforward_odds(url)

    if odds:
        for match in odds:
            print(f"{match['home_team']} vs {match['away_team']}:")
            print(f"  {match['home_team']}: {match['odds']['home_win']}")
            print(f"  Draw: {match['odds']['draw']}")
            print(f"  {match['away_team']}: {match['odds']['away_win']}\n")

        save_odds_to_file(odds)
    else:
        print("هیچ داده‌ای دریافت نشد.")

if __name__ == "__main__":
    main()
