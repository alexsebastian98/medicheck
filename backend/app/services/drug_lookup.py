import json
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.models.drug_model import DrugRecord

settings = get_settings()


class DrugLookupService:
    def __init__(self) -> None:
        self.catalog = self._load_local_catalog()

    def _load_local_catalog(self) -> dict[str, DrugRecord]:
        data_file = Path(__file__).resolve().parents[2] / "data" / "drug_catalog.json"
        with data_file.open("r", encoding="utf-8") as f:
            rows = json.load(f)
        return {row["name"].lower(): DrugRecord(**row) for row in rows}

    async def normalize_drug(self, name: str) -> tuple[str, str | None]:
        cleaned = name.strip().lower()
        if cleaned in self.catalog:
            return cleaned, self.catalog[cleaned].rxnorm_id

        # RxNorm normalization fallback for unknown names.
        rxnorm_id = await self._fetch_rxnorm_id(cleaned)
        return cleaned, rxnorm_id

    async def get_drug_info(self, name: str) -> DrugRecord:
        normalized, rxnorm_id = await self.normalize_drug(name)
        if normalized in self.catalog:
            return self.catalog[normalized]

        side_effects, contraindications = await self._fetch_openfda_label_data(name)
        return DrugRecord(
            name=normalized,
            rxnorm_id=rxnorm_id,
            side_effects=side_effects,
            contraindications=contraindications,
            classes=[],
        )

    async def _fetch_rxnorm_id(self, name: str) -> str | None:
        url = f"{settings.rxnorm_base_url}/rxcui.json"
        params = {"name": name}
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
            ids = payload.get("idGroup", {}).get("rxnormId", [])
            return ids[0] if ids else None
        except Exception:
            return None

    async def _fetch_openfda_label_data(self, name: str) -> tuple[list[str], list[str]]:
        url = f"{settings.openfda_base_url}/drug/label.json"
        query = f'openfda.generic_name:"{name}"+OR+openfda.brand_name:"{name}"'
        params = {"search": query, "limit": 1}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()

            results = payload.get("results", [])
            if not results:
                return [], []

            label = results[0]
            side_effects = label.get("adverse_reactions", [])
            contraindications = label.get("contraindications", [])

            return side_effects[:8], contraindications[:8]
        except Exception:
            return [], []
