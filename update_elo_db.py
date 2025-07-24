import os
import psycopg2
from datetime import datetime

# --- ELO formula ---
def update_elo(rating_a, rating_b, result, k=30):
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    actual_a = {'H': 1, 'D': 0.5, 'A': 0}[result]
    new_rating_a = round(rating_a + k * (actual_a - expected_a))
    new_rating_b = round(rating_b + k * ((1 - actual_a) - (1 - expected_a)))
    return new_rating_a, new_rating_b

# --- DB credentials ---
def get_connection():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME", "epl_prediction_db"),
        user=os.environ.get("DB_USER", "epl_user"),
        password=os.environ.get("DB_PASS", "Ianvl.2392"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432")
    )

# --- Update Elo ratings for passed data or unprocessed ones ---
def apply_updates_to_db(match_data=None):
    try:
        conn = get_connection()
        cur = conn.cursor()

        if match_data is None:
            # Auto-fetch unprocessed matches
            cur.execute("""
                SELECT id, home_team, away_team, home_goals, away_goals
                FROM match_results
                WHERE processed IS FALSE OR processed IS NULL
            """)
            match_data = cur.fetchall()
        else:
            # Convert to tuple with dummy ID for compatibility
            match_data = [(None, *m) for m in match_data]

        for match in match_data:
            match_id, home, away, home_goals, away_goals = match
            result = 'H' if home_goals > away_goals else 'A' if away_goals > home_goals else 'D'

            # Elo lookup
            cur.execute("SELECT elo_rating FROM elo_ratings WHERE team_name = %s", (home,))
            home_elo = cur.fetchone()
            cur.execute("SELECT elo_rating FROM elo_ratings WHERE team_name = %s", (away,))
            away_elo = cur.fetchone()

            if not home_elo or not away_elo:
                print(f"❌ Elo rating missing for: {home if not home_elo else away}")
                continue

            new_home, new_away = update_elo(home_elo[0], away_elo[0], result)

            # Update ratings
            cur.execute("UPDATE elo_ratings SET elo_rating = %s, last_updated = %s WHERE team_name = %s",
                        (new_home, datetime.now(), home))
            cur.execute("UPDATE elo_ratings SET elo_rating = %s, last_updated = %s WHERE team_name = %s",
                        (new_away, datetime.now(), away))

            # Insert match if new
            if match_id is None:
                cur.execute("""
                    INSERT INTO match_results (match_date, home_team, away_team, home_goals, away_goals, result, processed)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                """, (datetime.now().date(), home, away, home_goals, away_goals, result))
            else:
                cur.execute("UPDATE match_results SET processed = TRUE WHERE id = %s", (match_id,))

        conn.commit()
        print(f"✅ Processed {len(match_data)} match(es).")
    except Exception as e:
        print(f"❌ Error during Elo update: {e}")
    finally:
        if conn:
            conn.close()

# --- CLI entry point ---
if __name__ == "__main__":
    apply_updates_to_db()