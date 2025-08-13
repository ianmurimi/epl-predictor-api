# scripts/run_pipeline.py
"""
End-to-end pipeline:
1) Fetch finished EPL matches and insert into DB.
2) Update Elo for all unprocessed fixtures.

Run from project root:
  python -m scripts.run_pipeline
or:
  python scripts/run_pipeline.py
"""

def _import_fetch():
    try:
        # when run as module: python -m scripts.run_pipeline
        from .fetch_data import fetch_finished_epl_matches, insert_matches
    except Exception:
        # when run as script: python scripts/run_pipeline.py
        from fetch_data import fetch_finished_epl_matches, insert_matches
    return fetch_finished_epl_matches, insert_matches

def _import_elo_runner():
    try:
        from .run_elo_updates import main as run_elo_main
    except Exception:
        from run_elo_updates import main as run_elo_main
    return run_elo_main

def main():
    fetch_finished_epl_matches, insert_matches = _import_fetch()
    run_elo_main = _import_elo_runner()

    print("📡 Fetching finished EPL matches…")
    rows = fetch_finished_epl_matches()
    insert_matches(rows)

    print("♻️ Updating Elo ratings…")
    run_elo_main()

    print("✅ Full pipeline complete.")

if __name__ == "__main__":
    main()