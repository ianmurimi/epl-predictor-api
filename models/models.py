# models/models.py
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean, UniqueConstraint, func
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"  # if your table is named differently, change this
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, index=True, nullable=False)
    elo_rating = Column(Float, nullable=False, default=1500.0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Fixture(Base):
    __tablename__ = "match_results"  # aligns with your inserts
    id = Column(Integer, primary_key=True)
    match_date = Column(Date, nullable=False, index=True)
    home_team = Column(String(128), nullable=False, index=True)
    away_team = Column(String(128), nullable=False, index=True)
    home_goals = Column(Integer, nullable=False)
    away_goals = Column(Integer, nullable=False)
    result = Column(String(1), nullable=False)  # 'H'/'D'/'A'
    processed = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("match_date", "home_team", "away_team",
                         name="ux_match_unique"),
    )