from flask import Flask, request, jsonify
import joblib
import numpy as np
import os
import xgboost as xgb

# Load trained model
model = xgb.XGBClassifier()
model.load_model("match_predictor_xgb.json")

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
        print(f"Received data: {data}", flush=True)

        features = [
            data['home_form_goals'],
            data['away_form_goals'],
            data['home_win_rate'],
            data['away_win_rate'],
            data['elo_home'],
            data['elo_away']
        ]

        input_array = np.array(features).reshape(1, -1)
        print(f"Input array: {input_array}", flush=True)

        prediction = model.predict(input_array)[0]
        probabilities = model.predict_proba(input_array)[0]

        print(f"Prediction: {prediction}, Probabilities: {probabilities}", flush=True)

        return jsonify({
            'prediction': label_map[prediction],
            'probabilities': {
                'Home Win': round(float(probabilities[0]), 2),
                'Draw': round(float(probabilities[1]), 2),
                'Away Win': round(float(probabilities[2]), 2)
            }
        })

    except Exception as e:
        print(f"Error during prediction: {str(e)}", flush=True)
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    print("⚽ Starting Flask app...")
    port = int(os.environ.get("PORT", 5050))  # For Render
    app.run(host='0.0.0.0', port=port)