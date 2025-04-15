from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import re
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Enabled to reduce resource usage
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    chrome_options.add_argument("accept-language=fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_betforward_odds(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-segment-holder-bc"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        matches = []
        match_elements = soup.find_all("div", class_="c-segment-holder-bc single-g-info-bc")

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
                    "odds": odds
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
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-team-info-team-bc"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        matches = []
        match_elements = soup.find_all("div", class_="c-segment-holder-bc single-g-info-bc")

        for match in match_elements:
            try:
                team_names = match.find_all("span", class_="c-team-info-team-bc team")
                scores = match.find_all("b", class_="c-team-info-scores-bc")
                time_info = match.find("span", class_="c-info-score-bc fixed-direction")

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
                    # Pattern to handle regular minutes (e.g., 45') and extra time (e.g., 90+7')
                    minute_match = re.search(r"(\d+)(?:\s*\+\s*(\d+))?\s*`", time_text)
                    if minute_match:
                        base_minute = int(minute_match.group(1))
                        extra_minute = int(minute_match.group(2)) if minute_match.group(2) else 0
                        minute = f"{base_minute}+{extra_minute}" if extra_minute else str(base_minute)
                        if base_minute > 90 or extra_minute:
                            match_status = "Extra Time"
                        else:
                            match_status = "In Progress"
                    elif "HT" in time_text.upper():
                        match_status = "Half Time"
                    elif "FT" in time_text.upper():
                        match_status = "Finished"
                    else:
                        match_status = "Unknown"
                    
                    # Extract additional info like (3:3), (1:1)
                    extra_info_match = re.search(r"\((\d+):(\d+)\)", time_text)
                    if extra_info_match:
                        extra_info = [{"team1": int(extra_info_match.group(1)), "team2": int(extra_info_match.group(2))} ]

                else:
                    match_status = "Not Started"

                match_info = {
                    "team1": team1,
                    "team2": team2,
                    "score": {
                        "team1": score1,
                        "team2": score2
                    },
                    "minute": minute,
                    "status": match_status,
                    "extra_info": extra_info
                }
                matches.append(match_info)
            except Exception as e:
                logging.error(f"Error processing match: {e}")
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

def main():
    odds_url = "https://m.betforward.com/en/sports/pre-match/event-view/Soccer?specialSection=upcoming-matches"
    results_url = "https://m.betforward.com/en/sports/live/event-view/Soccer"
    
    driver = setup_driver()
    try:
        # Scrape odds
        odds = scrape_betforward_odds(driver, odds_url)
        if odds:
            print("Upcoming matches odds:")
            for match in odds:
                print(f"{match['home_team']} vs {match['away_team']}:")
                print(f"  {match['home_team']} win: {match['odds']['home_win']}")
                print(f"  Draw: {match['odds']['draw']}")
                print(f"  {match['away_team']} win: {match['odds']['away_win']}\n")
            save_to_file(odds, "betforward_odds.json")
        else:
            print("No odds retrieved.")

        # Scrape results
        results = scrape_betforward_results(driver, results_url)
        if results:
            print("\nLive match results:")
            for match in results:
                status = match['status']
                print(f"{match['team1']} {match['score']['team1']} - {match['score']['team2']} {match['team2']}", end="")
                if status == "In Progress" and match['minute']:
                    print(f" ({match['minute']}')")
                elif status == "Extra Time" and match['minute']:
                    print(f" (Extra Time: {match['minute']}')")
                elif status == "Half Time":
                    print(" (Half Time)")
                elif status == "Finished":
                    print(" (Finished)")
                elif status == "Not Started":
                    print(" (Not Started)")
                else:
                    print()
                if match.get('extra_info'):
                    print(f"  Additional Info: {match['extra_info']}")
            save_to_file(results, "betforward_results.json")
        else:
            print("No results retrieved.")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    main()