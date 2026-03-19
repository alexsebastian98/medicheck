import { useTranslation } from "react-i18next";
import type { CheckInteractionsResponse } from "../types/api";
import { SeverityIndicator } from "./SeverityIndicator";
import { WarningPanel } from "./WarningPanel";

interface InteractionResultProps {
  data: CheckInteractionsResponse;
}

export function InteractionResult({ data }: InteractionResultProps) {
  const { t } = useTranslation();

  return (
    <div className="results-grid">
      <section className="panel">
        <SeverityIndicator severity={data.overall_severity} />
      </section>

      <section className="panel">
        <h3 className="section-title">{t("interactions")}</h3>
        {data.primary_interaction ? (
          <p className="primary-highlight">
            <strong>{t("primaryInteraction")}:</strong> {data.primary_interaction.drug_a} +{" "}
            {data.primary_interaction.drug_b} ({data.primary_interaction.severity})
          </p>
        ) : null}
        {data.risk_summary ? <p className="risk-summary">{data.risk_summary}</p> : null}
        {data.risk_types && data.risk_types.length > 0 ? (
          <p className="risk-summary">
            <strong>{t("riskTypes")}:</strong> {data.risk_types.join(", ")}
          </p>
        ) : null}
        {data.interactions.length === 0 ? (
          <p>{t("noInteractions")}</p>
        ) : (
          <ul className="list">
            {data.interactions.map((item) => (
              <li key={item.id} className="list-card">
                <strong>
                  {item.drug_a} + {item.drug_b} ({item.severity})
                </strong>
                {item.risk_type ? <p>Risk type: {item.risk_type}</p> : null}
                <p>ID: {item.id} | Score: {item.severity_score.toFixed(2)}</p>
                <p>{item.description}</p>
                <small>{item.mechanism}</small>
              </li>
            ))}
          </ul>
        )}
        {data.modifiers && data.modifiers.length > 0 ? (
          <>
            <h4 className="subsection-title">{t("modifiers")}</h4>
            <ul className="list">
              {data.modifiers.map((modifier, index) => (
                <li key={`${modifier.drug}-${index}`} className="list-card modifier-item">
                  <strong>{modifier.drug}</strong>: {modifier.effect}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>

      <section className="panel">
        <h3 className="section-title">{t("sideEffects")}</h3>
        <ul className="list">
          {data.overlapping_side_effects.map((effect) => (
            <li key={effect.id} className="list-card">
              <strong>{effect.side_effect}</strong>: {effect.drugs.join(", ")}
              <div>ID: {effect.id} | Score: {effect.severity_score.toFixed(2)}</div>
            </li>
          ))}
        </ul>
      </section>

      <WarningPanel warnings={data.warnings} />

      <section className="panel">
        <h3 className="section-title">{t("monitoringNotes")}</h3>
        <ul className="list">
          {data.monitoring_notes.map((note, index) => (
            <li key={`${note}-${index}`} className="list-card">
              {note}
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h3 className="section-title">{t("simpleExplanation")}</h3>
        <p className="explanation-text">{data.patient_explanation}</p>
        <h3 className="section-title section-title-tight">{t("clinicalExplanation")}</h3>
        <p className="explanation-text">{data.clinical_explanation}</p>
      </section>

      <section className="panel">
        <h3 className="section-title">{t("recommendations")}</h3>
        <ul className="list">
          {data.recommendations.map((recommendation, index) => (
            <li key={index} className="list-card">
              {recommendation}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
