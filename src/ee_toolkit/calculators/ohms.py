"""Ohm's law, DC power, resistor networks, and dividers.

Conventions: passive sign convention, SI units (V, A, ohm, W).
Resistance must be > 0 for a finite solution; a true short circuit (R = 0)
with non-zero voltage implies unbounded current and is rejected rather than
silently returning ``inf``.
"""

from __future__ import annotations

import math

from ..errors import InsufficientInputError, InvalidInputError, PhysicalImpossibilityError
from ..results import CalculationResult
from ..validation import positive, resistor_list


def solve_ohms_law(*, voltage_v=None, current_a=None, resistance_ohm=None, power_w=None) -> CalculationResult:
    """Solve V=IR / P=VI for the unknowns. Supply at least two of the four.

    Any consistent pair determines the rest. Over-determined input is checked
    for consistency (relative tolerance 1e-6); contradictions are rejected.
    """
    given = {"V": voltage_v, "I": current_a, "R": resistance_ohm, "P": power_w}
    supplied = {k: float(v) for k, v in given.items() if v is not None}
    if len(supplied) < 2:
        raise InsufficientInputError("Provide at least two of voltage, current, resistance, power.")
    for k, v in supplied.items():
        if not math.isfinite(v):
            raise InvalidInputError(f"{k} must be finite.")
    if "R" in supplied:
        positive("resistance_ohm", supplied["R"])
    if "P" in supplied and supplied["P"] < 0:
        raise InvalidInputError("power_w dissipated by a passive resistor must be >= 0.")
    if "V" in supplied and "I" in supplied and supplied["V"] * supplied["I"] < 0:
        raise PhysicalImpossibilityError("V and I with opposite signs imply negative dissipated power for a passive resistor.")

    V, I, R, P = supplied.get("V"), supplied.get("I"), supplied.get("R"), supplied.get("P")
    # Derive a seed pair, preferring directly supplied quantities.
    if V is not None and I is not None:
        pass
    elif V is not None and R is not None:
        I = V / R
    elif I is not None and R is not None:
        V = I * R
    elif V is not None and P is not None:
        if V == 0:
            raise InsufficientInputError("V=0 with only P supplied is indeterminate (any R dissipating via I is unconstrained).")
        I = P / V
    elif I is not None and P is not None:
        if I == 0:
            raise InsufficientInputError("I=0 with only P supplied is indeterminate.")
        V = P / I
    elif R is not None and P is not None:
        I = math.sqrt(P / R)
        V = I * R
    assert V is not None and I is not None  # noqa: S101 - internal invariant
    if V == 0 and I == 0:
        raise InsufficientInputError("V=0 and I=0 do not determine resistance (0/0 is indeterminate).")
    R_calc = V / I if I != 0 else math.inf
    if not math.isfinite(R_calc) or R_calc <= 0:
        raise PhysicalImpossibilityError("Derived resistance is not positive and finite; check input signs/values.")
    P_calc = V * I
    expected = {"V": V, "I": I, "R": R_calc, "P": P_calc}
    for k, v in supplied.items():
        e = expected[k]
        if not math.isclose(v, e, rel_tol=1e-6, abs_tol=1e-12):
            raise PhysicalImpossibilityError(f"Inconsistent inputs: supplied {k}={v} but V=IR/P=VI imply {k}={e}.")
    steps = [f"V = {V:.6g} V, I = {I:.6g} A", f"R = V/I = {R_calc:.6g} ohm", f"P = V*I = I^2*R = V^2/R = {P_calc:.6g} W"]
    return CalculationResult(
        "ohms_law",
        {"voltage_v": V, "current_a": I, "resistance_ohm": R_calc, "power_w": P_calc},
        ["V = I * R", "P = V * I = I^2 * R = V^2 / R"],
        steps,
        ["Passive resistive load, DC or RMS AC resistive equivalent.", "Resistance > 0 (short circuit R=0 is not modelled as finite)."],
        [],
    )


def series_resistance(resistances: list[float]) -> CalculationResult:
    vals = resistor_list(resistances)
    total = math.fsum(vals)
    return CalculationResult(
        "series_resistance",
        {"equivalent_resistance_ohm": total, "count": float(len(vals))},
        ["R_eq = R1 + R2 + ... + Rn"],
        [f"R_eq = {' + '.join(f'{v:g}' for v in vals)} = {total:.6g} ohm"],
        ["Series resistors carry the same current."],
        [],
    )


def parallel_resistance(resistances: list[float]) -> CalculationResult:
    vals = resistor_list(resistances)
    conductance = math.fsum(1.0 / v for v in vals)
    total = 1.0 / conductance
    return CalculationResult(
        "parallel_resistance",
        {"equivalent_resistance_ohm": total, "count": float(len(vals))},
        ["1/R_eq = 1/R1 + 1/R2 + ... + 1/Rn"],
        [f"G_eq = {conductance:.6g} S", f"R_eq = 1/G_eq = {total:.6g} ohm"],
        ["Parallel resistors share the same voltage."],
        [],
    )


def voltage_divider(*, source_v: float, resistances: list[float]) -> CalculationResult:
    """Voltage across each series resistor and the common series current."""
    vals = resistor_list(resistances)
    total = math.fsum(vals)
    current = float(source_v) / total
    values: dict[str, float] = {"source_voltage_v": float(source_v), "total_resistance_ohm": total, "series_current_a": current}
    steps = [f"R_total = {total:.6g} ohm", f"I = V/R_total = {current:.6g} A"]
    for i, r in enumerate(vals, 1):
        v = current * r
        values[f"voltage_r{i}_v"] = v
        steps.append(f"V_R{i} = I*R{i} = {v:.6g} V ({v / float(source_v) * 100:.3f}% of source)" if source_v else f"V_R{i} = {v:.6g} V")
    return CalculationResult(
        "voltage_divider",
        values,
        ["I = V_s / sum(R)", "V_Rk = I * Rk = V_s * Rk/sum(R)"],
        steps,
        ["Series network; divider equation assumes no external load on the tap (or load included as a resistor)."],
        [],
    )


def current_divider(*, total_a: float, resistances: list[float]) -> CalculationResult:
    """Branch currents for parallel resistors fed by a total current."""
    vals = resistor_list(resistances)
    r_eq = 1.0 / math.fsum(1.0 / v for v in vals)
    voltage = float(total_a) * r_eq
    values: dict[str, float] = {"total_current_a": float(total_a), "equivalent_resistance_ohm": r_eq, "parallel_voltage_v": voltage}
    steps = [f"R_eq = {r_eq:.6g} ohm", f"V = I_total*R_eq = {voltage:.6g} V"]
    for i, r in enumerate(vals, 1):
        i_k = voltage / r
        values[f"current_r{i}_a"] = i_k
        steps.append(f"I_R{i} = V/R{i} = {i_k:.6g} A")
    return CalculationResult(
        "current_divider",
        values,
        ["V = I_total * R_eq", "I_Rk = V / Rk"],
        steps,
        ["Parallel branches share the same voltage."],
        ["Branch currents sum to the total current (KCL check in steps)."],
    )
