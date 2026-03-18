import json
import re
from pathlib import Path

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.models.drug_model import DrugRecord

settings = get_settings()

_SIDE_EFFECT_KEYWORDS = {
    "bleeding": "bleeding",
    "nausea": "nausea",
    "vomiting": "vomiting",
    "diarrhea": "diarrhea",
    "dizziness": "dizziness",
    "headache": "headache",
    "fatigue": "fatigue",
    "cough": "dry cough",
    "abdominal pain": "abdominal pain",
    "stomach": "stomach irritation",
    "rash": "rash",
    "hyperkalemia": "hyperkalemia",
    "kidney": "kidney stress",
}


class DrugLookupService:
    def __init__(self) -> None:
        self.catalog = self._load_local_catalog()
        self.mongo_cache_disabled = False

    def _load_local_catalog(self) -> dict[str, DrugRecord]:
        data_file = Path(__file__).resolve().parents[2] / "data" / "drug_catalog.json"
        with data_file.open("r", encoding="utf-8") as f:
            rows = json.load(f)
        catalog: dict[str, DrugRecord] = {}
        for row in rows:
            row.setdefault("aliases", [row["name"]])
            row.setdefault("label_interactions", [])
            row.setdefault("source", "local-catalog")
            catalog[row["name"].lower()] = DrugRecord(**row)
        return catalog

    async def normalize_drug(self, name: str) -> tuple[str, str | None]:
        cleaned = name.strip().lower()
        if cleaned in self.catalog:
            return cleaned, self.catalog[cleaned].rxnorm_id

        # RxNorm normalization fallback for unknown names.
        rxnorm_id = await self._fetch_rxnorm_id(cleaned)
        return cleaned, rxnorm_id

    async def get_drug_info(self, name: str, db: AsyncIOMotorDatabase | None = None) -> DrugRecord:
        normalized, rxnorm_id = await self.normalize_drug(name)

        # Fast path: if the drug is in our curated catalog, return immediately.
        # OpenFDA is used for uncatalogued drugs to keep broad coverage.
        if normalized in self.catalog:
            local_record = self.catalog[normalized]
            if not local_record.rxnorm_id:
                local_record.rxnorm_id = rxnorm_id
            return local_record

        cached = await self._get_cached_drug(normalized, db)
        if cached is not None:
            return cached

        local_record = self.catalog.get(normalized)
        label_payload = await self._fetch_openfda_label_payload(name)
        live_record = self._build_live_record(normalized, label_payload) if label_payload else None

        if live_record and local_record:
            merged = self._merge_records(local_record, live_record)
        elif live_record:
            merged = live_record
        elif local_record:
            merged = local_record
        else:
            side_effects, contraindications = await self._fetch_openfda_label_data(name)
            merged = DrugRecord(
                name=normalized,
                rxnorm_id=rxnorm_id,
                side_effects=side_effects,
                contraindications=contraindications,
                classes=[],
                aliases=[normalized],
                label_interactions=[],
                source="openfda-fallback" if side_effects or contraindications else "unresolved",
            )

        if not merged.rxnorm_id:
            merged.rxnorm_id = rxnorm_id

        await self._cache_drug(merged, db)
        return merged

    async def _get_cached_drug(
        self,
        normalized_name: str,
        db: AsyncIOMotorDatabase | None,
    ) -> DrugRecord | None:
        if db is None or self.mongo_cache_disabled:
            return None

        try:
            document = await db.drugs.find_one(
                {"$or": [{"name": normalized_name}, {"aliases": normalized_name}]}
            )
            if not document:
                return None

            document.pop("_id", None)
            return DrugRecord(**document)
        except Exception:
            self.mongo_cache_disabled = True
            return None

    async def _cache_drug(self, record: DrugRecord, db: AsyncIOMotorDatabase | None) -> None:
        if db is None or self.mongo_cache_disabled:
            return

        try:
            await db.drugs.update_one(
                {"name": record.name},
                {"$set": record.model_dump()},
                upsert=True,
            )
        except Exception:
            self.mongo_cache_disabled = True
            return

    def _merge_records(self, local_record: DrugRecord, live_record: DrugRecord) -> DrugRecord:
        return DrugRecord(
            name=live_record.name or local_record.name,
            rxnorm_id=live_record.rxnorm_id or local_record.rxnorm_id,
            side_effects=self._unique(live_record.side_effects + local_record.side_effects),
            contraindications=self._unique(
                live_record.contraindications + local_record.contraindications
            ),
            classes=self._unique(live_record.classes + local_record.classes),
            aliases=self._unique(live_record.aliases + local_record.aliases + [local_record.name]),
            label_interactions=self._unique(
                live_record.label_interactions + local_record.label_interactions
            ),
            source="openfda+local-catalog",
        )

    def _build_live_record(self, normalized_name: str, label: dict) -> DrugRecord:
        openfda = label.get("openfda", {})
        aliases = self._extract_aliases(openfda, normalized_name)
        rxnorm_id = self._extract_rxnorm_id(openfda)
        side_effects = self._extract_side_effect_terms(label.get("adverse_reactions", []))
        contraindications = label.get("contraindications", [])[:8]
        classes = self._extract_classes(openfda)
        label_interactions = label.get("drug_interactions", [])[:6]

        return DrugRecord(
            name=normalized_name,
            rxnorm_id=rxnorm_id,
            side_effects=side_effects,
            contraindications=contraindications,
            classes=classes,
            aliases=aliases,
            label_interactions=label_interactions,
            source="openfda",
        )

    def _extract_aliases(self, openfda: dict, normalized_name: str) -> list[str]:
        aliases = [normalized_name]
        for key in ["generic_name", "brand_name", "substance_name"]:
            for value in openfda.get(key, []):
                aliases.extend(self._split_alias_values(value))
        return self._unique(aliases)

    def _split_alias_values(self, value: str) -> list[str]:
        parts = re.split(r"[;,/]", value)
        return [part.strip().lower() for part in parts if part.strip()]

    def _extract_rxnorm_id(self, openfda: dict) -> str | None:
        values = openfda.get("rxcui", [])
        return values[0] if values else None

    def _extract_classes(self, openfda: dict) -> list[str]:
        classes: list[str] = []
        for key in ["pharm_class_epc", "pharm_class_moa", "pharm_class_cs"]:
            for value in openfda.get(key, []):
                classes.extend(self._split_alias_values(value))
        return self._unique(classes)

    def _extract_side_effect_terms(self, reaction_blocks: list[str]) -> list[str]:
        if not reaction_blocks:
            return []

        reaction_text = " ".join(reaction_blocks).lower()
        effects = [canonical for term, canonical in _SIDE_EFFECT_KEYWORDS.items() if term in reaction_text]
        return self._unique(effects)

    def _unique(self, values: list[str]) -> list[str]:
        seen: list[str] = []
        for value in values:
            cleaned = value.strip().lower()
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
        return seen

    async def _fetch_openfda_label_payload(self, name: str) -> dict | None:
        url = f"{settings.openfda_base_url}/drug/label.json"
        queries = [
            f'openfda.generic_name:"{name}"',
            f'openfda.brand_name:"{name}"',
            f'openfda.substance_name:"{name}"',
        ]

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                for query in queries:
                    response = await client.get(url, params={"search": query, "limit": 1})
                    if response.status_code >= 400:
                        continue

                    payload = response.json()
                    results = payload.get("results", [])
                    if results:
                        return results[0]
            return None
        except Exception:
            return None

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
        label = await self._fetch_openfda_label_payload(name)
        if not label:
            return [], []

        return (
            self._extract_side_effect_terms(label.get("adverse_reactions", [])),
            label.get("contraindications", [])[:8],
        )
