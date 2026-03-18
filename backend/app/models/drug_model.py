from pydantic import BaseModel


class DrugRecord(BaseModel):
    name: str
    rxnorm_id: str | None = None
    side_effects: list[str] = []
    contraindications: list[str] = []
    classes: list[str] = []
