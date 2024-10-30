from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re


def normalize_player_name(name):
    """Convert full names to First Initial. Last Name format, with specific conversions"""

    # Explicit conversions based on provided mappings
    name_conversion_lookup = {
        "Amon-Ra St. Brown": "A. St. Brown",
        "A.J. Brown": "A.J. Brown",
        "Bo Nix": "Bo Nix",
        "Christian Kirk": "C. Kirk",
        "C.J. Stroud": "C.J. Stroud",
        "DJ Moore": "DJ Moore",
        "Evan Engram": "E. Engram",
        "Gardner Minshew II": "G. Minshew II",
        "J.K. Dobbins": "J.K. Dobbins",
        "Marvin Harrison Jr.": "M. Harrison Jr.",
        "Patrick Mahomes II": "P. Mahomes II",
        "Ray-Ray McCloud III": "R. McCloud III",
        "Trevor Lawrence": "T. Lawrence",
        "T.J. Hockenson": "T.J. Hockenson",
        "Ty Chandler": "Ty Chandler",
        "Michael Pittman Jr.": "M. Pittman Jr.",
        "Kenneth Walker III": "K. Walker III",
        "Brian Thomas Jr.": "B. Thomas Jr.",
        "Brian Robinson Jr.": "B. Robinson Jr.",
        "Deebo Samuel Sr.": "D. Samuel Sr.",
        "Calvin Austin III": "C. Austin III",
        "Velus Jones Jr.": "V. Jones Jr.",
        "John Stephens Jr.": "J. Stephens Jr.",
        "Patrick Taylor Jr.": "P. Taylor Jr.",
        "Tyrone Tracy Jr.": "T. Tracy Jr.",
        "Erick All Jr.": "E. All Jr.",
        "Mecole Hardman Jr.": "M. Hardman Jr.",
        "DJ Turner": "DJ Turner",
        "Mo Alie-Cox": "Mo Alie-Cox",
        "AJ Barner": "AJ Barner",
        "Odell Beckham Jr.": "O. Beckham Jr.",
        "DJ Chark Jr.": "DJ Chark Jr.",
        "Travis Etienne Jr.": "T. Etienne Jr.",
        "Jody Fortson Jr.": "J. Fortson Jr.",
        "Troy Hairston II": "T. Hairston II",
        "C.J. Ham": "C.J. Ham",
        "Tyler Johnson": "Ty Johnson",
        "Ko Kieft": "Ko Kieft",
        "Bo Melton": "Bo Melton",
        "DK Metcalf": "DK Metcalf",
        "John Metchie III": "J. Metchie III",
        "Marvin Mims Jr.": "M. Mims Jr.",
        "K.J. Osborn": "K.J. Osborn",
        "Allen Robinson II": "A. Robinson II",
        "Laviska Shenault Jr.": "L. Shenault Jr.",
        "John Samuel Shenker": "J. Samuel Shenker",
        "Trent Sherfield Sr.": "T. Sherfield Sr.",
        "Steven Sims Jr.": "S. Sims Jr.",
        "Pierre Strong Jr.": "P. Strong Jr.",
        "Jeff Wilson Jr.": "J. Wilson Jr.",
        "Cedrick Wilson Jr.": "C. Wilson Jr."
    }

    # Check if the name is in the lookup dictionary
    if name in name_conversion_lookup:
        return name_conversion_lookup[name]

    # Default conversion to "First Initial. Last Name" format
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name


def extract_team_from_small(small_text):
    """Extract team from format like '(SF - WR)'"""
    match = re.match(r'\((.*?)\s*-\s*.*?\)', small_text)
    if match:
        return match.group(1).strip()
    return None

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
def scrape_salaries(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    salary_data = []

    try:
        print("Accessing DraftKings salary page...")
        driver.get(url)

        # Wait for table to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "data-table"))
        )
        driver.execute_script("document.querySelectorAll('.hidden').forEach(el => el.classList.remove('hidden'))")

        # Get all rows from the table
        rows = driver.find_elements(By.CSS_SELECTOR, "#data-table tbody tr")
        for row in rows:
            try:
                # Get position from class attribute
                position = re.search(r'(QB|RB|WR|TE|DST)', row.get_attribute('class')).group(1)
                print(position)
                # Only process if it's one of our desired positions
                if position in ['QB', 'RB', 'WR', 'TE']:
                    # Get player name
                    name_element = row.find_element(By.CSS_SELECTOR, "a.fp-player-link")
                    player_name = normalize_player_name(name_element.get_attribute("fp-player-name"))

                    # Get team from small text
                    #name_cell = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)")
                    #small_element = name_cell.find_element(By.CSS_SELECTOR, "small")
                    #small_element = row.find_element(By.TAG_NAME, "small")
                    team_position_text = row.find_element(By.CSS_SELECTOR, "td > small").text
                    team = extract_team_from_small(team_position_text)
                    team = normalize_team_name(team)

                    # Get current salary
                    salary_cell = row.find_element(By.CSS_SELECTOR, "td.salary")
                    salary = float(salary_cell.get_attribute("data-salary"))

                    player_data = {
                        'Player': player_name,
                        "Team": team,
                        'Position': position,
                        'Salary': salary
                    }

                    salary_data.append(player_data)
                    print(f"Collected data for {player_name} ({position}): ${salary:,.0f}")

            except Exception as e:
                print(f"Error processing a player row: {e}")
                continue

        return salary_data

    finally:
        driver.quit()


def combine_data(salary_data, points_data):
    # Convert lists of dictionaries to DataFrames
    salary_df = pd.DataFrame(salary_data)
    points_df = pd.DataFrame(points_data)

    # Merge the dataframes on Player name AND team
    combined_df = pd.merge(salary_df, points_df,
                           on=['Player', 'Team', 'Position'],
                           how='outer',
                           indicator=True)

    # Fill any missing values
    combined_df['Points'] = combined_df['Points'].fillna(0)
    combined_df['Salary'] = combined_df['Salary'].fillna(0)
    combined_df['Position'] = combined_df['Position'].fillna('Unknown')
    combined_df['Team'] = combined_df['Team'].fillna('Unknown')

    # Calculate points per $1000
    combined_df['Points_Per_1000'] = (combined_df['Points'] * 1000) / combined_df['Salary'].replace(0, float('nan'))

    # Sort by Points_Per_1000 descending
    combined_df = combined_df.sort_values('Points_Per_1000', ascending=False)

    return combined_df


if __name__ == "__main__":
    # First scrape fantasy points
    points_url = "https://www.bettingpros.com/nfl/odds/player-props/weekly-fantasy-points/"
    salary_url = "https://www.fantasypros.com/daily-fantasy/nfl/draftkings-salary-changes.php"

    try:
        # Get fantasy points data
        print("Starting fantasy points scraper...")
        from odds_scraper import scrape_betting_pros  # Import the previous script

        points_data = scrape_betting_pros(points_url)

        # Get salary data
        print("\nStarting salary scraper...")
        salary_data = scrape_salaries(salary_url)

        # Combine the data
        print("\nCombining data...")
        combined_df = combine_data(salary_data, points_data)

        # Save to CSV
        filename = 'nfl_fantasy_combined.csv'
        combined_df.to_csv(filename, index=False)
        print(f"\nData saved to '{filename}'")

        # Print some summary statistics
        print("\nTop 10 Value Players (Points per $1000):")
        print(combined_df.head(10)[['Player', 'Team','Position', 'Salary', 'Points', 'Points_Per_1000']])

        print(salary_data)
        print(points_data)
    except Exception as e:
        print(f"An error occurred: {e}")