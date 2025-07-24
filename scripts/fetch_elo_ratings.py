from scripts.elo_scraping import fetch_elo_ratings

if __name__ == "__main__":
    ratings = fetch_elo_ratings()
    for team, elo in ratings:
        print(f"{team}: {elo}")