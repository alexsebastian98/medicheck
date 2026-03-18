# API Examples

## POST /api/v1/check-interactions

### Request

```json
{
  "drugs": ["aspirin", "warfarin", "ibuprofen"],
  "allergies": ["ibuprofen"],
  "conditions": ["bleeding disorder"],
  "lang": "de"
}
```

### Response (example)

```json
{
  "request_id": "a17f95b6-742f-4ca9-bdb5-a6e743c30f8a",
  "timestamp": "2026-03-18T09:23:10.555842+00:00",
  "language": "de",
  "normalized_drugs": [
    { "input_name": "aspirin", "normalized_name": "aspirin", "rxnorm_id": "1191" },
    { "input_name": "warfarin", "normalized_name": "warfarin", "rxnorm_id": "11289" },
    { "input_name": "ibuprofen", "normalized_name": "ibuprofen", "rxnorm_id": "5640" }
  ],
  "overall_severity": "HIGH",
  "interactions": [
    {
      "drug_a": "aspirin",
      "drug_b": "warfarin",
      "severity": "HIGH",
      "mechanism": "Additive antithrombotic activity",
      "description": "Combined anticoagulant and antiplatelet effects increase bleeding risk.",
      "source": "curated-reference"
    }
  ],
  "overlapping_side_effects": [
    {
      "effect": "bleeding",
      "drugs": ["aspirin", "warfarin"]
    },
    {
      "effect": "nausea",
      "drugs": ["aspirin", "ibuprofen"]
    }
  ],
  "warnings": [
    {
      "type": "allergy",
      "message": "Allergieliste der Patientin/des Patienten enthalt ibuprofen.",
      "severity": "HIGH"
    }
  ],
  "explanations": {
    "simple": "Die gleichzeitige Einnahme kann das Blutungsrisiko erhohen.",
    "clinical": "Kombinierte gerinnungshemmende Effekte erhohen das Hamorrhagierisiko."
  },
  "recommendations": [
    "Diese Kombination sollte wegen eines erhohten Sicherheitsrisikos sofort fachlich gepruft werden.",
    "Beobachten Sie Symptome und sprechen Sie vor der weiteren Einnahme mit Ihrer Apotheke.",
    "Prufen Sie immer die Dosierungszeiten und passen Sie den Medikationsplan nicht eigenstandig an."
  ]
}
```

## GET /api/v1/drug-info/aspirin

### Response (example)

```json
{
  "name": "aspirin",
  "rxnorm_id": "1191",
  "side_effects": ["nausea", "stomach irritation", "bleeding"],
  "contraindications": ["active ulcer", "bleeding disorder"],
  "source": "local-catalog"
}
```
