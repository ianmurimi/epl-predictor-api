import requests
from bs4 import BeautifulSoup

def fetch_elo_ratings():
    url = "https://clubelo.com/ENG"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", {"class": "sortable"})
    ratings = []

    if not table:
        print("❌ Could not find Elo table on page.")
        return ratings

    for row in table.select("tbody tr"):
        try:
            columns = row.find_all("td")
            team_name = columns[1].text.strip()
            elo = int(columns[4].text.strip())
            ratings.append((team_name, elo))
        except Exception as e:
            continue  # Skip rows that don't match

    return ratings