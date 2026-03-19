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

## Recent Upgrades (March 2026)

The system was upgraded from a pure pairwise checker to a lightweight clinically aware analyzer, with minimal architecture changes.

### 1) Clinical Interaction Logic

- Class-based rules and hard safety overrides were added to catch high-value risks even when pairwise seed data is missing.
- Secondary pathway detection was added for CYP3A4-related interactions (including shared substrate competition for high-risk substrate pairs).
- Priority selection now highlights one `primary_interaction` and keeps remaining findings as `secondary_interactions`.

Implemented in:

- `backend/app/services/interaction_engine.py`
- `backend/app/services/severity_engine.py`
- `backend/app/api/routes.py`

### 2) Protective Modifiers and Severity Adjustment

- Protective drug logic (PPI examples: omeprazole, pantoprazole) reduces GI-related risk impact.
- Overall severity remains conservative (`HIGH` is never down-graded if a true high-risk interaction exists).

Implemented in:

- `backend/app/services/interaction_engine.py`
- `backend/app/services/severity_engine.py`

### 3) Clinical Signal-to-Noise Improvements

- Added risk category tagging per interaction (`bleeding`, `cardiac`, `toxicity`, `electrolyte`, `metabolic`).
- Monitoring notes are now tied to risk categories (INR/Hb for bleeding, ECG for cardiac, levels/markers for toxicity, potassium for electrolyte risk).
- Side-effect overlap output now filters out low-value generic noise and prioritizes clinically relevant effects.

Implemented in:

- `backend/app/services/interaction_engine.py`

### 4) API Output Enhancements (Backward-Compatible Additions)

Added fields to the existing response payload:

- `primary_interaction`
- `secondary_interactions`
- `modifiers`
- `risk_summary`
- `risk_types`

Schema updates in:

- `backend/app/schemas/interaction.py`

### 5) Data Enrichment for Rule Coverage

Curated catalog entries were expanded for targeted rule and pathway detection (e.g., tacrolimus, simvastatin, amlodipine, amiodarone, methotrexate, ciprofloxacin).

Data file:

- `backend/data/drug_catalog.json`

### 6) Frontend Integration and Reliability Fixes

- Added typings for new API fields and risk tags.
- Results panel now surfaces risk types while preserving existing layout and flow.
- Dev API routing fixed to avoid 8001 connection issues by using Vite proxy (`/api/v1` -> `localhost:8000`).

Implemented in:

- `frontend/src/types/api.ts`
- `frontend/src/components/InteractionResult.tsx`
- `frontend/src/api/client.ts`
- `frontend/vite.config.ts`
- `frontend/.env.example`

### 7) UI/UX Refresh (Minimalist, Classy)

- Updated visual system, spacing, typography, and panel/list polish.
- Improved mobile responsiveness and interaction states.

Implemented in:

- `frontend/src/styles.css`
- `frontend/src/App.tsx`
- `frontend/src/pages/Home.tsx`
- `frontend/src/pages/Results.tsx`
- `frontend/src/components/DrugInputBox.tsx`
- `frontend/src/components/WarningPanel.tsx`

### 8) Quick Validation Commands

Backend scenario check:

```powershell
$body = @{ drugs = @('naproxen','prednisone','omeprazole'); allergies = @(); conditions = @(); lang = 'en' } | ConvertTo-Json -Depth 4
Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/check-interactions' -Method Post -ContentType 'application/json' -Body $body
```

Secondary metabolic scenario check:

```powershell
$body = @{ drugs = @('tacrolimus','simvastatin'); allergies = @(); conditions = @(); lang = 'en' } | ConvertTo-Json -Depth 4
Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/check-interactions' -Method Post -ContentType 'application/json' -Body $body
```

Frontend production build check:

```bash
cd frontend
npm run build
```

## Next Production Steps

- Add EU/German data enrichment pipeline (ABDA/if licensed, EMA labels, BfArM integration)
- Add authentication, RBAC, and audit trails (pharmacist vs public mode)
- Add test suite, observability, and CI/CD gates
