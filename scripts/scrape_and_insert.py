# scripts/scrape_and_insert.py

from scripts.elo_scraping import fetch_latest_results
from scripts.fetch_data import insert_matches_to_db

if __name__ == "__main__":
    matches = fetch_latest_results()

    # Restructure to include dummy match_date and result if needed
    formatted_matches = []
    from datetime import datetime
    for home, away, home_goals, away_goals in matches:
        result = 'H' if home_goals > away_goals else 'A' if away_goals > home_goals else 'D'
        formatted_matches.append((datetime.now().date(), home, away, home_goals, away_goals, result))

    insert_matches_to_db(formatted_matches)