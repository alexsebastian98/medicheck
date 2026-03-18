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
  drug_a: string;
  drug_b: string;
  severity: SeverityLevel;
  mechanism: string;
  description: string;
  source: string;
}

export interface SideEffectAggregate {
  effect: string;
  drugs: string[];
  frequency_hint?: string | null;
}

export interface WarningItem {
  type: string;
  message: string;
  severity: SeverityLevel;
}

export interface ExplanationBlock {
  simple: string;
  clinical: string;
}

export interface CheckInteractionsResponse {
  request_id: string;
  timestamp: string;
  language: SupportedLanguage;
  normalized_drugs: DrugMatch[];
  overall_severity: SeverityLevel;
  interactions: InteractionFinding[];
  overlapping_side_effects: SideEffectAggregate[];
  warnings: WarningItem[];
  explanations: ExplanationBlock;
  recommendations: string[];
}
