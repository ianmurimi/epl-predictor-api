# test_db_utils.py
from db_utils import get_elo, update_elo, save_fixture

# Check current Elo rating
print("Arsenal Elo:", get_elo("Arsenal"))

# Update Elo
update_elo("Arsenal", 1530)

# Save a sample fixture and prediction
save_fixture({
    'match_date': '2025-08-01',
    'home_team': 'Arsenal',
    'away_team': 'Chelsea',
    'home_form_goals': 1.5,
    'away_form_goals': 1.2,
    'home_win_rate': 0.6,
    'away_win_rate': 0.4,
    'result': None,
    'predicted_result': 'Home Win',
    'prediction_probabilities': {'Home Win': 0.65, 'Draw': 0.2, 'Away Win': 0.15}
})