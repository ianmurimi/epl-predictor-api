# ⚽ EPL Predictor API

**Author:** Ian Murimi  
**Stack:** Python · Flask · PostgreSQL · XGBoost · Elo Ratings  
**Project Type:** End-to-End Machine Learning System  
**Focus:** Sports Analytics, Predictive Modeling, Multi-Agent Dynamics

---

## 🔍 Overview

The EPL Predictor API is a fully functional RESTful service for forecasting outcomes of English Premier League matches. It leverages historical match data, real-time Elo ratings, and engineered features to train an **XGBoost classifier** that predicts **win**, **draw**, or **loss** outcomes for upcoming fixtures.

Though rooted in football analytics, this project generalizes to any scenario involving competitive agents and dynamic rating systems. It reflects principles of **multi-agent learning**, **time-series forecasting**, and **model deployment at scale**.

---

## 🚀 Features

- 📈 **Elo Rating Engine** – Continuously updates team strength based on past performance.
- 🧠 **XGBoost Classifier** – Predicts outcome probabilities using engineered features.
- 🧪 **Feature Engineering Scripts** – Extracts insights from match history, team stats, and form.
- 🌐 **REST API** – Easily query match predictions with team names as inputs.
- 🗃️ **PostgreSQL Integration** – Stores fixtures, results, and rating history.
- 🔁 **CI/CD Ready** – Includes GitHub Actions for testing and deployment.

---

## 🗂️ Repository Structure
epl-predictor-api/
├── api/           # Backend API logic (Flask)
├── db/            # SQL schema and DB utilities
├── models/        # Trained model and Elo scripts
├── scripts/       # Feature engineering and Elo updates
├── tests/         # Unit & integration tests
├── .github/       # CI workflows
├── render.yaml    # Deployment config (e.g. Render.com)
├── requirements.txt
├── runtime.txt
└── README.md

---

## 🔧 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL (local or remote)
- Recommended: virtual environment (`venv` or `poetry`)

### Installation & Run

```bash
# Clone the repo
git clone https://github.com/ianmurimi/epl-predictor-api.git
cd epl-predictor-api

# Install dependencies
pip install -r requirements.txt

# Set up your database (PostgreSQL)
# Add DB credentials in a .env file or directly in db_utils.py

# Run the API
python api/app.py

Sample API Request
curl -X POST http://localhost:8000/predict_match \
     -H "Content-Type: application/json" \
     -d '{"home_team": "Arsenal", "away_team": "Chelsea"}'

Returns:
{
  "prediction": "Home Win",
  "probabilities": {
    "Home Win": 0.52,
    "Draw": 0.27,
    "Away Win": 0.21
  }
}
