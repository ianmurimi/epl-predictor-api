# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env if available
load_dotenv()

# Get database credentials from env or use defaults
DB_USER = os.getenv("DB_USER", "epl_user")
DB_PASSWORD = os.getenv("DB_PASS", "Ianvl.2392")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "epl_prediction_db")

# Construct DB URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Add this to db.py
def get_connection():
    return engine.raw_connection()