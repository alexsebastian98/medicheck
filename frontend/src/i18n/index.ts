import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {
      appTitle: "MediCheck",
      subtitle: "Drug interaction and safety analysis for multi-drug regimens",
      enterDrugs: "Enter medications",
      drugsPlaceholder: "e.g. aspirin, warfarin, ibuprofen",
      allergiesPlaceholder: "Allergies (optional)",
      conditionsPlaceholder: "Conditions (optional)",
      checkButton: "Analyze combination",
      loading: "Analyzing interaction profile...",
      noInteractions: "No known pairwise interactions in current dataset",
      severity: "Overall severity",
      interactions: "Interactions",
      sideEffects: "Overlapping side effects",
      monitoringNotes: "Monitoring notes",
      warnings: "Warnings",
      simpleExplanation: "Patient explanation",
      clinicalExplanation: "Clinical explanation",
      recommendations: "Recommendations",
      back: "Back",
      requiredHint: "Provide at least 2 medications.",
      footer: "Use this tool as decision support only. Professional review is required.",
    },
  },
  de: {
    translation: {
      appTitle: "MediCheck",
      subtitle: "Arzneimittel-Interaktions- und Sicherheitsanalyse fur Mehrfachmedikation",
      enterDrugs: "Medikamente eingeben",
      drugsPlaceholder: "z. B. aspirin, warfarin, ibuprofen",
      allergiesPlaceholder: "Allergien (optional)",
      conditionsPlaceholder: "Erkrankungen (optional)",
      checkButton: "Kombination analysieren",
      loading: "Interaktionsprofil wird analysiert...",
      noInteractions: "Keine bekannten paarweisen Interaktionen im aktuellen Datensatz",
      severity: "Gesamtschweregrad",
      interactions: "Interaktionen",
      sideEffects: "Uberlappende Nebenwirkungen",
      monitoringNotes: "Monitoring-Hinweise",
      warnings: "Warnhinweise",
      simpleExplanation: "Patienten-Erklarung",
      clinicalExplanation: "Klinische Erklarung",
      recommendations: "Empfehlungen",
      back: "Zuruck",
      requiredHint: "Bitte mindestens 2 Medikamente angeben.",
      footer: "Dieses Tool dient nur der Entscheidungsunterstutzung. Eine fachliche Prufung ist erforderlich.",
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
