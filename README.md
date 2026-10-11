# Rain-Fed Farming Decision Assistant — Prototype

Safe, lightweight FastAPI prototype for rain-fed farmers. It uses transparent
demo rules and does not predict yields, prescribe chemicals, or diagnose disease.

## Run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`.

Before real use, have KVK/ANGRAU experts approve every rule; add authorised
weather data, consent, encryption and secure storage for personal data.
