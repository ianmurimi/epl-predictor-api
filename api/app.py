from flask import Flask, request, jsonify
import numpy as np
import os
import xgboost as xgb
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Load the XGBoost model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'match_predictor_xgb.json')
model = xgb.XGBClassifier()
model.load_model(MODEL_PATH)
#model.load_model("match_predictor_xgb.json")

# Inverse label map
label_map = {0: 'Home Win', 1: 'Draw', 2: 'Away Win'}

# Initialize Flask app
app = Flask(__name__)

# Root endpoint for test

@app.route("/")
def home():
    return "⚽ EPL Predictor API is running!"
@app.route('/')
def index():
    return "Football Match Predictor API is running."

# POST endpoint for direct features
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        features = [
            data['home_form_goals'],
            data['away_form_goals'],
            data['home_win_rate'],
            data['away_win_rate'],
            data['elo_home'],
            data['elo_away']
        ]
        input_array = np.array(features).reshape(1, -1)
        prediction = model.predict(input_array)[0]
        probabilities = model.predict_proba(input_array)[0]

        return jsonify({
            'prediction': label_map[prediction],
            'probabilities': {
                'Home Win': round(float(probabilities[0]), 2),
                'Draw': round(float(probabilities[1]), 2),
                'Away Win': round(float(probabilities[2]), 2)
            }
        })

    except Exception as e:
        print(f"Error in /predict: {str(e)}", flush=True)
        return jsonify({'error': str(e)}), 400

# Function to get team stats from PostgreSQL
def get_team_stats(team_name):
    """Query team stats from the PostgreSQL DB"""
    conn = psycopg2.connect(
        dbname="epl_prediction_db",
        user="epl_user",
        password="Ianvl.2392",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT form_goals, win_rate, elo_rating FROM team_stats WHERE team_name = %s
    """, (team_name,))
    result = cur.fetchone()
    conn.close()
    if result:
        return {
            "form_goals": result[0],
            "win_rate": result[1],
            "elo_rating": result[2]
        }
    else:
        raise ValueError(f"No stats found for team: {team_name}")

# POST endpoint for team names (Arsenal vs Chelsea)
@app.route('/predict_match', methods=['POST'])
def predict_match():
    try:
        data = request.get_json()
        home_team = data['home_team']
        away_team = data['away_team']

        home_stats = get_team_stats(home_team)
        away_stats = get_team_stats(away_team)

        features = [
            home_stats['form_goals'],
            away_stats['form_goals'],
            home_stats['win_rate'],
            away_stats['win_rate'],
            home_stats['elo_rating'],
            away_stats['elo_rating']
        ]

        input_array = np.array(features).reshape(1, -1)
        prediction = model.predict(input_array)[0]
        probabilities = model.predict_proba(input_array)[0]

        return jsonify({
            'prediction': label_map[prediction],
            'probabilities': {
                'Home Win': round(float(probabilities[0]), 2),
                'Draw': round(float(probabilities[1]), 2),
                'Away Win': round(float(probabilities[2]), 2)
            }
        })

    except Exception as e:
        print(f"Error in /predict_match: {str(e)}", flush=True)
        return jsonify({'error': str(e)}), 400

# Run the app
if __name__ == '__main__':
    print("⚽ Starting Flask app...")
    port = int(os.environ.get("PORT", 5050))  # Default to 5050 for local dev
    app.run(host='0.0.0.0', port=port)