"""Single-phase and balanced three-phase AC power.

Conventions (documented, consistent everywhere):
* Voltages/currents are RMS.
* P [W] real, Q [VAR] reactive (positive = inductive/lagging load absorbing
  VARs, negative = capacitive/leading), S [VA] apparent, S = sqrt(P^2+Q^2).
* PF magnitude in (0, 1]; angle theta = acos(PF), lagging => theta > 0.
* Three-phase formulas are for BALANCED loads only.
"""

from __future__ import annotations

import math

from ..errors import InvalidInputError
from ..results import CalculationResult
from ..validation import efficiency_fraction, positive, power_factor, sign_convention

SQRT3 = math.sqrt(3.0)


def _triangle(p_w: float, pf: float, kind: str) -> tuple[float, float, float, float]:
    """Return (S, Q signed, angle_deg, Q magnitude) from P and PF."""
    s = p_w / pf
    angle = math.degrees(math.acos(pf))
    q_mag = math.sqrt(max(s * s - p_w * p_w, 0.0))
    q = q_mag if kind == "lagging" else (-q_mag if kind == "leading" else 0.0)
    if kind == "unity":
        angle = 0.0
    return s, q, angle, q_mag


def single_phase_power(
    *, voltage_v=None, current_a=None, power_w=None, apparent_va=None, power_factor_value=None, pf_type: str = "lagging"
) -> CalculationResult:
    """Solve a single-phase AC power problem.

    Supply (V and I) optionally with PF, or P with PF, or S with PF, etc.
    At minimum a magnitude pair that determines S, plus PF if P/Q are needed.
    """
    kind = sign_convention(pf_type)
    pf = power_factor(power_factor_value) if power_factor_value is not None else None
    V = positive("voltage_v", voltage_v) if voltage_v is not None else None
    I = positive("current_a", current_a, allow_zero=True) if current_a is not None else None
    P = float(power_w) if power_w is not None else None
    S = positive("apparent_va", apparent_va, allow_zero=True) if apparent_va is not None else None
    if S is None and V is not None and I is not None:
        S = V * I
    if S is None and P is not None and pf is not None:
        S = abs(P) / pf
    if S is None:
        raise InvalidInputError("Provide V and I, or apparent power S, or P together with power factor.")
    if pf is None and P is not None and S > 0:
        pf = abs(P) / S
        power_factor(pf)
    if pf is None:
        # Only S determinable; return it with an explicit warning.
        values = {"apparent_power_va": S}
        if V is not None:
            values["voltage_v"] = V
        if I is not None:
            values["current_a"] = I
        return CalculationResult(
            "single_phase_ac",
            values,
            ["S = V * I"],
            [f"S = {S:.6g} VA"],
            ["RMS quantities."],
            ["Power factor not supplied: P, Q and phase angle cannot be determined from S alone."],
        )
    if P is None:
        P = S * pf
    S2, Q, angle, _ = _triangle(P, pf, kind)
    if not math.isclose(S2, S, rel_tol=1e-9, abs_tol=1e-12):
        S = S2
    if V is None and I is not None and I > 0:
        V = S / I
    if I is None and V is not None:
        I = S / V
    values = {
        "apparent_power_va": S,
        "real_power_w": P,
        "reactive_power_var": Q,
        "power_factor": pf,
        "phase_angle_deg": angle if kind != "leading" else -angle,
    }
    if V is not None:
        values["voltage_v"] = V
    if I is not None:
        values["current_a"] = I
    steps = [
        f"S = {S:.6g} VA",
        f"theta = acos({pf:g}) = {angle:.4f} deg",
        f"P = S*PF = {P:.6g} W",
        f"Q = {'+' if Q >= 0 else ''}{Q:.6g} VAR ({kind})",
    ]
    return CalculationResult(
        "single_phase_ac",
        values,
        ["S = V_rms * I_rms", "P = S * PF", "Q = S * sin(theta)", "S^2 = P^2 + Q^2", "theta = acos(PF)"],
        steps,
        ["RMS voltage/current.", "Q > 0 means lagging (inductive); Q < 0 means leading (capacitive)."],
        [],
    )


