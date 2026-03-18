from pydantic import BaseModel


class InteractionRecord(BaseModel):
    drug_a: str
    drug_b: str
    severity: str
    description: str
    mechanism: str
    source: str = "internal-dataset"
