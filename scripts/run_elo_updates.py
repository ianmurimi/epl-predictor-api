# scripts/run_elo_updates.py
from dataclasses import dataclass
import math
from typing import Dict

from db.db_utils import (
    get_latest_elos,
    get_unprocessed_fixtures,
    mark_fixtures_processed,
    upsert_team_elo,
)

@dataclass
class EloConfig:
    base_rating: float = 1500.0
    k: float = 24.0
    home_adv: float = 65.0

class SoccerElo:
    def __init__(self, cfg: EloConfig):
        self.cfg = cfg
        self.ratings: Dict[str, float] = {}

    def get(self, team: str) -> float:
        return self.ratings.get(team, self.cfg.base_rating)

    @staticmethod
    def expected(d: float) -> float:
        return 1.0 / (1.0 + 10 ** (-d / 400.0))

    @staticmethod
    def g_factor(goal_diff: int, d_abs: float) -> float:
        if goal_diff <= 0:
            return 1.0
        return math.log(goal_diff + 1.0) * (2.2 / ((d_abs * 0.001) + 2.2))

    def update_pair(self, home: str, away: str, hg: int, ag: int):
        Ra, Rb = self.get(home), self.get(away)
        d = (Ra + self.cfg.home_adv) - Rb
        Eh = self.expected(d); Ea = 1 - Eh
        Sh, Sa = (1.0, 0.0) if hg > ag else (0.0, 1.0) if ag > hg else (0.5, 0.5)
        g = self.g_factor(abs(hg - ag), abs(d))
        Rh_new = Ra + self.cfg.k * g * (Sh - Eh)
        Rb_new = Rb + self.cfg.k * g * (Sa - Ea)
        self.ratings[home] = Rh_new
        self.ratings[away] = Rb_new
        return Rh_new, Rb_new

def main():
    cfg = EloConfig()
    elo = SoccerElo(cfg)

    # 1) seed with current elos
    latest = get_latest_elos()  # {team: rating}
    elo.ratings.update(latest)

    # 2) get unprocessed fixtures
    fixtures = get_unprocessed_fixtures()  # [(date, home, away, hg, ag, result, id), ...]
    if not fixtures:
        print("No unprocessed fixtures.")
        return

    processed_ids = []
    for mdate, home, away, hg, ag, result, fid in fixtures:
        new_home, new_away = elo.update_pair(home, away, hg, ag)
        upsert_team_elo(home, new_home)
        upsert_team_elo(away, new_away)
        processed_ids.append(fid)

    mark_fixtures_processed(processed_ids)
    print(f"✅ Processed {len(processed_ids)} fixtures and updated team Elo.")

if __name__ == "__main__":
    main()