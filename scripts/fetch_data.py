import os
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import requests

from db.db_utils import save_fixture

API_TOKEN = os.getenv("FOOTBALL_DATA_API_TOKEN")
#API_URL = "https://api.football-data.org/v4/competitions/PL/matches?season=2023"
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_TOKEN}

# Type: (date, home, away, hg, ag, result)
MatchRow = Tuple[datetime, str, str, int, int, str]

def _normalize_team(name: str) -> str:
    """Keep names consistent. we can adjust this map if needed."""
    name = name.replace("FC ", "").replace("AFC ", "").strip()
    mapping = {
        "Manchester United FC": "Manchester United",
        "Manchester City FC": "Manchester City",
        "Tottenham Hotspur FC": "Tottenham Hotspur",
        "Brighton & Hove Albion FC": "Brighton",
        "Nottingham Forest FC": "Nottingham Forest",
        "Wolverhampton Wanderers FC": "Wolves",
        "Newcastle United FC": "Newcastle United",
        "West Ham United FC": "West Ham",
        "Brentford FC": "Brentford",
        "Leicester City FC": "Leicester City",
        "Ipswich Town FC": "Ipswich Town",
        "Southampton FC": "Southampton",
        "Chelsea FC": "Chelsea",
        "Arsenal FC": "Arsenal",
        "Liverpool FC": "Liverpool",
        "Everton FC": "Everton",
        "Aston Villa FC": "Aston Villa",
        "Bournemouth": "AFC Bournemouth",
        "AFC Bournemouth": "Bournemouth",
        # add more as they appear
    }
    return mapping.get(name, name)

def fetch_finished_epl_matches(
    season: Optional[int] = None,
    date_from: Optional[str] = None,  # "YYYY-MM-DD"
    date_to: Optional[str] = None,    # "YYYY-MM-DD"
    retry: int = 2,
    backoff: float = 1.5,
) -> List[MatchRow]:
    """
    Pull finished EPL matches from Football-Data.org.

    Args:
        season: e.g., 2024 for 2024/25 season. If None, API returns current.
        date_from/date_to: optional bounding; if provided, API filters by UTC date.
    """
    if not API_TOKEN:
        raise RuntimeError("FOOTBALL_DATA_API_TOKEN is not set in your environment.")

    url = f"{BASE_URL}/competitions/PL/matches"
    params = {"status": "FINISHED"}
    if season is not None:
        params["season"] = season
    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to

    for attempt in range(retry + 1):
        resp = requests.get(url, headers=HEADERS, params=params, timeout=25)
        if resp.status_code == 200:
            break
        if attempt == retry:
            raise RuntimeError(f"Football-Data API error {resp.status_code}: {resp.text}")
        time.sleep(backoff ** attempt)

    data = resp.json()
    raw_matches = data.get("matches", [])
    rows: List[MatchRow] = []

    for m in raw_matches:
        # Defensive parsing
        if m.get("status") != "FINISHED":
            continue

        score = m.get("score", {})
        full = score.get("fullTime", {}) or {}
        hg = full.get("home")
        ag = full.get("away")
        if hg is None or ag is None:
            # Sometimes missing; skip or fall back to halfTime/regularTime if you want
            continue

        home = _normalize_team(m.get("homeTeam", {}).get("name", "").strip())
        away = _normalize_team(m.get("awayTeam", {}).get("name", "").strip())
        if not home or not away:
            continue

        # utcDate like "2024-08-13T19:00:00Z"
        utc = m.get("utcDate")
        if not utc:
            continue
        match_date = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").date()

        result = "H" if hg > ag else "A" if ag > hg else "D"
        rows.append((match_date, home, away, int(hg), int(ag), result))

    return rows

def insert_matches_to_db(matches: List[MatchRow]) -> int:
    """
    Batch insert with ON CONFLICT do-nothing.
    Requires a UNIQUE index on (match_date, home_team, away_team), e.g.:

        CREATE UNIQUE INDEX IF NOT EXISTS ux_match_unique
          ON match_results(match_date, home_team, away_team);
    """
    if not matches:
        print("No matches to insert.")
        return 0

    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO match_results
                    (match_date, home_team, away_team, home_goals, away_goals, result, processed)
                VALUES %s
                ON CONFLICT (match_date, home_team, away_team) DO NOTHING
                """,
                matches,
            )
        print(f"✅ Inserted {len(matches)} finished EPL matches.")
        return len(matches)
    finally:
        conn.close()

if __name__ == "__main__":
    rows = fetch_finished_epl_matches(season=None)
    insert_matches_to_db(rows)
