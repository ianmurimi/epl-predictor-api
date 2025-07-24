# db_utils.py
from db import SessionLocal
from models import Team, Fixture
from sqlalchemy.exc import NoResultFound

def get_elo(team_name):
    db = SessionLocal()
    try:
        team = db.query(Team).filter_by(name=team_name).one()
        return team.elo_rating
    except NoResultFound:
        print(f"⚠️ Team '{team_name}' not found. Returning default Elo.")
        return 1500  # default Elo
    finally:
        db.close()

def update_elo(team_name, new_elo):
    db = SessionLocal()
    try:
        team = db.query(Team).filter_by(name=team_name).one()
        team.elo_rating = new_elo
        db.commit()
        print(f"✅ Updated Elo for {team_name} to {new_elo}")
    except NoResultFound:
        print(f"⚠️ Team '{team_name}' not found. Creating new team.")
        new_team = Team(name=team_name, elo_rating=new_elo)
        db.add(new_team)
        db.commit()
    finally:
        db.close()

def save_fixture(data):
    db = SessionLocal()
    try:
        fixture = Fixture(**data)
        db.add(fixture)
        db.commit()
        print(f"✅ Saved fixture: {data['home_team']} vs {data['away_team']}")
    finally:
        db.close()