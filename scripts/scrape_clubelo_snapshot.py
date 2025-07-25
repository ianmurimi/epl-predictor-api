# scripts/scrape_clubelo_snapshot.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

WAYBACK_URL = "https://web.archive.org/web/20240515013703/https://clubelo.com/ENG"
OUTPUT_PATH = "data/elo_snapshot_2024.csv"


def scrape_clubelo_snapshot():
    response = requests.get(WAYBACK_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch snapshot. Status: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Try finding all tables
    tables = soup.find_all("table")
    print(f"✅ Found {len(tables)} tables in snapshot")

    if not tables:
        raise Exception("❌ No tables found in snapshot.")

    # Try the second table — usually the Elo table on ClubElo
    table = tables[1] if len(tables) > 1 else tables[0]

    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    rows = []

    for row in table.find_all("tr")[1:]:  # skip header
        cols = row.find_all("td")
        if len(cols) < 8:
            continue
        rows.append([td.get_text(strip=True) for td in cols])

    df = pd.DataFrame(rows, columns=headers)

    df = df.rename(columns={
        "Club": "team",
        "Elo": "elo",
        "From": "last_match_date"
    })
    df = df[["team", "elo", "last_match_date"]]
    df["elo"] = pd.to_numeric(df["elo"], errors="coerce")

    os.makedirs("data", exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Elo ratings saved to {OUTPUT_PATH}")