from app.schemas.interaction import SeverityLevel, SupportedLanguage


_TEXT = {
    "severity": {
        "en": {
            SeverityLevel.low: "Low risk",
            SeverityLevel.moderate: "Moderate risk",
            SeverityLevel.high: "High risk",
        },
        "de": {
            SeverityLevel.low: "Niedriges Risiko",
            SeverityLevel.moderate: "Mittleres Risiko",
            SeverityLevel.high: "Hohes Risiko",
        },
    },
    "recommendation_monitor": {
        "en": "Monitor symptoms and consult your pharmacist before continuing this combination.",
        "de": "Beobachten Sie Symptome und sprechen Sie vor der weiteren Einnahme mit Ihrer Apotheke.",
    },
    "recommendation_urgent": {
        "en": "This combination needs immediate professional review due to elevated safety risk.",
        "de": "Diese Kombination sollte wegen eines erhöhten Sicherheitsrisikos sofort fachlich geprüft werden.",
    },
    "recommendation_general": {
        "en": "Always verify dose timing and avoid self-adjusting medication plans.",
        "de": "Prüfen Sie immer die Dosierungszeiten und passen Sie den Medikationsplan nicht eigenständig an.",
    },
}


def t(key: str, lang: SupportedLanguage) -> str:
    entry = _TEXT.get(key, {})
    return entry.get(lang.value, entry.get("en", key))


def severity_label(level: SeverityLevel, lang: SupportedLanguage) -> str:
    mapping = _TEXT["severity"].get(lang.value, _TEXT["severity"]["en"])
    return mapping[level]
