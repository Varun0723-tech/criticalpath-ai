# CriticalPath AI: Emergency Care Intelligence System

CriticalPath AI is a multi-agent emergency triage demo built with FastAPI and React. It simulates a real ER intake workflow, combines conservative clinical rules with AI-assisted reasoning when available, and returns a FHIR-style report with a polished hospital-style dashboard.

## Features

- Multi-agent workflow:
  - Intake Agent
  - Triage Agent
  - Diagnosis Agent
  - Risk Agent
  - Recommendation Agent
  - Report Agent
- Triage severity classification
- Red flag detection
- Top 3 diagnoses with confidence scores
- Weighted 0-100 risk score
- Recommendations and suggested tests
- Explainability panel
- FHIR-style JSON output
- Voice input support in compatible browsers

## Local development

### Backend

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn backend.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend runs at `http://localhost:5173` and the API runs at `http://127.0.0.1:8000`.

## Production deployment

This repo is set up to deploy as a single public website:

- React is built into static files
- FastAPI serves the built frontend
- Docker runs the full app on one public URL

### Deploy on Render

1. Push this repository to GitHub.
2. Create a new **Web Service** on Render.
3. Connect your GitHub repo.
4. Set **Language** to `Docker`.
5. Add environment variables:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL=gpt-4o-mini`
   - `ENABLE_LLM=true`
6. Deploy.

Render will build the Dockerfile and expose the app on a public `onrender.com` URL.

## Push to GitHub

Create a new empty GitHub repository first, then run:

```powershell
git branch -M main
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

Important:

- Do not commit `.env`
- Keep your real `OPENAI_API_KEY` only in local env files or your hosting provider's environment settings

## API

`POST /triage`

```json
{
  "age": 54,
  "symptoms": ["chest pain", "shortness of breath"]
}
```

Returns a FHIR-style `Bundle` with:

- patient
- observation
- triage
- condition
- riskAssessment
- carePlan
- clinicalImpression
- explanation
- agentLogs

## Notes

- This is a clinical decision-support simulation, not a medical device.
- The app includes safe rules-based fallbacks when AI reasoning is unavailable.
- In production, FastAPI serves the frontend build from `frontend/dist`.
