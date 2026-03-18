import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

interface DrugInputBoxProps {
  onSubmit: (payload: {
    drugs: string[];
    allergies: string[];
    conditions: string[];
  }) => void;
  isLoading: boolean;
}

function toList(raw: string): string[] {
  return raw
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean)
    .filter((value, index, arr) => arr.indexOf(value) === index);
}

export function DrugInputBox({ onSubmit, isLoading }: DrugInputBoxProps) {
  const { t } = useTranslation();
  const [drugText, setDrugText] = useState("");
  const [allergyText, setAllergyText] = useState("");
  const [conditionText, setConditionText] = useState("");

  const drugs = useMemo(() => toList(drugText), [drugText]);
  const isValid = drugs.length >= 2 && drugs.length <= 5;

  return (
    <section className="panel">
      <h2>{t("enterDrugs")}</h2>
      <label>
        <textarea
          value={drugText}
          onChange={(event) => setDrugText(event.target.value)}
          placeholder={t("drugsPlaceholder")}
          rows={4}
        />
      </label>

      <label>
        <input
          type="text"
          value={allergyText}
          onChange={(event) => setAllergyText(event.target.value)}
          placeholder={t("allergiesPlaceholder")}
        />
      </label>

      <label>
        <input
          type="text"
          value={conditionText}
          onChange={(event) => setConditionText(event.target.value)}
          placeholder={t("conditionsPlaceholder")}
        />
      </label>

      <div className="chips">
        {drugs.map((drug) => (
          <span key={drug} className="chip">
            {drug}
          </span>
        ))}
      </div>

      {!isValid && <p className="hint">{t("requiredHint")}</p>}

      <button
        className="action"
        type="button"
        disabled={!isValid || isLoading}
        onClick={() =>
          onSubmit({
            drugs,
            allergies: toList(allergyText),
            conditions: toList(conditionText),
          })
        }
      >
        {isLoading ? t("loading") : t("checkButton")}
      </button>
    </section>
  );
}
