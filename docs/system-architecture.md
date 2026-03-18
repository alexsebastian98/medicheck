# System Architecture

## 1. Backend Layers

- `app/api/routes.py`: HTTP endpoints, request orchestration, logging
- `app/services/drug_lookup.py`: drug normalization, OpenFDA and RxNorm lookups
- `app/services/interaction_engine.py`: deterministic pairwise interactions + side effect overlap + warnings
- `app/services/severity_engine.py`: LOW/MODERATE/HIGH severity scoring
- `app/services/ai_explainer.py`: EN/DE explanation generation from structured facts only
- `app/db/mongodb.py`: MongoDB client lifecycle and dependency
- `app/schemas/interaction.py`: request/response contracts

## 2. Frontend Layers

- `src/pages/Home.tsx`: medication input and submit flow
- `src/pages/Results.tsx`: displays completed analysis
- `src/components/DrugInputBox.tsx`: input parsing and validation (2-5 meds)
- `src/components/InteractionResult.tsx`: structured medical result rendering
- `src/components/LanguageSwitcher.tsx`: EN/DE toggle
- `src/i18n/index.ts`: localization dictionary and i18next setup
- `src/api/interactionApi.ts`: backend communication

## 3. Data and Fact Reliability Model

- Deterministic engines consume curated datasets and external APIs.
- AI receives only extracted interaction facts and severity.
- AI output is restricted to dual-format communication:
  - Simple patient explanation
  - Clinical pharmacist explanation

## 4. Healthcare IT Alignment (Germany/EU)

- Multilingual response model (English/German)
- Clear deterministic + AI-assist split for compliance readiness
- Audit-friendly logs in MongoDB (`logs` collection)
- Extendable to EU regulated datasets and pharmacy systems (e.g., ABDA, if licensed)

## 5. Runtime Sequence

1. User submits 2-5 medications and language.
2. Backend normalizes names via local mapping and RxNorm fallback.
3. Drug metadata loaded from local catalog and optional OpenFDA label fallback.
4. Pairwise combinations are analyzed (`n*(n-1)/2`).
5. Side effects, contraindications, allergies, and duplicate classes are aggregated.
6. Severity engine computes overall level.
7. AI generates EN/DE simple and clinical explanation from facts.
8. Structured response is returned and persisted in `logs`.