def three_phase_power(
    *,
    line_voltage_v=None,
    line_current_a=None,
    power_w=None,
    apparent_va=None,
    power_factor_value=None,
    pf_type: str = "lagging",
    connection: str = "star",
) -> CalculationResult:
    """Balanced three-phase power. Line quantities are the primary inputs."""
    kind, conn = sign_convention(pf_type), connection.strip().lower()
    if conn not in {"star", "delta", "y", "d"}:
        raise InvalidInputError("connection must be 'star' (Y) or 'Delta'.")
    conn = "star" if conn in {"star", "y"} else "delta"
    pf = power_factor(power_factor_value) if power_factor_value is not None else None
    VL = positive("line_voltage_v", line_voltage_v) if line_voltage_v is not None else None
    IL = positive("line_current_a", line_current_a, allow_zero=True) if line_current_a is not None else None
    P = float(power_w) if power_w is not None else None
    S = positive("apparent_va", apparent_va, allow_zero=True) if apparent_va is not None else None
    if S is None and VL is not None and IL is not None:
        S = SQRT3 * VL * IL
    if S is None and P is not None and pf is not None:
        S = abs(P) / pf
    if S is None:
        raise InvalidInputError("Provide line V and line I, or S, or P together with power factor.")
    if pf is None and P is not None and S > 0:
        pf = abs(P) / S
        power_factor(pf)
    if pf is None:
        values = {"apparent_power_va": S}
        if VL is not None:
            values["line_voltage_v"] = VL
        if IL is not None:
            values["line_current_a"] = IL
        return CalculationResult(
            "three_phase_ac",
            values,
            ["S = sqrt(3) * V_L * I_L"],
            [f"S = {S:.6g} VA"],
            ["Balanced three-phase load, RMS line quantities."],
            ["PF not supplied: P, Q and angle cannot be determined."],
        )
    if P is None:
        P = S * pf
    S2, Q, angle, _ = _triangle(P, pf, kind)
    S = S2
    if VL is None and IL is not None and IL > 0:
        VL = S / (SQRT3 * IL)
    if IL is None and VL is not None:
        IL = S / (SQRT3 * VL)
    assert VL is not None and IL is not None  # noqa: S101
    if conn == "star":
        v_ph, i_ph = VL / SQRT3, IL
    else:
        v_ph, i_ph = VL, IL / SQRT3
    values = {
        "line_voltage_v": VL,
        "line_current_a": IL,
        "phase_voltage_v": v_ph,
        "phase_current_a": i_ph,
        "apparent_power_va": S,
        "real_power_w": P,
        "reactive_power_var": Q,
        "power_factor": pf,
        "phase_angle_deg": angle if kind != "leading" else -angle,
    }
    steps = [
        f"S = sqrt(3)*{VL:.6g}*{IL:.6g} = {S:.6g} VA",
        f"P = S*PF = {P:.6g} W",
        f"Q = {'+' if Q >= 0 else ''}{Q:.6g} VAR ({kind})",
        f"{conn}: V_ph = {v_ph:.6g} V, I_ph = {i_ph:.6g} A",
    ]
    assumptions = [
        "BALANCED three-phase load only — do not apply to unbalanced loads.",
        "Star: V_L = sqrt(3)*V_ph, I_L = I_ph. Delta: V_L = V_ph, I_L = sqrt(3)*I_ph.",
        "RMS line quantities.",
    ]
    return CalculationResult(
        "three_phase_ac",
        values,
        ["S = sqrt(3) * V_L * I_L", "P = sqrt(3) * V_L * I_L * PF", "Q = sqrt(3) * V_L * I_L * sin(theta)"],
        steps,
        assumptions,
        [],
    )


