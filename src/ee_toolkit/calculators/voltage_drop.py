"""Voltage-drop estimates (approximate, preliminary — NOT conductor sizing).

Model (stated explicitly):
* ``length_m`` is the ONE-WAY conductor (route) length.
* DC / single-phase: the loop has two conductors, factor 2:
  DC: Vd = 2 * I * r * L ;  1-phase AC: Vd = 2 * I * L * (r*cos(phi) + x*sin(phi))
* Balanced three-phase (line-voltage drop): Vd = sqrt(3) * I * L * (r*cos(phi) + x*sin(phi))
* r, x are per-unit-length values in ohm per unit selected by ``per`` ('km' default, or 'm').
This is the standard approximate AC voltage-drop formula (neglects the small
quadrature term). It does NOT check ampacity, thermal limits, protection, or
code compliance.
"""

from __future__ import annotations

import math

from ..errors import InvalidInputError
from ..results import CalculationResult
from ..validation import non_negative, positive, power_factor

SQRT3 = math.sqrt(3.0)


def voltage_drop(
    *,
    system: str,
    voltage_v: float,
    current_a: float,
    length_m: float,
    resistance_ohm_per_km: float,
    reactance_ohm_per_km: float = 0.0,
    power_factor_value: float = 1.0,
    per: str = "km",
    warn_threshold_percent: float = 5.0,
) -> CalculationResult:
    sys_norm = system.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "dc": "dc",
        "single_phase": "single_phase",
        "1_phase": "single_phase",
        "1ph": "single_phase",
        "three_phase": "three_phase",
        "3_phase": "three_phase",
        "3ph": "three_phase",
    }
    if sys_norm not in aliases:
        raise InvalidInputError("system must be 'dc', 'single_phase', or 'three_phase'.")
    sys_norm = aliases[sys_norm]
    V = positive("voltage_v", voltage_v)
    I = non_negative("current_a", current_a)
    L = non_negative("length_m", length_m)
    r = non_negative("resistance_ohm_per_km", resistance_ohm_per_km)
    x = non_negative("reactance_ohm_per_km", reactance_ohm_per_km)
    threshold = positive("warn_threshold_percent", warn_threshold_percent)
    if per not in {"km", "m"}:
        raise InvalidInputError("per must be 'km' (ohm/km) or 'm' (ohm/m).")
    scale = L / 1000.0 if per == "km" else L  # length in the same unit as r/x
    pf = power_factor(power_factor_value, allow_zero=True)
    warnings: list[str] = []
    if sys_norm == "dc":
        vd = 2.0 * I * r * scale
        formula = "Vd = 2 * I * r * L (go + return conductors)"
        if x != 0.0:
            warnings.append("Reactance has no effect in DC and was ignored.")
        if pf != 1.0:
            warnings.append("Power factor does not apply to DC and was ignored.")
    else:
        sin_phi = math.sqrt(max(1.0 - pf * pf, 0.0))
        z_term = r * pf + x * sin_phi
        factor = 2.0 if sys_norm == "single_phase" else SQRT3
        vd = factor * I * z_term * scale
        formula = (
            f"Vd = {'2' if sys_norm == 'single_phase' else 'sqrt(3)'} * I * L * (r*cos(phi) + x*sin(phi)) "
            f"({'two-conductor loop' if sys_norm == 'single_phase' else 'balanced three-phase line drop'})"
        )
    pct = vd / V * 100.0
    v_recv = V - vd
    if pct > threshold:
        warnings.append(f"Voltage drop {pct:.2f}% exceeds the configured {threshold:g}% threshold.")
    if v_recv < 0:
        warnings.append(
            "Estimated drop exceeds source voltage: receiving-end voltage would be negative under this linear model — inputs are outside the useful range of the approximation."
        )
    values = {
        "source_voltage_v": V,
        "current_a": I,
        "one_way_length_m": L,
        "voltage_drop_v": vd,
        "voltage_drop_percent": pct,
        "receiving_voltage_v": v_recv,
        "warn_threshold_percent": threshold,
        "exceeds_threshold": 1.0 if pct > threshold else 0.0,
    }
    steps = [formula, f"Vd = {vd:.6g} V", f"Vd% = Vd/V * 100 = {pct:.4f}%", f"V_receiving = V - Vd = {v_recv:.6g} V"]
    return CalculationResult(
        "voltage_drop",
        values,
        [formula, "Vd% = 100 * Vd / V", "V_receiving = V - Vd"],
        steps,
        [
            f"length_m is the one-way route length; {'two-conductor loop' if sys_norm != 'three_phase' else 'balanced three-phase'} model.",
            f"r/x are given in ohm/{per}.",
            "Approximate AC drop formula (quadrature term neglected).",
            "Estimate only: NOT an ampacity, thermal, protection, or code-compliance check.",
        ],
        warnings,
    )
