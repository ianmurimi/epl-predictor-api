# models.py
from sqlalchemy import Column, Integer, String, Float, Date, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    elo_rating = Column(Integer, nullable=False)

class Fixture(Base):
    __tablename__ = 'fixtures'
    id = Column(Integer, primary_key=True, index=True)
    match_date = Column(Date)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_form_goals = Column(Float)
    away_form_goals = Column(Float)
    home_win_rate = Column(Float)
    away_win_rate = Column(Float)
    result = Column(String)
    predicted_result = Column(String)
    prediction_probabilities = Column(JSON)