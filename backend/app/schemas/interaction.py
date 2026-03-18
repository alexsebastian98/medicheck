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
    drugs: list[str] = Field(min_length=2, max_length=5)
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
    drug_a: str
    drug_b: str
    severity: SeverityLevel
    mechanism: str
    description: str
    source: str


class SideEffectAggregate(BaseModel):
    effect: str
    drugs: list[str]
    frequency_hint: str | None = None


class WarningItem(BaseModel):
    type: str
    message: str
    severity: SeverityLevel


class ExplanationBlock(BaseModel):
    simple: str
    clinical: str


class CheckInteractionsResponse(BaseModel):
    request_id: str
    timestamp: datetime
    language: SupportedLanguage
    normalized_drugs: list[DrugMatch]
    overall_severity: SeverityLevel
    interactions: list[InteractionFinding]
    overlapping_side_effects: list[SideEffectAggregate]
    warnings: list[WarningItem]
    explanations: ExplanationBlock
    recommendations: list[str]


class DrugInfoResponse(BaseModel):
    name: str
    rxnorm_id: str | None = None
    side_effects: list[str]
    contraindications: list[str]
    source: str
