from app.schemas.interaction import (
    InteractionFinding,
    SeverityLevel,
    WarningItem,
)


class SeverityEngine:
    """Rule-based severity evaluation with deterministic output for auditability."""

    severity_rank = {
        SeverityLevel.low: 1,
        SeverityLevel.moderate: 2,
        SeverityLevel.high: 3,
    }

    severity_score = {
        SeverityLevel.low: 0.2,
        SeverityLevel.moderate: 0.6,
        SeverityLevel.high: 0.9,
    }

    def derive_overall(
        self,
        interactions: list[InteractionFinding],
        warnings: list[WarningItem],
    ) -> SeverityLevel:
        levels = [item.severity for item in interactions] + [warn.severity for warn in warnings]
        if not levels:
            return SeverityLevel.low
        return max(levels, key=lambda level: self.severity_rank[level])

    def score_for(self, severity: SeverityLevel) -> float:
        return self.severity_score[severity]
