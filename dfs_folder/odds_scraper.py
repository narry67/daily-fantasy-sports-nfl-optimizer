from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import pandas as pd



def normalize_team_name(team):
    """Standardize team abbreviations"""
    team_mappings = {
        'JAC': 'JAX',
        'JAX': 'JAX',
        'Jacksonville': 'JAX',
        'SF': 'SF',
        'San Francisco': 'SF',
        # Add more mappings as needed
    }
    team = team.upper().strip()
    return team_mappings.get(team, team)
def extract_team_position(text):
    """Extract team and position from format like 'CLE - RB'"""
    if not text:
        return None, None
    parts = text.split(' - ')
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, None
def scrape_betting_pros(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)

    try:
        print("Accessing website...")
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "odds-offer"))
        )

        print("Starting to scroll and collect data...")

        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 30

        while scroll_attempts < max_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
            print(f"Scrolling... attempt {scroll_attempts}")

        print("Collecting player data...")

        odds_data = []
        player_containers = driver.find_elements(By.CLASS_NAME, "odds-offer")

        for container in player_containers:
            try:
                # Get player name
                player_name = container.find_element(By.CLASS_NAME, "odds-player__heading").text

                team_pos_element = container.find_element(By.CLASS_NAME, "odds-player__subheading")
                team, position = extract_team_position(team_pos_element.text)

                # Get line value and strip the 'O ' prefix
                line_element = container.find_element(By.CSS_SELECTOR, "span.odds-cell__line")
                line_value = line_element.text.replace('O ', '')

                # Create a record with just player name and numeric line value
                player_data = {
                    'Player': player_name,
                    'Team': normalize_team_name(team),
                    'Position': position,
                    'Points': float(line_value)  # Convert to numeric value
                }

                odds_data.append(player_data)
                print(f"Collected data for {player_name}: {line_value}")

            except Exception as e:
                print(f"Error processing a player container: {e}")
                continue

        return odds_data

    finally:
        driver.quit()


def print_odds_data(odds_data):
    for player in odds_data:
        print(f"{player['Player']}: {player['Points']}")


if __name__ == "__main__":
    url = "https://www.bettingpros.com/nfl/odds/player-props/weekly-fantasy-points/"
    try:
        print("Starting scraper...")
        results = scrape_betting_pros(url)

        print(f"\nFound data for {len(results)} players:")
        print_odds_data(results)

        # Save to CSV
        df = pd.DataFrame(results)
        filename = 'nfl_fantasy_points.csv'
        df.to_csv(filename, index=False)
        print(f"\nData saved to '{filename}'")

    except Exception as e:
        print(f"An error occurred: {e}")