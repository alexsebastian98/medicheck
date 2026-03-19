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
        <h3>{t("interactions")}</h3>
        {data.primary_interaction ? (
          <p>
            <strong>{t("primaryInteraction")}:</strong> {data.primary_interaction.drug_a} +{" "}
            {data.primary_interaction.drug_b} ({data.primary_interaction.severity})
          </p>
        ) : null}
        {data.risk_summary ? <p>{data.risk_summary}</p> : null}
        {data.interactions.length === 0 ? (
          <p>{t("noInteractions")}</p>
        ) : (
          <ul className="list">
            {data.interactions.map((item) => (
              <li key={item.id}>
                <strong>
                  {item.drug_a} + {item.drug_b} ({item.severity})
                </strong>
                <p>ID: {item.id} | Score: {item.severity_score.toFixed(2)}</p>
                <p>{item.description}</p>
                <small>{item.mechanism}</small>
              </li>
            ))}
          </ul>
        )}
        {data.modifiers && data.modifiers.length > 0 ? (
          <>
            <h4>{t("modifiers")}</h4>
            <ul className="list">
              {data.modifiers.map((modifier, index) => (
                <li key={`${modifier.drug}-${index}`}>
                  <strong>{modifier.drug}</strong>: {modifier.effect}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>

      <section className="panel">
        <h3>{t("sideEffects")}</h3>
        <ul className="list">
          {data.overlapping_side_effects.map((effect) => (
            <li key={effect.id}>
              <strong>{effect.side_effect}</strong>: {effect.drugs.join(", ")}
              <div>ID: {effect.id} | Score: {effect.severity_score.toFixed(2)}</div>
            </li>
          ))}
        </ul>
      </section>

      <WarningPanel warnings={data.warnings} />

      <section className="panel">
        <h3>{t("monitoringNotes")}</h3>
        <ul className="list">
          {data.monitoring_notes.map((note, index) => (
            <li key={`${note}-${index}`}>{note}</li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h3>{t("simpleExplanation")}</h3>
        <p>{data.patient_explanation}</p>
        <h3>{t("clinicalExplanation")}</h3>
        <p>{data.clinical_explanation}</p>
      </section>

      <section className="panel">
        <h3>{t("recommendations")}</h3>
        <ul className="list">
          {data.recommendations.map((recommendation, index) => (
            <li key={index}>{recommendation}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
