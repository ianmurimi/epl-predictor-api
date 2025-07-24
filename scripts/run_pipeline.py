from fetch_from_football_data import fetch_epl_matches, insert_matches_to_db
from update_elo_db import apply_updates_to_db

if __name__ == "__main__":
    print("📡 Fetching match data...")
    matches = fetch_epl_matches()
    insert_matches_to_db(matches)

    print("♻️ Updating Elo ratings...")
    apply_updates_to_db()

    print("✅ Full pipeline complete.")