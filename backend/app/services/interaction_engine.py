import json
import re
from collections import Counter
from itertools import combinations
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.drug_model import DrugRecord
from app.models.interaction_model import InteractionRecord
from app.schemas.interaction import (
    InteractionFinding,
    ModifierItem,
    SeverityLevel,
    SideEffectAggregate,
    SupportedLanguage,
    WarningItem,
)

_CLASS_RULES = [
    {
        "classes": ("nsaid", "corticosteroid"),
        "severity": SeverityLevel.moderate,
        "mechanism": "Combined gastric mucosal injury",
        "description": "NSAIDs and corticosteroids both increase gastric irritation, raising risk of ulcers and bleeding.",
    },
    {
        "classes": ("nsaid", "ssri"),
        "severity": SeverityLevel.moderate,
        "mechanism": "Platelet and mucosal bleeding pathway overlap",
        "description": "NSAIDs can injure gastric mucosa while SSRIs reduce platelet serotonin signaling, increasing bleeding risk.",
    },
    {
        "classes": ("diuretic", "digoxin"),
        "severity": SeverityLevel.high,
        "mechanism": "Electrolyte-mediated digoxin toxicity",
        "description": "Diuretic-related potassium shifts can increase digoxin effect and trigger toxicity, including arrhythmia risk.",
    },
]

_CLASS_SYNONYMS = {
    "nsaid": ["nsaid", "nonsteroidal anti-inflammatory", "cox inhibitor"],
    "corticosteroid": ["corticosteroid", "glucocorticoid", "steroid"],
    "ssri": ["ssri", "selective serotonin reuptake inhibitor"],
    "diuretic": ["diuretic", "loop diuretic", "thiazide", "potassium-sparing diuretic"],
    "digoxin": ["digoxin", "cardiac glycoside"],
    "ppi": ["ppi", "proton pump inhibitor"],
}

_PPI_DRUGS = {"omeprazole", "pantoprazole", "esomeprazole", "lansoprazole", "rabeprazole"}

_PRIMARY_RISK_TERMS = {
    "bleed": 3,
    "bleeding": 3,
    "hemorrhage": 3,
    "arrhythmia": 3,
    "toxicity": 3,
    "toxic": 3,
    "ulcer": 2,
}


