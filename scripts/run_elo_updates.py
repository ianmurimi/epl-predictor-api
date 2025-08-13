# run_elo_updates.py
from __future__ import annotations
import json
import math
from dataclasses import dataclass
from typing import Dict, Tuple, List
from datetime import date

import psycopg2
from psycopg2.extras import execute_values

from db import get_connection  # must return a psycopg2 connection

# ---------- Elo engine (soccer-tuned) ----------

@dataclass
class EloConfig:
    base_rating: float = 1500.0
    k: float = 24.0
    home_adv: float = 65.0  # EPL-typical home advantage in Elo points

class SoccerElo:
    def __init__(self, cfg: EloConfig = EloConfig()):
        self.cfg = cfg
        self.ratings: Dict[str, float] = {}

    def get_rating(self, team: str) -> float:
        return self.ratings.get(team, self.cfg.base_rating)

    def set_rating(self, team: str, rating: float):
        self.ratings[team] = float(rating)

    @staticmethod
    def _expected(d: float) -> float:
        # Standard Elo logistic expectation
        return 1.0 / (1.0 + 10.0 ** (-d / 400.0))

    @staticmethod
    def _g_factor(goal_diff: int, d_abs: float) -> float:
        # Goal-difference multiplier (Elo soccer convention)
        if goal_diff <= 0:
            return 1.0
        return math.log(goal_diff + 1.0) * (2.2 / ((d_abs * 0.001) + 2.2))

    def update(self, home: str, away: str, hg: int, ag: int) -> Tuple[float, float]:
        Ra, Rb = self.get_rating(home), self.get_rating(away)
        d = (Ra + self.cfg.home_adv) - Rb
        Eh = self._expected(d)
        Ea = 1.0 - Eh

        if hg > ag:
            Sh, Sa = 1.0, 0.0
        elif hg < ag:
            Sh, Sa = 0.0, 1.0
        else:
            Sh, Sa = 0.5, 0.5

        g = self._g_factor(abs(hg - ag), abs(d))
        Kh = Ka = self.cfg.k

        Rh_new = Ra + Kh * g * (Sh - Eh)
        Ra_new = Rb + Ka * g * (Sa - Ea)

        self.ratings[home] = Rh_new
        self.ratings[away] = Ra_new
        return Rh_new, Ra_new

# ---------- DB utilities ----------

def load_latest_team_ratings(conn) -> Dict[str, float]:
    """
    Load each team's latest Elo rating from team_ratings (rating_type='elo').
    Uses Postgres DISTINCT ON to get the newest per team.
    """
    q = """
        SELECT DISTINCT ON (team_name) team_name, rating_value
        FROM team_ratings
        WHERE rating_type = 'elo'
        ORDER BY team_name, rating_date DESC
    """
    ratings: Dict[str, float] = {}
    with conn.cursor() as cur:
        cur.execute(q)
        for team, value in cur.fetchall():
            ratings[team] = float(value)
    return ratings

def fetch_unprocessed_matches(conn) -> List[Tuple[date, str, str, int, int]]:
    """
    Pull finished matches that haven't been processed into Elo yet.
    """
    q = """
        SELECT match_date, home_team, away_team, home_goals, away_goals
        FROM match_results
        WHERE processed = FALSE
        ORDER BY match_date ASC, home_team ASC, away_team ASC
    """
    with conn.cursor() as cur:
        cur.execute(q)
        rows = cur.fetchall()
    return [(r[0], r[1], r[2], int(r[3]), int(r[4])) for r in rows]

def upsert_team_ratings(conn, rows: List[Tuple[str, date, str, float, str, dict]]):
    """
    Batch UPSERT into team_ratings.
    Expects rows as: (team_name, rating_date, rating_type, rating_value, source, meta_json)
    Requires a unique constraint on (team_name, rating_date, rating_type), e.g.:

      CREATE UNIQUE INDEX IF NOT EXISTS ux_team_rating_unique
      ON team_ratings(team_name, rating_date, rating_type);
    """
    if not rows:
        return
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO team_ratings
                (team_name, rating_date, rating_type, rating_value, source, meta)
            VALUES %s
            ON CONFLICT (team_name, rating_date, rating_type)
            DO UPDATE SET
                rating_value = EXCLUDED.rating_value,
                source = EXCLUDED.source,
                meta = EXCLUDED.meta
            """,
            [(t, d, rt, rv, src, json.dumps(meta) if meta is not None else None)
             for (t, d, rt, rv, src, meta) in rows]
        )

def mark_matches_processed(conn, matches: List[Tuple[date, str, str]]):
    """
    Mark processed = TRUE for each match (by date+teams).
    """
    if not matches:
        return
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            UPDATE match_results AS mr
            SET processed = TRUE
            FROM (VALUES %s) AS v(match_date, home_team, away_team)
            WHERE mr.match_date = v.match_date
              AND mr.home_team = v.home_team
              AND mr.away_team = v.away_team
            """,
            matches
        )

# ---------- Pipeline runner ----------

def main():
    cfg = EloConfig(base_rating=1500.0, k=24.0, home_adv=65.0)
    elo = SoccerElo(cfg)

    conn = get_connection()
    try:
        # 1) Seed Elo with latest stored ratings (if any)
        latest = load_latest_team_ratings(conn)
        for team, r in latest.items():
            elo.set_rating(team, r)

        # 2) Pull unprocessed matches in chronological order
        todo = fetch_unprocessed_matches(conn)
        if not todo:
            print("No unprocessed matches. Nothing to do.")
            return

        rating_rows = []  # for batch UPSERT
        processed_keys = []  # for marking processed

        for mdate, home, away, hg, ag in todo:
            # Run Elo update
            new_home, new_away = elo.update(home, away, hg, ag)

            # Queue rating upserts (rating_date = match_date)
            meta_home = {"opponent": away, "home_goals": hg, "away_goals": ag}
            meta_away = {"opponent": home, "home_goals": hg, "away_goals": ag}

            rating_rows.append((home, mdate, "elo", new_home, "internal", meta_home))
            rating_rows.append((away, mdate, "elo", new_away, "internal", meta_away))

            processed_keys.append((mdate, home, away))

        # 3) Persist in a single transaction
        with conn:
            upsert_team_ratings(conn, rating_rows)
            mark_matches_processed(conn, processed_keys)

        print(f"✅ Processed {len(todo)} matches; upserted {len(rating_rows)} team-rating rows.")

    finally:
        conn.close()

if __name__ == "__main__":
    main()