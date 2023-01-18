"""Energy consumption and electricity cost.

Period assumptions (explicit): week = 7 days, month = 30 days, year = 365 days.
Money uses Decimal quantised to cents to avoid binary-float currency errors.
Tariffs are flat-rate unless the caller supplies tiered usage separately.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ..errors import InvalidInputError
from ..results import CalculationResult
from ..validation import non_negative, positive

DAYS = {"daily": 1.0, "weekly": 7.0, "monthly": 30.0, "annual": 365.0}
CENT = Decimal("0.01")


def _money(value: Decimal) -> float:
    return float(value.quantize(CENT, rounding=ROUND_HALF_UP))


def energy_cost(
    *,
    power_w: float,
    hours_per_day: float,
    days: float = 30.0,
    tariff_per_kwh: float = 0.15,
    duty_cycle: float = 1.0,
    currency: str = "USD",
) -> CalculationResult:
    """Energy and cost for one load over ``days`` days at ``hours_per_day``."""
    p = non_negative("power_w", power_w)
    h = float(hours_per_day)
    if not (0.0 <= h <= 24.0):
        raise InvalidInputError("hours_per_day must be in [0, 24].")
    d = positive("days", days)
    duty = float(duty_cycle)
    if not (0.0 <= duty <= 1.0):
        raise InvalidInputError("duty_cycle must be a fraction in [0, 1] (e.g. 0.5 = runs 50% of the stated hours).")
    tariff = Decimal(str(tariff_per_kwh))
    if tariff < 0:
        raise InvalidInputError("tariff_per_kwh must be >= 0.")
    kwh_per_day = p * h * duty / 1000.0
    kwh = kwh_per_day * d
    cost = _money(Decimal(str(kwh)) * tariff)
    values = {
        "power_w": p,
        "hours_per_day": h,
        "days": d,
        "energy_kwh": kwh,
        "energy_kwh_per_day": kwh_per_day,
        "energy_wh": kwh * 1000.0,
        "cost": cost,
        "tariff_per_kwh": float(tariff),
        "duty_cycle": duty,
    }
    steps = [
        f"E_day = {p:g} W * {h:g} h * {duty:g} / 1000 = {kwh_per_day:.6g} kWh/day",
        f"E = E_day * {d:g} days = {kwh:.6g} kWh",
        f"Cost = {kwh:.6g} kWh * {tariff} {currency}/kWh = {cost:.2f} {currency}",
    ]
    return CalculationResult(
        "energy_cost",
        values,
        ["E(kWh) = P(W) * hours * duty / 1000", "Cost = E * tariff"],
        steps,
        [
            "Flat-rate tariff (no tiers, taxes, or standing charges).",
            f"Period = {d:g} days (month assumed 30 days, year 365 days).",
            f"Currency: {currency}. Money rounded to cents (Decimal, ROUND_HALF_UP).",
        ],
        [],
    )


def compare_energy(
    *,
    name_a: str = "Device A",
    power_a_w: float,
    name_b: str = "Device B",
    power_b_w: float,
    hours_per_day: float,
    days: float = 365.0,
    tariff_per_kwh: float = 0.15,
    currency: str = "USD",
) -> CalculationResult:
    """Annual-style comparison and savings from replacing A with B."""
    a = energy_cost(power_w=power_a_w, hours_per_day=hours_per_day, days=days, tariff_per_kwh=tariff_per_kwh, currency=currency).values
    b = energy_cost(power_w=power_b_w, hours_per_day=hours_per_day, days=days, tariff_per_kwh=tariff_per_kwh, currency=currency).values
    savings = _money(Decimal(str(a["cost"])) - Decimal(str(b["cost"])))
    values = {
        "a_energy_kwh": a["energy_kwh"],
        "b_energy_kwh": b["energy_kwh"],
        "a_cost": a["cost"],
        "b_cost": b["cost"],
        "energy_saving_kwh": a["energy_kwh"] - b["energy_kwh"],
        "cost_saving": savings,
        "days": float(days),
    }
    steps = [
        f"{name_a}: {a['energy_kwh']:.4f} kWh, cost {a['cost']:.2f} {currency}",
        f"{name_b}: {b['energy_kwh']:.4f} kWh, cost {b['cost']:.2f} {currency}",
        f"Saving (A - B) = {values['energy_saving_kwh']:.4f} kWh, {savings:.2f} {currency} (negative means B costs more)",
    ]
    return CalculationResult(
        "energy_comparison",
        values,
        ["E = P*h*days/1000", "Saving = cost_A - cost_B"],
        steps,
        ["Both devices used for the same hours/day and days.", "Flat-rate tariff."],
        [],
    )
