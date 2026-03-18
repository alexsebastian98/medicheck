from pydantic import BaseModel, Field


class DrugRecord(BaseModel):
    name: str
    rxnorm_id: str | None = None
    side_effects: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    label_interactions: list[str] = Field(default_factory=list)
    source: str = "local-catalog"
