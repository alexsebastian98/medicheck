# MediCheck

MediCheck is a bilingual (English/German) full-stack drug safety platform for pharmacists and general users. It analyzes 2-5 medications for pairwise interactions, overlapping side effects, contraindications, allergy risk, and duplicate therapeutic class usage.

## Stack

- Frontend: React + Vite + TypeScript + axios + react-i18next
- Backend: FastAPI + MongoDB + modular service architecture
- Data: Local curated interaction seed + OpenFDA + RxNorm fallback
- AI: OpenAI (optional) for explanation generation only

## Monorepo Structure

- `backend/` FastAPI API + interaction engines
- `frontend/` React UI with EN/DE i18n
- `docs/` architecture and API examples

## Quick Start (Local)

### 1) Backend

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

### 3) MongoDB

Run local MongoDB on `mongodb://localhost:27017` or use Docker compose:

```bash
docker compose up --build
```

## Core API Endpoints

- `POST /api/v1/check-interactions`
- `POST /api/v1/analyze-combination`
- `GET /api/v1/drug-info/{drug_name}`
- `GET /health`

## Important Clinical Safety Notes

- AI is restricted to explanation/summarization. It must not invent medical facts.
- Interaction, side-effect, and contraindication detection uses deterministic data and rules.
- This is decision support software and not a replacement for physician/pharmacist judgement.

## Next Production Steps

- Add EU/German data enrichment pipeline (ABDA/if licensed, EMA labels, BfArM integration)
- Add authentication, RBAC, and audit trails (pharmacist vs public mode)
- Add test suite, observability, and CI/CD gates
