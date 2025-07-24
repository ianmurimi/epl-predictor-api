import requests
from bs4 import BeautifulSoup

def fetch_latest_results():
    url = "https://www.espn.com/soccer/scoreboard/_/league/eng.1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Example logic: You'll need to adjust based on structure
    results = []
    for match in soup.select('.scoreboard'):
        home = match.select_one('.team-home .name').text
        away = match.select_one('.team-away .name').text
        score = match.select_one('.score').text  # e.g., "2 - 1"
        home_goals, away_goals = map(int, score.split('-'))
        results.append((home, away, home_goals, away_goals))
    return results