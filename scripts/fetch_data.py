from db import get_connection
import requests
from datetime import datetime
import os

API_TOKEN = os.getenv("b30c72d9184e4fc8b3d6d3600a16df42")
#API_URL = "https://api.football-data.org/v4/competitions/PL/matches?season=2023"
API_URL = "https://api.football-data.org/v4/matches"
HEADERS = {"X-Auth-Token": API_TOKEN}


def fetch_epl_matches():
    response = requests.get(API_URL, headers=HEADERS)
    data = response.json()
    print(data)
    matches = []

    for match in data["matches"]:
        if match["status"] == "FINISHED":
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]
            home_goals = match["score"]["fullTime"]["home"]
            away_goals = match["score"]["fullTime"]["away"]
            match_date = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ").date()
            result = 'H' if home_goals > away_goals else 'A' if away_goals > home_goals else 'D'
            matches.append((match_date, home, away, home_goals, away_goals, result))

    return matches


def insert_matches_to_db(matches):
    conn = get_connection()
    cur = conn.cursor()

    for match in matches:
        cur.execute("""
                    INSERT INTO match_results (match_date, home_team, away_team,
                                               home_goals, away_goals, result, processed)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE) ON CONFLICT DO NOTHING;
                    """, match)

    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(matches)} EPL matches.")


if __name__ == "__main__":
    matches = fetch_epl_matches()
    insert_matches_to_db(matches)
