# db_utils_elo_debug.py
import json
from typing import Iterable, Mapping, Tuple
import psycopg2
from psycopg2.extras import execute_values

UPSERT_SQL_RETURNING = """
INSERT INTO elo_ratings
    (team_name, rating_date, rating_value, rating_type, source, meta)
VALUES %s
ON CONFLICT (team_name, rating_date, rating_type, source)
DO UPDATE SET
    rating_value = EXCLUDED.rating_value,
    meta         = COALESCE(elo_ratings.meta, '{}'::jsonb) || COALESCE(EXCLUDED.meta, '{}'::jsonb),
    updated_at   = now()
RETURNING 1;
"""

def _to_row(rec: Mapping) -> Tuple:
    return (
        rec["team_name"],
        rec["rating_date"],        # date or 'YYYY-MM-DD'
        float(rec["rating_value"]),
        rec.get("rating_type", "clubelo"),
        rec.get("source", "ClubElo"),
        json.dumps(rec.get("meta", {})),
    )

def upsert_elo_batch_debug(conn_str: str, records: Iterable[Mapping], page_size: int = 1000) -> int:
    rows = [_to_row(r) for r in records]
    if not rows:
        print("[elo] No records to upsert.")
        return 0
    try:
        with psycopg2.connect(conn_str) as conn:
            with conn.cursor() as cur:
                # Print where we connected
                cur.execute("SELECT current_database(), current_user;")
                db, user = cur.fetchone()
                print(f"[elo] Connected to DB={db} as {user}. Attempting {len(rows)} upserts...")

                # Show a tiny sample of teams
                sample = [r[0] for r in rows[:5]]
                print(f"[elo] Sample teams: {sample}{'...' if len(rows) > 5 else ''}")

                execute_values(cur, UPSERT_SQL_RETURNING, rows, page_size=page_size)
                applied = cur.rowcount  # number of RETURNING rows for this statement
                print(f"[elo] Applied rows (inserted+updated): {applied}")
                return applied
    except Exception as e:
        print("[elo] ERROR during upsert:", repr(e))
        return 0