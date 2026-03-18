from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import get_db_dependency
from app.schemas.interaction import (
    CheckInteractionsRequest,
    CheckInteractionsResponse,
    DrugInfoResponse,
    DrugMatch,
    ExplanationBlock,
    SeverityLevel,
)
from app.services.ai_explainer import AIExplainer
from app.services.drug_lookup import DrugLookupService
from app.services.interaction_engine import InteractionEngine
from app.services.severity_engine import SeverityEngine
from app.services.translation_service import t

router = APIRouter(tags=["drug-safety"])

drug_lookup = DrugLookupService()
interaction_engine = InteractionEngine()
severity_engine = SeverityEngine()
ai_explainer = AIExplainer()


def _recommendations(overall: SeverityLevel, lang) -> list[str]:
    base = [t("recommendation_general", lang)]
    if overall == SeverityLevel.high:
        return [t("recommendation_urgent", lang), t("recommendation_monitor", lang)] + base
    if overall == SeverityLevel.moderate:
        return [t("recommendation_monitor", lang)] + base
    return base


@router.post("/check-interactions", response_model=CheckInteractionsResponse)
async def check_interactions(
    payload: CheckInteractionsRequest,
    db: AsyncIOMotorDatabase = Depends(get_db_dependency),
) -> CheckInteractionsResponse:
    if len(payload.drugs) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 unique drugs are required.",
        )

    normalized_drugs = []
    drug_records = []

    for drug_name in payload.drugs:
        record = await drug_lookup.get_drug_info(drug_name)
        drug_records.append(record)
        normalized_drugs.append(
            DrugMatch(
                input_name=drug_name,
                normalized_name=record.name,
                rxnorm_id=record.rxnorm_id,
            )
        )

    interactions = interaction_engine.detect_pairwise_interactions(drug_records)
    side_effects = interaction_engine.aggregate_side_effects(drug_records)

    warnings = interaction_engine.detect_duplicate_class_usage(drug_records, payload.lang)
    warnings.extend(
        interaction_engine.detect_condition_and_allergy_warnings(
            drugs=drug_records,
            conditions=payload.conditions,
            allergies=payload.allergies,
            lang=payload.lang,
        )
    )

    overall = severity_engine.derive_overall(interactions, warnings)
    simple, clinical = await ai_explainer.generate_explanations(interactions, overall, payload.lang)

    response = CheckInteractionsResponse(
        request_id=str(uuid4()),
        timestamp=datetime.now(tz=timezone.utc),
        language=payload.lang,
        normalized_drugs=normalized_drugs,
        overall_severity=overall,
        interactions=interactions,
        overlapping_side_effects=side_effects,
        warnings=warnings,
        explanations=ExplanationBlock(simple=simple, clinical=clinical),
        recommendations=_recommendations(overall, payload.lang),
    )

    await db.logs.insert_one(
        {
            "request_id": response.request_id,
            "drugs_checked": payload.drugs,
            "lang": payload.lang.value,
            "timestamp": response.timestamp,
            "result": response.model_dump(),
        }
    )

    return response


@router.post("/analyze-combination", response_model=CheckInteractionsResponse)
async def analyze_combination(
    payload: CheckInteractionsRequest,
    db: AsyncIOMotorDatabase = Depends(get_db_dependency),
) -> CheckInteractionsResponse:
    return await check_interactions(payload, db)


@router.get("/drug-info/{drug_name}", response_model=DrugInfoResponse)
async def get_drug_info(drug_name: str) -> DrugInfoResponse:
    record = await drug_lookup.get_drug_info(drug_name)
    source = "local-catalog" if record.name in drug_lookup.catalog else "openfda"
    return DrugInfoResponse(
        name=record.name,
        rxnorm_id=record.rxnorm_id,
        side_effects=record.side_effects,
        contraindications=record.contraindications,
        source=source,
    )
