# db/db_utils.py
from datetime import date
from typing import List, Tuple, Dict, Iterable

Key = Tuple[date, str, str]

import os
import psycopg2
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import and_

from db import SessionLocal
from models import Team, Fixture

# ---- Optional: keep raw connection for legacy scripts (not used by Elo runner) ----
def get_connection():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME", "epl_prediction_db"),
        user=os.environ.get("DB_USER", "epl_user"),
        password=os.environ.get("DB_PASS", "Ianvl.2392"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
    )

# ---- Simple getters/setters used elsewhere ----
def get_elo(team_name: str) -> float:
    db = SessionLocal()
    try:
        team = db.query(Team).filter_by(name=team_name).one()
        return float(team.elo_rating or 1500.0)
    except NoResultFound:
        print(f"⚠️ Team '{team_name}' not found. Returning default Elo.")
        return 1500.0
    finally:
        db.close()

def update_elo(team_name: str, new_elo: float) -> None:
    db = SessionLocal()
    try:
        team = db.query(Team).filter_by(name=team_name).one_or_none()
        if team is None:
            team = Team(name=team_name, elo_rating=new_elo)
            db.add(team)
        else:
            team.elo_rating = new_elo
        db.commit()
        print(f"✅ Updated Elo for {team_name} to {new_elo:.2f}")
    finally:
        db.close()

def save_fixture(data: Dict) -> None:
    """
    Insert a match into match_results.
    If the unique (match_date, home_team, away_team) already exists, ignore it.
    """
    db = SessionLocal()
    try:
        fixture = Fixture(**data)
        db.add(fixture)
        db.commit()
        print(f"✅ Saved fixture: {data['home_team']} vs {data['away_team']} on {data['match_date']}")
    except IntegrityError:
        db.rollback()
        # Already exists — that's fine for idempotent ingestion
        # Optionally, update existing row's scores/result if needed.
    finally:
        db.close()

# ---- Helpers required by scripts/run_elo_updates.py ----
def get_latest_elos() -> Dict[str, float]:
    """
    Return {team_name: latest_elo} for all teams.
    """
    db = SessionLocal()
    try:
        rows = db.query(Team.name, Team.elo_rating).all()
        return {name: float(elo or 1500.0) for name, elo in rows}
    finally:
        db.close()

def get_unprocessed_fixtures() -> List[Tuple[date, str, str, int, int, str]]:
    """
    Returns list of:
      (match_date, home_team, away_team, home_goals, away_goals, result)
    """
    db = SessionLocal()
    try:
        q = (
            db.query(Fixture)
            .filter(Fixture.processed.is_(False))
            .order_by(Fixture.match_date.asc(), Fixture.home_team.asc(), Fixture.away_team.asc())
        )
        rows: List[Tuple[date, str, str, int, int, str]] = []
        for f in q.all():
            result = "H" if f.home_goals > f.away_goals else "A" if f.away_goals > f.home_goals else "D"
            rows.append((f.match_date, f.home_team, f.away_team, f.home_goals, f.away_goals, result))
        return rows
    finally:
        db.close()

def mark_fixtures_processed_by_keys(keys: Iterable[Key]) -> None:
    """
    Mark processed = TRUE using composite key (match_date, home_team, away_team).
    """
    keys = list(keys)
    if not keys:
        return
    db = SessionLocal()
    try:
        # Looping is simplest & clear; number of unprocessed items is usually small
        for mdate, home, away in keys:
            (db.query(Fixture)
               .filter(
                    Fixture.match_date == mdate,
                    Fixture.home_team == home,
                    Fixture.away_team == away,
               )
               .update({"processed": True}, synchronize_session=False))
        db.commit()
    finally:
        db.close()

def upsert_team_elo(team_name: str, new_elo: float) -> None:
    """Create/Update Team.elo_rating atomically."""
    db = SessionLocal()
    try:
        team = db.query(Team).filter_by(name=team_name).one_or_none()
        if team is None:
            team = Team(name=team_name, elo_rating=new_elo)
            db.add(team)
        else:
            team.elo_rating = new_elo
        db.commit()
    finally:
        db.close()