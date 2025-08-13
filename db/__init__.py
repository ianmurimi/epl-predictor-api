# db/__init__.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DB_URL = os.getenv(
    "DB_URL",
    "postgresql+psycopg2://epl_user:Ianvl.2392@localhost:5432/epl_prediction_db"
)
engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["SessionLocal", "engine"]