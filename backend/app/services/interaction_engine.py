import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from app.models.drug_model import DrugRecord
from app.models.interaction_model import InteractionRecord
from app.schemas.interaction import (
    InteractionFinding,
    SeverityLevel,
    SideEffectAggregate,
    SupportedLanguage,
    WarningItem,
)


class InteractionEngine:
    def __init__(self) -> None:
        self.interactions = self._load_interactions()

    def _load_interactions(self) -> dict[tuple[str, str], InteractionRecord]:
        data_file = Path(__file__).resolve().parents[2] / "data" / "interactions.json"
        with data_file.open("r", encoding="utf-8") as f:
            rows = json.load(f)

        mapping: dict[tuple[str, str], InteractionRecord] = {}
        for row in rows:
            key = tuple(sorted([row["drug_a"].lower(), row["drug_b"].lower()]))
            mapping[key] = InteractionRecord(**row)
        return mapping

    def detect_pairwise_interactions(self, drugs: list[DrugRecord]) -> list[InteractionFinding]:
        findings: list[InteractionFinding] = []

        for a, b in combinations(drugs, 2):
            key = tuple(sorted([a.name.lower(), b.name.lower()]))
            if key not in self.interactions:
                continue

            record = self.interactions[key]
            findings.append(
                InteractionFinding(
                    drug_a=a.name,
                    drug_b=b.name,
                    severity=SeverityLevel(record.severity),
                    mechanism=record.mechanism,
                    description=record.description,
                    source=record.source,
                )
            )
        return findings

    def aggregate_side_effects(self, drugs: list[DrugRecord]) -> list[SideEffectAggregate]:
        effect_to_drugs: dict[str, set[str]] = {}

        for drug in drugs:
            for effect in drug.side_effects:
                normalized = effect.strip().lower()
                if not normalized:
                    continue
                effect_to_drugs.setdefault(normalized, set()).add(drug.name)

        overlap = [
            SideEffectAggregate(effect=effect, drugs=sorted(list(drug_set)))
            for effect, drug_set in effect_to_drugs.items()
            if len(drug_set) >= 2
        ]

        return sorted(overlap, key=lambda x: len(x.drugs), reverse=True)

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
