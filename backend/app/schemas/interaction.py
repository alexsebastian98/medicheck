from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SupportedLanguage(str, Enum):
    en = "en"
    de = "de"


class SeverityLevel(str, Enum):
    low = "LOW"
    moderate = "MODERATE"
    high = "HIGH"


class CheckInteractionsRequest(BaseModel):
    drugs: list[str] = Field(min_length=2)
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    lang: SupportedLanguage = SupportedLanguage.en

    @field_validator("drugs", mode="before")
    @classmethod
    def normalize_drug_input(cls, value: list[str]) -> list[str]:
        cleaned = []
        for name in value:
            name = (name or "").strip().lower()
            if name and name not in cleaned:
                cleaned.append(name)
        return cleaned


class DrugMatch(BaseModel):
    input_name: str
    normalized_name: str
    rxnorm_id: str | None = None


class InteractionFinding(BaseModel):
    id: str
    drug_a: str
    drug_b: str
    severity: SeverityLevel
    severity_score: float = Field(ge=0.0, le=1.0)
    mechanism: str
    description: str
    source: str


class SideEffectAggregate(BaseModel):
    id: str
    side_effect: str
    drugs: list[str]
    severity_score: float = Field(ge=0.0, le=1.0)
    frequency_hint: str | None = None


class WarningItem(BaseModel):
    type: str
    message: str
    severity: SeverityLevel


class CheckInteractionsResponse(BaseModel):
    request_id: str
    timestamp: datetime
    language: SupportedLanguage
    normalized_drugs: list[DrugMatch]
    overall_severity: SeverityLevel
    overall_severity_score: float = Field(ge=0.0, le=1.0)
    interactions: list[InteractionFinding]
    overlapping_side_effects: list[SideEffectAggregate]
    monitoring_notes: list[str]
    warnings: list[WarningItem]
    patient_explanation: str
    clinical_explanation: str
    recommendations: list[str]


class DrugInfoResponse(BaseModel):
    name: str
    rxnorm_id: str | None = None
    side_effects: list[str]
    contraindications: list[str]
    source: str
