import requests
import csv
from io import StringIO
from datetime import datetime
from db.db_connection import get_connection

# Constants
CSV_URL = "https://projects.fivethirtyeight.com/soccer-predictions/data/spi_global_rankings.csv"
EPL_LEAGUE = "Barclays Premier League"

def fetch_538_elo_ratings():
    response = requests.get(CSV_URL)
    if response.status_code != 200:
        raise Exception("Failed to download FiveThirtyEight SPI data")

    csv_text = response.content.decode("utf-8")
    csv_reader = csv.DictReader(StringIO(csv_text))

    today = datetime.today().date()
    elo_ratings = []

    for row in csv_reader:
        if row["league"] == EPL_LEAGUE:
            team_name = row["name"]
            rating = float(row["elo"])
            elo_ratings.append((team_name, rating, today))

    return elo_ratings

def insert_elo_ratings_to_db(ratings):
    conn = get_connection()
    cursor = conn.cursor()

    for team_name, rating, date in ratings:
        cursor.execute("""
            INSERT INTO elo_ratings (team_name, rating, rating_type, date)
            VALUES (%s, %s, 'elo', %s)
            ON CONFLICT (team_name, date, rating_type) DO UPDATE SET rating = EXCLUDED.rating
        """, (team_name, rating, date))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Inserted {len(ratings)} EPL Elo ratings from FiveThirtyEight.")

if __name__ == "__main__":
    ratings = fetch_538_elo_ratings()
    insert_elo_ratings_to_db(ratings)