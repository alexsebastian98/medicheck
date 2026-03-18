import { useTranslation } from "react-i18next";
import type { WarningItem } from "../types/api";

interface WarningPanelProps {
  warnings: WarningItem[];
}

export function WarningPanel({ warnings }: WarningPanelProps) {
  const { t } = useTranslation();

  if (warnings.length === 0) {
    return null;
  }

  return (
    <section className="panel">
      <h3>{t("warnings")}</h3>
      <ul className="list">
        {warnings.map((warning, index) => (
          <li key={`${warning.type}-${index}`} className="warning-item">
            <strong>{warning.severity}</strong> {warning.message}
          </li>
        ))}
      </ul>
    </section>
  );
}
