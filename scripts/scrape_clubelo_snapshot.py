# scripts/scrape_clubelo_snapshot.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

WAYBACK_URL = "https://web.archive.org/web/20240515013703/https://clubelo.com/ENG"
OUTPUT_PATH = "/Users/ianmurimi/Documents/Practice/ML/EPL_Pred/epl_predictor_api/data/elo_snapshot_2024.csv"

def scrape_clubelo_snapshot():
    response = requests.get(WAYBACK_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch snapshot. Status: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"class": "clubs sortable"})

    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    rows = []

    for row in table.find_all("tr")[1:]:  # skip header
        cols = row.find_all("td")
        if len(cols) < 8:  # skip incomplete rows
            continue
        rows.append([td.get_text(strip=True) for td in cols])

    df = pd.DataFrame(rows, columns=headers)

    # Clean & retain relevant columns
    df = df.rename(columns={
        "Club": "team",
        "Elo": "elo",
        "From": "last_match_date"
    })
    df = df[["team", "elo", "last_match_date"]]
    df["elo"] = pd.to_numeric(df["elo"], errors="coerce")

    # Save to CSV
    os.makedirs("data", exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Elo ratings saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    scrape_clubelo_snapshot()