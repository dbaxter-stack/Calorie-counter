
# Round Pakenham • Calorie Calculator (Streamlit)

A branded Streamlit app for estimating daily calorie needs using the Mifflin–St Jeor equation, activity multipliers, body-type nudges, and goal intensity.

## Local Run
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy on Streamlit Community Cloud
1. Create a **public GitHub repo** and add these files.
2. In Streamlit Community Cloud, connect your GitHub and pick this repo.
3. Set the app path to `streamlit_app.py` and deploy.

### Optional
- Add `assets/9round_logo.png` to display your club's logo.
- Theme is set in `.streamlit/config.toml` (red/black/white).

## Notes
- Estimates only; not medical advice.
- Body type adjustment is a small heuristic (ecto +5%, meso 0%, endo −5%).
