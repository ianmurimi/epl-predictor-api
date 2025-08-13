# scripts/fetch_data.py
import os
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests

from db.db_utils import save_fixture  # ORM helper that writes a row

API_TOKEN = os.getenv("FOOTBALL_DATA_API_TOKEN")
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_TOKEN}

def _normalize_team(name: str) -> str:
    """Keep names consistent. Adjust this map as needed."""
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
        "AFC Bournemouth": "Bournemouth",
        "Bournemouth": "AFC Bournemouth",
    }
    return mapping.get(name.strip(), name.strip())

def fetch_finished_epl_matches(
    season: Optional[int] = None,
    date_from: Optional[str] = None,  # "YYYY-MM-DD"
    date_to: Optional[str] = None,    # "YYYY-MM-DD"
    retry: int = 2,
    backoff: float = 1.5,
) -> List[Dict[str, Any]]:
    """Pull finished EPL matches from Football-Data.org and return rows for save_fixture()."""
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
            raise RuntimeError(f"Football-Data API error {resp.status_code}: {resp.text[:200]}")
        time.sleep(backoff ** attempt)

    data = resp.json()
    rows: List[Dict[str, Any]] = []

    for m in data.get("matches", []):
        if m.get("status") != "FINISHED":
            continue

        score = m.get("score", {}) or {}
        full = score.get("fullTime", {}) or {}
        hg = full.get("home")
        ag = full.get("away")
        if hg is None or ag is None:
            continue

        home = _normalize_team((m.get("homeTeam", {}) or {}).get("name", ""))
        away = _normalize_team((m.get("awayTeam", {}) or {}).get("name", ""))
        if not home or not away:
            continue

        utc = m.get("utcDate")
        if not utc:
            continue
        match_date = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").date()

        result = "H" if hg > ag else "A" if ag > hg else "D"
        rows.append({
            "match_date": match_date,
            "home_team": home,
            "away_team": away,
            "home_goals": int(hg),
            "away_goals": int(ag),
            "result": result,
            "processed": False,
        })

    return rows

def insert_matches(rows: List[Dict[str, Any]]) -> int:
    """Insert via ORM helper into match_results."""
    inserted = 0
    for r in rows:
        save_fixture(r)
        inserted += 1
    print(f"✅ Inserted {inserted} finished EPL matches.")
    return inserted

if __name__ == "__main__":
    payload = fetch_finished_epl_matches()
    insert_matches(payload)