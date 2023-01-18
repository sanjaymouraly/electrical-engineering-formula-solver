"""Structured calculation result shared by the library, CLI, UI and reports."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CalculationResult:
    """A transparent calculation outcome.

    ``values`` holds SI-base numeric results (keys document their unit, e.g.
    ``voltage_v``). ``steps``/``formulas`` make the working auditable and
    ``assumptions``/``warnings`` state the engineering model explicitly.
    """

    category: str
    values: dict[str, float]
    formulas: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "values": self.values,
            "formulas": self.formulas,
            "steps": self.steps,
            "assumptions": self.assumptions,
            "warnings": self.warnings,
        }
