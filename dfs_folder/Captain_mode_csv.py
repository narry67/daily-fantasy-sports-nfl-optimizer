import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import os
import shutil
import pandas as pd


def download_projections(date_str):
    try:
        input_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        print("Please enter date in YYYY-MM-DD format")
        return

    # Setup directories
    download_dir = r"C:\Downloads"
    target_dir = r"C:\Users\gohar\PycharmProjects\pythonProject7"

    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Record initial files in download directory
        initial_files = set(os.listdir(download_dir))

        # Download FanDuel projections
        print("Downloading FanDuel projections...")
        fd_url = f"https://www.dailyfantasyfuel.com/nfl/showdown-single-game-projections/fanduel/{date_str}/"
        driver.get(fd_url)

        wait = WebDriverWait(driver, 10)
        fd_csv_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(), 'CSV')]")))
        fd_csv_button.click()
        time.sleep(3)

        # Download DraftKings projections
        print("Downloading DraftKings projections...")
        dk_url = f"https://www.dailyfantasyfuel.com/nfl/showdown-single-game-projections/draftkings/{date_str}/"
        driver.get(dk_url)

        dk_csv_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(), 'CSV')]")))
        dk_csv_button.click()
        time.sleep(3)

    except Exception as e:
        print(f"An error occurred during download: {str(e)}")
        return
    finally:
        driver.quit()

    try:
        # Get list of new files (files that weren't there initially)
        final_files = set(os.listdir(download_dir))
        new_files = final_files - initial_files

        # Get full paths of new files
        new_file_paths = [os.path.join(download_dir, f) for f in new_files]

        # Sort files by modification time (newest first)
        sorted_files = sorted(new_file_paths,
                              key=lambda x: os.path.getmtime(x),
                              reverse=True)

        if len(sorted_files) >= 2:
            # First file (newest) is DraftKings, Second file is FanDuel
            dk_path = sorted_files[0]
            fd_path = sorted_files[1]

            # Move files to target directory with correct names
            shutil.move(dk_path, os.path.join(target_dir, "DFF_NFL_cheatsheet_DK.csv"))
            shutil.move(fd_path, os.path.join(target_dir, "DFF_NFL_cheatsheet_FD.csv"))
            print("Files have been successfully renamed and moved.")
        else:
            print("Could not find both downloaded files. Please check the downloads manually.")

    except Exception as e:
        print(f"An error occurred while processing files: {str(e)}")


if __name__ == "__main__":
    date_input = input("Enter date (YYYY-MM-DD format): ")
    download_projections(date_input)

# Load the CSV files
nfl_fantasy_combined = pd.read_csv('nfl_fantasy_combined.csv')
dff_nfl_cheatsheet_fd = pd.read_csv('DFF_NFL_cheatsheet_FD.csv')
dff_nfl_cheatsheet_dk = pd.read_csv('DFF_NFL_cheatsheet_DK.csv')

# Split the names into first initial and last name for nfl_fantasy_combined
nfl_fantasy_combined['first_initial'] = nfl_fantasy_combined['Player'].str[0]
nfl_fantasy_combined['last_name'] = nfl_fantasy_combined['Player'].str.split().str[-1]

# Rename columns to lowercase for all DataFrames
nfl_fantasy_combined = nfl_fantasy_combined.rename(columns=str.lower)
dff_nfl_cheatsheet_fd = dff_nfl_cheatsheet_fd.rename(columns=str.lower)
dff_nfl_cheatsheet_dk = dff_nfl_cheatsheet_dk.rename(columns=str.lower)

# Merge the DataFrames for FanDuel
fd_merged = pd.merge(nfl_fantasy_combined, dff_nfl_cheatsheet_fd,
                    on=['last_name', 'team', 'position'],
                    how='inner')
fd_output_df = fd_merged[['first_initial', 'last_name', 'team', 'position', 'points', 'salary_y']]
print(fd_output_df.head())
fd_output_df.to_csv('FD_single_game.csv', index=False)

# Merge the DataFrames for DraftKings
dk_merged = pd.merge(nfl_fantasy_combined, dff_nfl_cheatsheet_dk,
                    on=['last_name', 'team', 'position'],
                    how='inner')
dk_output_df = dk_merged[['first_initial', 'last_name', 'team', 'position', 'points', 'salary_y']]
print(dk_output_df.head())
dk_output_df.to_csv('DK_single_game.csv', index=False)