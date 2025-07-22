from flask import Flask, request, jsonify
import joblib
import numpy as np

# Load trained model
model = joblib.load('/Users/ianmurimi/Documents/Practice/ML/EPL_Pred/match_predictor_xgb.pkl')

# Flask app
app = Flask(__name__)

# Inverse label map
label_map = {0: 'Home Win', 1: 'Draw', 2: 'Away Win'}


@app.route('/')
def index():
    return "Football Match Predictor API is running."


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()

        # Extract features in the correct order
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
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    print("⚽ Starting Flask app...")
    app.run(host='127.0.0.1', port=5000, debug=True)