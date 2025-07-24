import streamlit as st
import requests

st.title("⚽ EPL Match Predictor")

home_team = st.text_input("Home Team", value="Arsenal")
away_team = st.text_input("Away Team", value="Chelsea")

if st.button("Predict"):
    url = "https://epl-predictor-api.onrender.com/predict_match"
    payload = {
        "home_team": home_team,
        "away_team": away_team
    }
    try:
        response = requests.post(url, json=payload)
        data = response.json()

        if "error" in data:
            st.error(data["error"])
        else:
            st.success(f"Prediction: {data['prediction']}")
            st.write("Probabilities:")
            st.write(data["probabilities"])
    except Exception as e:
        st.error(f"Failed to reach API: {e}")