def power_factor_correction(
    *,
    power_w: float,
    current_pf: float,
    target_pf: float,
    voltage_v: float,
    frequency_hz: float = 50.0,
    phases: int = 1,
    current_type: str = "lagging",
    target_type: str = "lagging",
) -> CalculationResult:
    """Capacitor sizing to correct lagging PF. Assumes constant real power P.

    Qc = P * (tan(theta1) - tan(theta2)); single-phase C = Qc / (2*pi*f*V^2).
    For three-phase, Qc is the total three-phase capacitor VAR; per-phase
    capacitance depends on the capacitor bank connection, so both star and
    Delta per-phase values are reported with the connection stated.
    """
    P = positive("power_w", power_w, allow_zero=True)
    pf1, pf2 = power_factor(current_pf), power_factor(target_pf)
    V, f = positive("voltage_v", voltage_v), positive("frequency_hz", frequency_hz)
    if phases not in (1, 3):
        raise InvalidInputError("phases must be 1 or 3.")
    if sign_convention(current_type) != "lagging":
        raise InvalidInputError(
            "This correction model assumes a lagging (inductive) load; leading loads need reactor, not capacitor, correction."
        )
    t_kind = sign_convention(target_type)
    tan1 = math.tan(math.acos(pf1))
    tan2 = math.tan(math.acos(pf2)) * (1 if t_kind == "lagging" else -1)
    qc = P * (tan1 - tan2)
    if qc < 0:
        raise InvalidInputError("Target power factor is lower (more lagging) than current PF; no capacitor correction applies.")
    values: dict[str, float] = {
        "real_power_w": P,
        "current_pf": pf1,
        "target_pf": pf2,
        "capacitor_reactive_power_var": qc,
        "capacitor_reactive_power_kvar": qc / 1000.0,
        "angle_before_deg": math.degrees(math.acos(pf1)),
        "angle_after_deg": math.degrees(math.acos(pf2)),
    }
    steps = [f"tan(theta1) = {tan1:.6g}, tan(theta2) = {tan2:.6g}", f"Qc = P*(tan1 - tan2) = {qc:.6g} VAR ({qc / 1000:.4f} kVAR)"]
    omega = 2 * math.pi * f
    if phases == 1:
        c = qc / (omega * V * V) if qc else 0.0
        values["capacitance_f"] = c
        values["capacitance_uf"] = c * 1e6
        steps.append(f"C = Qc/(2*pi*f*V^2) = {c:.6g} F ({c * 1e6:.3f} uF)")
    else:
        # Total Qc split across 3 capacitors. Delta: each sees V_L; Star: each sees V_L/sqrt(3).
        c_delta = (qc / 3.0) / (omega * V * V) if qc else 0.0
        c_star = (qc / 3.0) / (omega * (V / SQRT3) ** 2) if qc else 0.0
        values.update(
            {
                "capacitance_per_phase_delta_f": c_delta,
                "capacitance_per_phase_delta_uf": c_delta * 1e6,
                "capacitance_per_phase_star_f": c_star,
                "capacitance_per_phase_star_uf": c_star * 1e6,
            }
        )
        steps.append(f"Per-phase Delta C = {c_delta * 1e6:.3f} uF; per-phase star C = {c_star * 1e6:.3f} uF")
    return CalculationResult(
        "power_factor_correction",
        values,
        ["Qc = P * (tan(theta1) - tan(theta2))", "C = Qc / (2*pi*f*V^2) (per capacitor, at its own voltage)"],
        steps,
        [
            "Real power P stays constant during correction.",
            "Ideal (lossless) capacitors; practical banks are stepped/standard sizes.",
            "For three-phase, voltage_v is the LINE voltage; capacitor voltage depends on bank connection.",
        ],
        [],
    )


def three_phase_efficiency(
    *, output_power_w: float, line_voltage_v: float, line_current_a: float, power_factor_value: float
) -> CalculationResult:
    """Efficiency of a balanced three-phase machine from electrical input."""
    p_out = positive("output_power_w", output_power_w, allow_zero=True)
    res = three_phase_power(line_voltage_v=line_voltage_v, line_current_a=line_current_a, power_factor_value=power_factor_value)
    p_in = res.values["real_power_w"]
    if p_in <= 0:
        raise InvalidInputError("Electrical input power must be > 0 to compute efficiency.")
    eff = (
        efficiency_fraction(p_out / p_in)
        if p_out <= p_in
        else (_ for _ in ()).throw(
            InvalidInputError(f"Output ({p_out} W) exceeds electrical input ({p_in:.6g} W): efficiency would exceed 100%.")
        )
    )
    values = {
        **res.values,
        "output_power_w": p_out,
        "input_power_w": p_in,
        "efficiency_fraction": eff,
        "efficiency_percent": eff * 100.0,
        "losses_w": p_in - p_out,
    }
    return CalculationResult(
        "three_phase_efficiency",
        values,
        ["P_in = sqrt(3)*V_L*I_L*PF", "efficiency = P_out / P_in"],
        [f"P_in = {p_in:.6g} W", f"efficiency = {eff * 100:.4f}%", f"losses = {p_in - p_out:.6g} W"],
        ["Balanced three-phase input.", "Power factor is NOT efficiency: PF comes from phase shift, efficiency from losses."],
        [],
    )
