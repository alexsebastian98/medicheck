from openai import OpenAI

from app.core.config import get_settings
from app.schemas.interaction import InteractionFinding, SeverityLevel, SupportedLanguage

settings = get_settings()


class AIExplainer:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def generate_explanations(
        self,
        interactions: list[InteractionFinding],
        overall_severity: SeverityLevel,
        lang: SupportedLanguage,
    ) -> tuple[str, str]:
        if not interactions:
            return self._safe_no_interaction_text(lang)

        factual_lines = [
            f"- {item.drug_a} + {item.drug_b}: {item.description} (severity={item.severity.value})"
            for item in interactions
        ]
        facts_block = "\n".join(factual_lines)

        if not self.client:
            return self._template_fallback(interactions, overall_severity, lang)

        prompt = self._build_prompt(facts_block, overall_severity, lang)

        try:
            response = self.client.responses.create(
                model=settings.openai_model,
                input=prompt,
                max_output_tokens=280,
            )
            text = response.output_text.strip()
            simple, clinical = self._split_output(text, overall_severity, lang)
            return simple, clinical
        except Exception:
            return self._template_fallback(interactions, overall_severity, lang)

    def _build_prompt(self, facts_block: str, severity: SeverityLevel, lang: SupportedLanguage) -> str:
        language_name = "German" if lang == SupportedLanguage.de else "English"
        return (
            "You are a clinical communication assistant. "
            "Use ONLY the provided facts. Do not add new medical facts, numbers, or claims. "
            f"Return in {language_name}. "
            "Format exactly as two lines:\n"
            "Simple: ...\n"
            "Clinical: ...\n\n"
            f"Overall severity: {severity.value}\n"
            f"Facts:\n{facts_block}"
        )

    def _split_output(
        self,
        text: str,
        severity: SeverityLevel,
        lang: SupportedLanguage,
    ) -> tuple[str, str]:
        simple = ""
        clinical = ""
        for line in text.splitlines():
            if line.lower().startswith("simple:"):
                simple = line.split(":", 1)[1].strip()
            if line.lower().startswith("clinical:"):
                clinical = line.split(":", 1)[1].strip()

        if not simple or not clinical:
            return self._template_fallback([], severity, lang)
        return simple, clinical

    def _template_fallback(
        self,
        interactions: list[InteractionFinding],
        severity: SeverityLevel,
        lang: SupportedLanguage,
    ) -> tuple[str, str]:
        if lang == SupportedLanguage.de:
            simple = (
                "Diese Arzneimittelkombination kann relevante Nebenwirkungen verursachen. "
                "Lassen Sie die Kombination in der Apotheke oder ärztlich prüfen."
            )
            clinical = (
                "Es wurden pharmakodynamische/klinisch relevante Interaktionen identifiziert "
                f"(Gesamtrisiko: {severity.value}). Eine strukturierte Medikationsprüfung wird empfohlen."
            )
        else:
            simple = (
                "This medication combination may cause meaningful side effects. "
                "Please review it with a pharmacist or physician."
            )
            clinical = (
                "Clinically relevant pharmacodynamic interactions were identified "
                f"(overall risk: {severity.value}). Structured medication review is recommended."
            )
        return simple, clinical

    def _safe_no_interaction_text(self, lang: SupportedLanguage) -> tuple[str, str]:
        if lang == SupportedLanguage.de:
            return (
                "Für diese Kombination wurden in den verfügbaren Daten keine relevanten Interaktionen gefunden.",
                "Aktuell keine signifikanten Interaktionen aus den verfügbaren strukturierten Quellen erkannt.",
            )
        return (
            "No relevant interactions were found for this combination in available data.",
            "No clinically significant interactions currently identified from available structured sources.",
        )