class InteractionEngine:
    def __init__(self) -> None:
        self.interactions = self._load_interactions()
        self.mongo_cache_disabled = False

    def _load_interactions(self) -> dict[tuple[str, str], InteractionRecord]:
        data_file = Path(__file__).resolve().parents[2] / "data" / "interactions.json"
        with data_file.open("r", encoding="utf-8") as f:
            rows = json.load(f)

        mapping: dict[tuple[str, str], InteractionRecord] = {}
        for row in rows:
            key = tuple(sorted([row["drug_a"].lower(), row["drug_b"].lower()]))
            mapping[key] = InteractionRecord(**row)
        return mapping

    async def detect_pairwise_interactions(
        self,
        drugs: list[DrugRecord],
        db: AsyncIOMotorDatabase | None = None,
    ) -> list[InteractionFinding]:
        findings: list[InteractionFinding] = []

        for a, b in combinations(drugs, 2):
            candidates: list[InteractionFinding] = []
            seed_or_label = await self._get_live_or_cached_interaction(a, b, db)
            if seed_or_label is not None:
                candidates.append(seed_or_label)

            class_rule = self._extract_class_rule_interaction(a, b)
            if class_rule is not None:
                candidates.append(class_rule)

            if not candidates:
                continue

            finding = max(candidates, key=lambda item: self._severity_rank(item.severity))
            finding.id = f"int_{len(findings) + 1:03d}"
            findings.append(finding)
        return findings

    def _extract_class_rule_interaction(
        self,
        drug_a: DrugRecord,
        drug_b: DrugRecord,
    ) -> InteractionFinding | None:
        tags_a = self._normalize_drug_classes(drug_a)
        tags_b = self._normalize_drug_classes(drug_b)
        pair_tags = tags_a | tags_b

        matches: list[dict] = []
        for rule in _CLASS_RULES:
            required = set(rule["classes"])
            if required.issubset(pair_tags):
                if required.issubset(tags_a) or required.issubset(tags_b):
                    continue
                matches.append(rule)

        if not matches:
            return None

        best = max(matches, key=lambda item: self._severity_rank(item["severity"]))
        return InteractionFinding(
            id="",
            drug_a=drug_a.name,
            drug_b=drug_b.name,
            severity=best["severity"],
            severity_score=0.0,
            mechanism=best["mechanism"],
            description=best["description"],
            source="class-rule",
        )

    def _normalize_drug_classes(self, drug: DrugRecord) -> set[str]:
        terms = [drug.name.lower()] + [item.lower() for item in drug.classes]
        tags: set[str] = set()

        for canonical, synonyms in _CLASS_SYNONYMS.items():
            if any(synonym in term for term in terms for synonym in synonyms):
                tags.add(canonical)

        if drug.name.lower() in _PPI_DRUGS:
            tags.add("ppi")

        return tags

    def detect_modifiers(
        self,
        drugs: list[DrugRecord],
        interactions: list[InteractionFinding],
    ) -> list[ModifierItem]:
        ppis = [drug.name for drug in drugs if "ppi" in self._normalize_drug_classes(drug)]
        if not ppis or not interactions:
            return []

        gi_interaction_ids = [
            item.id
            for item in interactions
            if any(term in f"{item.description} {item.mechanism}".lower() for term in ["gi", "gastric", "ulcer", "bleed"])
        ]
        if not gi_interaction_ids:
            return []

        return [
            ModifierItem(
                type="protective",
                drug=drug_name,
                effect="PPI reduces gastric acid exposure and can lower GI bleeding risk.",
                applies_to=gi_interaction_ids,
                severity_delta=-0.2,
            )
            for drug_name in ppis
        ]

    def select_primary_interaction(
        self,
        interactions: list[InteractionFinding],
    ) -> InteractionFinding | None:
        if not interactions:
            return None

        def _priority_score(item: InteractionFinding) -> tuple[int, int, float]:
            lowered = f"{item.description} {item.mechanism}".lower()
            keyword_weight = max(
                [weight for term, weight in _PRIMARY_RISK_TERMS.items() if term in lowered],
                default=0,
            )
            return (self._severity_rank(item.severity), keyword_weight, item.severity_score)

        return max(interactions, key=_priority_score)

    def build_risk_summary(
        self,
        interactions: list[InteractionFinding],
        primary_interaction: InteractionFinding | None,
        modifiers: list[ModifierItem],
        lang: SupportedLanguage,
    ) -> str:
        if not interactions:
            return (
                "No clinically significant interaction risk detected from available rules and data."
                if lang == SupportedLanguage.en
                else "Kein klinisch relevantes Interaktionsrisiko aus verfugbaren Regeln und Daten erkannt."
            )

        if primary_interaction is None:
            return (
                "Interaction risk detected; monitor symptoms and review treatment plan."
                if lang == SupportedLanguage.en
                else "Interaktionsrisiko erkannt; Symptome uberwachen und Therapieplan prufen."
            )

        if not modifiers:
            return (
                f"Primary interaction: {primary_interaction.drug_a} + {primary_interaction.drug_b}. "
                "Risk is increased and should be monitored closely."
                if lang == SupportedLanguage.en
                else f"Primare Interaktion: {primary_interaction.drug_a} + {primary_interaction.drug_b}. "
                "Das Risiko ist erhoht und sollte engmaschig uberwacht werden."
            )

        protective_names = ", ".join(sorted({item.drug for item in modifiers}))
        return (
            f"Primary interaction: {primary_interaction.drug_a} + {primary_interaction.drug_b}. "
            f"Risk is increased by this combination and partially reduced by {protective_names}."
            if lang == SupportedLanguage.en
            else f"Primare Interaktion: {primary_interaction.drug_a} + {primary_interaction.drug_b}. "
            f"Das Risiko ist durch die Kombination erhoht und wird durch {protective_names} teilweise reduziert."
        )

    async def _get_live_or_cached_interaction(
        self,
        drug_a: DrugRecord,
        drug_b: DrugRecord,
        db: AsyncIOMotorDatabase | None,
    ) -> InteractionFinding | None:
        key_a, key_b = sorted([drug_a.name.lower(), drug_b.name.lower()])

        if db is not None and not self.mongo_cache_disabled:
            try:
                cached = await db.interactions.find_one({"drug_a": key_a, "drug_b": key_b})
                if cached:
                    cached.pop("_id", None)
                    return InteractionFinding(id="", severity_score=0.0, **cached)
            except Exception:
                self.mongo_cache_disabled = True
                pass

        live_finding = self._extract_label_based_interaction(drug_a, drug_b)
        if live_finding is None:
            live_finding = self._extract_seed_interaction(drug_a, drug_b)

        if live_finding is not None and db is not None and not self.mongo_cache_disabled:
            try:
                await db.interactions.update_one(
                    {"drug_a": key_a, "drug_b": key_b},
                    {
                        "$set": {
                            "drug_a": live_finding.drug_a,
                            "drug_b": live_finding.drug_b,
                            "severity": live_finding.severity.value,
                            "mechanism": live_finding.mechanism,
                            "description": live_finding.description,
                            "source": live_finding.source,
                        }
                    },
                    upsert=True,
                )
            except Exception:
                self.mongo_cache_disabled = True
                pass

        return live_finding

    def _extract_seed_interaction(
        self,
        drug_a: DrugRecord,
        drug_b: DrugRecord,
    ) -> InteractionFinding | None:
        key = tuple(sorted([drug_a.name.lower(), drug_b.name.lower()]))
        if key not in self.interactions:
            return None

        record = self.interactions[key]
        return InteractionFinding(
            id="",
            drug_a=drug_a.name,
            drug_b=drug_b.name,
            severity=SeverityLevel(record.severity),
            severity_score=0.0,
            mechanism=record.mechanism,
            description=record.description,
            source=record.source,
        )

    def _extract_label_based_interaction(
        self,
        drug_a: DrugRecord,
        drug_b: DrugRecord,
    ) -> InteractionFinding | None:
        match_a = self._match_label_interaction(drug_a, drug_b)
        match_b = self._match_label_interaction(drug_b, drug_a)
        candidates = [candidate for candidate in [match_a, match_b] if candidate is not None]
        if not candidates:
            return None

        best = max(candidates, key=lambda item: self._severity_rank(item[0]))
        severity, description = best
        return InteractionFinding(
            id="",
            drug_a=drug_a.name,
            drug_b=drug_b.name,
            severity=severity,
            severity_score=0.0,
            mechanism="OpenFDA label-derived interaction",
            description=description,
            source="openfda-label",
        )

    def _match_label_interaction(
        self,
        source_drug: DrugRecord,
        target_drug: DrugRecord,
    ) -> tuple[SeverityLevel, str] | None:
        aliases = [target_drug.name] + target_drug.aliases
        for block in source_drug.label_interactions:
            sentences = re.split(r"(?<=[.!?])\s+", block)
            for sentence in sentences:
                lowered = sentence.lower()
                if any(re.search(rf"\b{re.escape(alias)}\b", lowered) for alias in aliases if alias):
                    return self._severity_from_text(lowered), sentence.strip()
        return None

    def _severity_from_text(self, text: str) -> SeverityLevel:
        if any(term in text for term in ["contraindicat", "avoid", "severe", "major", "bleed"]):
            return SeverityLevel.high
        if any(term in text for term in ["monitor", "adjust", "increase", "decrease", "caution"]):
            return SeverityLevel.moderate
        return SeverityLevel.low

    def _severity_rank(self, severity: SeverityLevel) -> int:
        return {
            SeverityLevel.low: 1,
            SeverityLevel.moderate: 2,
            SeverityLevel.high: 3,
        }[severity]

    def aggregate_side_effects(self, drugs: list[DrugRecord]) -> list[SideEffectAggregate]:
        effect_to_drugs: dict[str, set[str]] = {}

        for drug in drugs:
            for effect in drug.side_effects:
                normalized = effect.strip().lower()
                if not normalized:
                    continue
                effect_to_drugs.setdefault(normalized, set()).add(drug.name)

        overlap = []
        for index, (effect, drug_set) in enumerate(effect_to_drugs.items(), start=1):
            if len(drug_set) < 2:
                continue

            overlap.append(
                SideEffectAggregate(
                    id=f"se_{index:03d}",
                    side_effect=effect,
                    drugs=sorted(list(drug_set)),
                    severity_score=min(1.0, 0.2 * len(drug_set)),
                )
            )

        return sorted(overlap, key=lambda x: len(x.drugs), reverse=True)

    def build_monitoring_notes(
        self,
        drugs: list[DrugRecord],
        interactions: list[InteractionFinding],
        overlapping_side_effects: list[SideEffectAggregate],
        lang: SupportedLanguage,
    ) -> list[str]:
        notes: list[str] = []
        drug_names = {drug.name.lower() for drug in drugs}
        side_effect_names = {item.side_effect.lower() for item in overlapping_side_effects}
        interaction_text = " ".join(
            [f"{item.description} {item.mechanism}".lower() for item in interactions]
        )

        if "bleeding" in interaction_text or "bleeding" in side_effect_names:
            notes.append(
                "Monitor for bruising, GI bleeding, hemoglobin, and hematocrit."
                if lang == SupportedLanguage.en
                else "Kontrollieren Sie Blutungszeichen, Hb, Hamatokrit und gastrointestinale Blutungen."
            )

        if {"lisinopril", "metformin"} & drug_names or "kidney stress" in side_effect_names:
            notes.append(
                "Monitor serum creatinine, potassium, renal function, and blood pressure."
                if lang == SupportedLanguage.en
                else "Kontrollieren Sie Serumkreatinin, Kalium, Nierenfunktion und Blutdruck."
            )

        if "metformin" in drug_names:
            notes.append(
                "Monitor glucose control and renal function during therapy changes."
                if lang == SupportedLanguage.en
                else "Uberwachen Sie Blutzuckerkontrolle und Nierenfunktion bei Therapieanderungen."
            )

        if "dizziness" in side_effect_names or "nausea" in side_effect_names:
            notes.append(
                "Monitor hydration status, orthostatic symptoms, and overall tolerance."
                if lang == SupportedLanguage.en
                else "Uberwachen Sie Hydratation, orthostatische Beschwerden und die allgemeine Vertrlichkeit."
            )

        if not notes:
            notes.append(
                "Continue routine symptom review and reassess if new symptoms emerge."
                if lang == SupportedLanguage.en
                else "Fuhren Sie die routinemassige Symptomkontrolle fort und beurteilen Sie neue Beschwerden erneut."
            )

        return notes

    def detect_duplicate_class_usage(
        self,
        drugs: list[DrugRecord],
        lang: SupportedLanguage,
    ) -> list[WarningItem]:
        class_counter = Counter()
        class_to_drugs: dict[str, list[str]] = {}

        for drug in drugs:
            for drug_class in drug.classes:
                normalized = drug_class.strip().lower()
                class_counter[normalized] += 1
                class_to_drugs.setdefault(normalized, []).append(drug.name)

        warnings: list[WarningItem] = []
        for drug_class, count in class_counter.items():
            if count >= 2:
                if lang == SupportedLanguage.de:
                    message = (
                        f"Mehrere Arzneimittel aus der Klasse '{drug_class}' erkannt: "
                        f"{', '.join(sorted(class_to_drugs[drug_class]))}."
                    )
                else:
                    message = (
                        f"Multiple drugs in class '{drug_class}' detected: "
                        f"{', '.join(sorted(class_to_drugs[drug_class]))}."
                    )

                warnings.append(
                    WarningItem(
                        type="duplicate_class",
                        message=message,
                        severity=SeverityLevel.moderate,
                    )
                )
        return warnings

    def detect_condition_and_allergy_warnings(
        self,
        drugs: list[DrugRecord],
        conditions: list[str],
        allergies: list[str],
        lang: SupportedLanguage,
    ) -> list[WarningItem]:
        warnings: list[WarningItem] = []
        condition_set = {c.lower().strip() for c in conditions}
        allergy_set = {a.lower().strip() for a in allergies}

        for drug in drugs:
            for contraindication in drug.contraindications:
                c_text = contraindication.lower()
                if any(condition in c_text for condition in condition_set if condition):
                    if lang == SupportedLanguage.de:
                        message = (
                            f"{drug.name} hat eine Kontraindikation, die zur Patientensituation passt: "
                            f"{contraindication}."
                        )
                    else:
                        message = (
                            f"{drug.name} has contraindication relevant to patient condition: "
                            f"{contraindication}."
                        )

                    warnings.append(
                        WarningItem(
                            type="contraindication",
                            message=message,
                            severity=SeverityLevel.high,
                        )
                    )

            if drug.name.lower() in allergy_set:
                message = (
                    f"Allergieliste der Patientin/des Patienten enthält {drug.name}."
                    if lang == SupportedLanguage.de
                    else f"Patient allergy list includes {drug.name}."
                )
                warnings.append(
                    WarningItem(
                        type="allergy",
                        message=message,
                        severity=SeverityLevel.high,
                    )
                )

        return warnings
