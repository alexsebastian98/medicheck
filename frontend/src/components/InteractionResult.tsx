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
        {data.interactions.length === 0 ? (
          <p>{t("noInteractions")}</p>
        ) : (
          <ul className="list">
            {data.interactions.map((item, index) => (
              <li key={`${item.drug_a}-${item.drug_b}-${index}`}>
                <strong>
                  {item.drug_a} + {item.drug_b} ({item.severity})
                </strong>
                <p>{item.description}</p>
                <small>{item.mechanism}</small>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="panel">
        <h3>{t("sideEffects")}</h3>
        <ul className="list">
          {data.overlapping_side_effects.map((effect) => (
            <li key={effect.effect}>
              <strong>{effect.effect}</strong>: {effect.drugs.join(", ")}
            </li>
          ))}
        </ul>
      </section>

      <WarningPanel warnings={data.warnings} />

      <section className="panel">
        <h3>{t("simpleExplanation")}</h3>
        <p>{data.explanations.simple}</p>
        <h3>{t("clinicalExplanation")}</h3>
        <p>{data.explanations.clinical}</p>
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
