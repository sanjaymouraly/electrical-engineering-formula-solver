"""Transformer turns ratio and efficiency (ideal-ratio + loss model)."""

from __future__ import annotations

from ..errors import InvalidInputError
from ..results import CalculationResult
from ..validation import non_negative, positive


def turns_ratio(*, primary_v=None, secondary_v=None, primary_turns=None, secondary_turns=None, primary_current_a=None) -> CalculationResult:
    """Vp/Vs = Np/Ns; ideal transformer: Vs*Is = Vp*Ip (lossless assumption)."""
    supplied = [x for x in (primary_v, secondary_v, primary_turns, secondary_turns) if x is not None]
    if len(supplied) < 2:
        raise InvalidInputError("Provide at least two of primary/secondary voltage or turns.")
    ratio = None
    if primary_v is not None and secondary_v is not None:
        ratio = positive("primary_v", primary_v) / positive("secondary_v", secondary_v)
    elif primary_turns is not None and secondary_turns is not None:
        ratio = positive("primary_turns", primary_turns) / positive("secondary_turns", secondary_turns)
    if ratio is None:
        raise InvalidInputError("Provide a matching pair: (Vp, Vs) or (Np, Ns) to determine the ratio.")
    values: dict[str, float] = {"turns_ratio_np_over_ns": ratio}
    steps = [f"Np/Ns = Vp/Vs = {ratio:.6g}"]
    if primary_v is not None and secondary_v is None and primary_turns is not None and secondary_turns is not None:
        values["secondary_v"] = float(primary_v) / ratio
        steps.append(f"Vs = Vp / ratio = {values['secondary_v']:.6g} V")
    if secondary_v is not None and primary_v is None and primary_turns is not None and secondary_turns is not None:
        values["primary_v"] = float(secondary_v) * ratio
        steps.append(f"Vp = Vs * ratio = {values['primary_v']:.6g} V")
    if primary_v is not None:
        values["primary_v"] = float(primary_v)
    if secondary_v is not None:
        values["secondary_v"] = float(secondary_v)
    if primary_turns is not None:
        values["primary_turns"] = float(primary_turns)
    if secondary_turns is not None:
        values["secondary_turns"] = float(secondary_turns)
    if primary_current_a is not None and "secondary_v" in values and "primary_v" in values:
        ip = positive("primary_current_a", primary_current_a, allow_zero=True)
        values["primary_current_a"] = ip
        values["secondary_current_a"] = ip * values["primary_v"] / values["secondary_v"] if values["secondary_v"] else 0.0
        steps.append(f"Is = Ip * Vp/Vs = {values['secondary_current_a']:.6g} A (ideal, lossless)")
    return CalculationResult(
        "transformer_ratio",
        values,
        ["Vp/Vs = Np/Ns", "Vp*Ip = Vs*Is (ideal)"],
        steps,
        ["Ideal transformer ratio; real transformers have magnetising current, losses and regulation."],
        [],
    )


def transformer_efficiency(
    *, output_power_w: float, core_loss_w: float, full_load_copper_loss_w: float, load_fraction: float = 1.0
) -> CalculationResult:
    """eta = Pout / (Pout + core loss + x^2 * full-load copper loss)."""
    pout = non_negative("output_power_w", output_power_w)
    core = non_negative("core_loss_w", core_loss_w)
    cu_full = non_negative("full_load_copper_loss_w", full_load_copper_loss_w)
    x = float(load_fraction)
    if not (0.0 <= x <= 1.5):
        raise InvalidInputError("load_fraction must be in [0, 1.5] (1.0 = full load).")
    cu = (x**2) * cu_full
    losses = core + cu
    pin = pout + losses
    eta = (pout / pin * 100.0) if pin > 0 else 0.0
    return CalculationResult(
        "transformer_efficiency",
        {
            "output_power_w": pout,
            "core_loss_w": core,
            "copper_loss_w": cu,
            "losses_w": losses,
            "input_power_w": pin,
            "efficiency_percent": eta,
            "load_fraction": x,
        },
        ["P_cu(x) = x^2 * P_cu(full load)", "eta = P_out / (P_out + P_core + P_cu)"],
        [f"Copper loss at x={x:g}: {cu:.6g} W", f"eta = {eta:.4f}%"],
        [
            "Core (iron) loss assumed constant; copper loss varies with the square of load fraction.",
            "Output power should already reflect the load fraction chosen.",
        ],
        [],
    )


def motor_input(
    *, phases: int, voltage_v: float, current_a: float, power_factor_value: float, efficiency_percent_value: float
) -> CalculationResult:
    """Motor electrical input, shaft output, and losses (1-phase or balanced 3-phase)."""
    from .ac import single_phase_power, three_phase_power
    from .efficiency import efficiency as eff_calc

    if phases == 1:
        elec = single_phase_power(voltage_v=voltage_v, current_a=current_a, power_factor_value=power_factor_value)
    elif phases == 3:
        elec = three_phase_power(line_voltage_v=voltage_v, line_current_a=current_a, power_factor_value=power_factor_value)
    else:
        raise InvalidInputError("phases must be 1 or 3.")
    p_in = elec.values["real_power_w"]
    out = eff_calc(input_power_w=p_in, efficiency_percent_value=efficiency_percent_value)
    values = {**elec.values, **out.values}
    return CalculationResult(
        "motor",
        values,
        ["P_in (3-ph) = sqrt(3)*V_L*I_L*PF  /  P_in (1-ph) = V*I*PF", "P_shaft = eta * P_in", "P_loss = P_in - P_shaft"],
        elec.steps + out.steps,
        [
            "Motor efficiency is nameplate/rated efficiency at the operating point.",
            "Power factor and efficiency are different quantities and are both required.",
        ],
        [],
    )
