export type SupportedLanguage = "en" | "de";

export type SeverityLevel = "LOW" | "MODERATE" | "HIGH";

export interface CheckInteractionsRequest {
  drugs: string[];
  allergies: string[];
  conditions: string[];
  lang: SupportedLanguage;
}

export interface DrugMatch {
  input_name: string;
  normalized_name: string;
  rxnorm_id?: string | null;
}

export interface InteractionFinding {
  id: string;
  drug_a: string;
  drug_b: string;
  severity: SeverityLevel;
  severity_score: number;
  risk_type?: string;
  mechanism: string;
  description: string;
  source: string;
}

export interface ModifierItem {
  type: string;
  drug: string;
  effect: string;
  applies_to: string[];
  severity_delta: number;
}

export interface SideEffectAggregate {
  id: string;
  side_effect: string;
  drugs: string[];
  severity_score: number;
  frequency_hint?: string | null;
}

export interface WarningItem {
  type: string;
  message: string;
  severity: SeverityLevel;
}

export interface CheckInteractionsResponse {
  request_id: string;
  timestamp: string;
  language: SupportedLanguage;
  normalized_drugs: DrugMatch[];
  overall_severity: SeverityLevel;
  overall_severity_score: number;
  interactions: InteractionFinding[];
  primary_interaction?: InteractionFinding | null;
  secondary_interactions?: InteractionFinding[];
  modifiers?: ModifierItem[];
  risk_summary?: string;
  risk_types?: string[];
  overlapping_side_effects: SideEffectAggregate[];
  monitoring_notes: string[];
  warnings: WarningItem[];
  patient_explanation: string;
  clinical_explanation: string;
  recommendations: string[];
}
