from app.schemas.interaction import (
    InteractionFinding,
    ModifierItem,
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
        modifiers: list[ModifierItem] | None = None,
    ) -> SeverityLevel:
        levels = [item.severity for item in interactions] + [warn.severity for warn in warnings]
        if not levels:
            return SeverityLevel.low

        base = max(levels, key=lambda level: self.severity_rank[level])
        if base == SeverityLevel.high:
            return SeverityLevel.high
        if not modifiers:
            return base

        base_score = self.score_for(base)
        modifier_delta = sum(item.severity_delta for item in modifiers)
        adjusted_score = max(0.0, min(1.0, base_score + modifier_delta))

        if adjusted_score >= self.severity_score[SeverityLevel.high]:
            return SeverityLevel.high
        if adjusted_score >= self.severity_score[SeverityLevel.moderate]:
            return SeverityLevel.moderate

        # Keep a minimum LOW signal when a real interaction exists.
        if interactions:
            return SeverityLevel.low
        return SeverityLevel.low

    def score_for(self, severity: SeverityLevel) -> float:
        return self.severity_score[severity]
