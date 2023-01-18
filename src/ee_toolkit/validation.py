"""Centralised input validation. Every calculator routes checks through here."""

from __future__ import annotations

import math
from collections.abc import Iterable

from .errors import InvalidInputError, PhysicalImpossibilityError


def finite(name: str, value: float) -> float:
    v = float(value)
    if not math.isfinite(v):
        raise InvalidInputError(f"{name} must be a finite number, got {value!r}.")
    return v


def positive(name: str, value: float, *, allow_zero: bool = False) -> float:
    v = finite(name, value)
    if allow_zero and v < 0:
        raise InvalidInputError(f"{name} must be >= 0, got {v}.")
    if not allow_zero and v <= 0:
        raise InvalidInputError(f"{name} must be > 0, got {v}.")
    return v


def non_negative(name: str, value: float) -> float:
    return positive(name, value, allow_zero=True)


def power_factor(value: float, *, allow_zero: bool = False) -> float:
    """Power factor magnitude must lie in (0, 1] (0 allowed only if requested)."""
    v = finite("power_factor", value)
    lo_ok = v >= 0 if allow_zero else v > 0
    if not lo_ok or v > 1.0:
        raise PhysicalImpossibilityError(
            f"power_factor must be in {'[0, 1]' if allow_zero else '(0, 1]'}, got {v}. "
            "|PF| > 1 would imply more real power than apparent power."
        )
    return v


def efficiency_fraction(value: float) -> float:
    v = finite("efficiency", value)
    if not (0.0 <= v <= 1.0):
        raise PhysicalImpossibilityError(f"efficiency fraction must be in [0, 1], got {v}.")
    return v


def efficiency_percent(value: float) -> float:
    v = finite("efficiency_percent", value)
    if not (0.0 <= v <= 100.0):
        raise PhysicalImpossibilityError(
            f"efficiency_percent must be in [0, 100], got {v}. Values > 100% are physically impossible "
            "for a passive energy-conversion device."
        )
    return v


def resistor_list(values: Iterable[float]) -> list[float]:
    vals = [positive(f"resistance[{i}]", v) for i, v in enumerate(values)]
    if not vals:
        raise InvalidInputError("At least one resistor value is required.")
    return vals


def sign_convention(value: str) -> str:
    v = value.strip().lower()
    if v not in {"lagging", "leading", "unity"}:
        raise InvalidInputError("power factor type must be 'lagging', 'leading', or 'unity'.")
    return v
