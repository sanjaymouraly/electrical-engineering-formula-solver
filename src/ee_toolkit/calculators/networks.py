"""Basic resistive network analysis (series source + series/parallel loads)."""

from __future__ import annotations

import math

from ..errors import InvalidInputError
from ..results import CalculationResult
from ..validation import positive
from .ohms import parallel_resistance, series_resistance


def resistive_load(*, voltage_v: float, resistance_ohm: float) -> CalculationResult:
    """Current and power drawn by a single resistive load."""
    v, r = positive("voltage_v", voltage_v), positive("resistance_ohm", resistance_ohm)
    i, p = v / r, v * v / r
    return CalculationResult(
        "resistive_load",
        {"voltage_v": v, "resistance_ohm": r, "current_a": i, "power_w": p},
        ["I = V/R", "P = V^2/R"],
        [f"I = {v:g}/{r:g} = {i:.6g} A", f"P = {p:.6g} W"],
        ["Purely resistive load (unity power factor)."],
        [],
    )


def series_parallel_network(*, source_v: float, series_ohm: float = 0.0, parallel_ohms: list[float] | None = None) -> CalculationResult:
    """Source -> optional series resistor -> parallel bank. Full branch results."""
    if parallel_ohms is None or len(parallel_ohms) == 0:
        raise InvalidInputError("Provide at least one parallel branch resistance.")
    r_par = parallel_resistance(parallel_ohms).values["equivalent_resistance_ohm"]
    r_total = float(series_ohm) + r_par
    if r_total <= 0:
        raise InvalidInputError("Total resistance must be > 0.")
    i_total = float(source_v) / r_total
    v_par = i_total * r_par
    values = {
        "source_voltage_v": float(source_v),
        "series_resistance_ohm": float(series_ohm),
        "parallel_equivalent_ohm": r_par,
        "total_resistance_ohm": r_total,
        "total_current_a": i_total,
        "parallel_voltage_v": v_par,
        "series_voltage_drop_v": i_total * float(series_ohm),
        "total_power_w": float(source_v) * i_total,
    }
    steps = [f"R_parallel = {r_par:.6g} ohm", f"I_total = {i_total:.6g} A", f"V_parallel = {v_par:.6g} V"]
    for i, r in enumerate(parallel_ohms, 1):
        values[f"branch_current_{i}_a"] = v_par / r
        steps.append(f"I_branch{i} = V_parallel/{r:g} = {v_par / r:.6g} A")
    if not math.isfinite(i_total):
        raise InvalidInputError("Non-finite network solution.")
    _ = series_resistance  # re-exported helper kept in the public module graph
    return CalculationResult(
        "series_parallel_network",
        values,
        ["R_eq(parallel) = 1/sum(1/Rk)", "I_total = V_s/(R_series + R_eq)", "I_branchk = V_parallel/Rk"],
        steps,
        ["DC resistive network, ideal voltage source."],
        [],
    )
