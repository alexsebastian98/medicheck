import { useTranslation } from "react-i18next";
import type { SeverityLevel } from "../types/api";

interface SeverityIndicatorProps {
  severity: SeverityLevel;
}

const classes: Record<SeverityLevel, string> = {
  LOW: "severity-low",
  MODERATE: "severity-moderate",
  HIGH: "severity-high",
};

export function SeverityIndicator({ severity }: SeverityIndicatorProps) {
  const { t } = useTranslation();

  return (
    <div className={`severity ${classes[severity]}`}>
      <span>{t("severity")}</span>
      <strong>{severity}</strong>
    </div>
  );
}
