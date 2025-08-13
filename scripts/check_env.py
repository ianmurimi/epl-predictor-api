# scripts/check_env.py
import os
import requests
from dotenv import load_dotenv
from sqlalchemy import text

# Load .env into environment
load_dotenv()

print("DB_USER:", os.getenv("DB_USER"))
print("DB_PASS:", os.getenv("DB_PASS"))
print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_PORT:", os.getenv("DB_PORT"))
print("DB_NAME:", os.getenv("DB_NAME"))
print("FOOTBALL_DATA_API_TOKEN:", "SET" if os.getenv("FOOTBALL_DATA_API_TOKEN") else "MISSING")

# --- DB connectivity check ---
try:
    from db import engine
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ DB connection OK")
except Exception as e:
    print(f"❌ DB connection failed: {e}")

# --- API connectivity check ---
api_token = os.getenv("FOOTBALL_DATA_API_TOKEN")  # <-- use the proper env var name
if api_token:
    try:
        r = requests.get(
                "https://api.football-data.org/v4/competitions/PL",
            #"https://api.football-data.org/v4/status",
            headers={"X-Auth-Token": api_token},
            timeout=10,
        )
        if r.status_code in (200, 401, 403):
            print(f"✅ Football-Data API reachable (status={r.status_code})")
        else:
            print(f"⚠️ Football-Data API unusual status: {r.status_code}")
    except Exception as e:
        print(f"❌ Football-Data API check failed: {e}")
else:
    print("⚠️ Football-Data API token not set; skipping API check")