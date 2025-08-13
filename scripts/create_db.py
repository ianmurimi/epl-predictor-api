# scripts/create_db.py
from db import engine
from models import Base

def main():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables ensured.")

if __name__ == "__main__":
    main()