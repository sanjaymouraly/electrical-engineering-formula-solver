"""Efficiency, losses, and required input/output power."""

from __future__ import annotations

from ..errors import InvalidInputError
from ..results import CalculationResult
from ..validation import efficiency_percent, positive


def efficiency(*, input_power_w=None, output_power_w=None, efficiency_percent_value=None) -> CalculationResult:
    """Solve eta = Pout/Pin. Supply any two of (Pin, Pout, eta%)."""
    supplied = sum(x is not None for x in (input_power_w, output_power_w, efficiency_percent_value))
    if supplied < 2:
        raise InvalidInputError("Provide at least two of input power, output power, and efficiency percent.")
    eta = efficiency_percent(efficiency_percent_value) / 100.0 if efficiency_percent_value is not None else None
    pin = positive("input_power_w", input_power_w) if input_power_w is not None else None
    pout = positive("output_power_w", output_power_w, allow_zero=True) if output_power_w is not None else None
    if pin is not None and pout is not None:
        if pout > pin:
            raise InvalidInputError(f"Output ({pout} W) cannot exceed input ({pin} W) for a passive device (efficiency > 100%).")
        eta_calc = pout / pin
        if eta is not None and abs(eta_calc - eta) > 1e-9:
            raise InvalidInputError(f"Inconsistent inputs: Pout/Pin = {eta_calc * 100:.4f}% but efficiency supplied as {eta * 100:.4f}%.")
        eta = eta_calc
    elif pin is not None and eta is not None:
        pout = pin * eta
    elif pout is not None and eta is not None:
        if eta == 0:
            raise InvalidInputError("Efficiency 0% with non-zero output would require infinite input power.")
        pin = pout / eta
    assert pin is not None and pout is not None and eta is not None  # noqa: S101
    losses = pin - pout
    return CalculationResult(
        "efficiency",
        {"input_power_w": pin, "output_power_w": pout, "efficiency_percent": eta * 100.0, "efficiency_fraction": eta, "losses_w": losses},
        ["eta = P_out / P_in", "P_loss = P_in - P_out", "P_in = P_out / eta"],
        [f"eta = {eta * 100:.4f}%", f"P_loss = {losses:.6g} W"],
        ["Efficiency is the ratio of useful output to input power; it is unrelated to power factor."],
        [],
    )
