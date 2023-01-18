"""Plotly figure builders. Every trace is computed from caller-supplied inputs."""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go


def power_triangle_figure(p_w: float, q_var: float, title: str = "AC Power Triangle") -> go.Figure:
    s = math.hypot(p_w, q_var)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, p_w, p_w, 0],
            y=[0, 0, q_var, 0],
            mode="lines+markers+text",
            text=["", f"P={p_w:.3g} W", f"S={s:.3g} VA", ""],
            textposition="top center",
            name="Power triangle",
        )
    )
    fig.add_trace(go.Scatter(x=[0, p_w], y=[0, q_var], mode="lines", name=f"Q={q_var:.3g} VAR", line={"dash": "dot"}))
    fig.update_layout(title=title, xaxis_title="Real power P (W)", yaxis_title="Reactive power Q (VAR)", showlegend=True)
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig


def voltage_drop_figure(
    *,
    system: str,
    voltage_v: float,
    current_a: float,
    resistance_ohm_per_km: float,
    reactance_ohm_per_km: float = 0.0,
    power_factor_value: float = 1.0,
    max_length_m: float = 500.0,
) -> go.Figure:
    from .calculators.voltage_drop import voltage_drop

    lengths = np.linspace(0, max_length_m, 50)
    drops = [
        voltage_drop(
            system=system,
            voltage_v=voltage_v,
            current_a=current_a,
            length_m=float(x),
            resistance_ohm_per_km=resistance_ohm_per_km,
            reactance_ohm_per_km=reactance_ohm_per_km,
            power_factor_value=power_factor_value,
        ).values["voltage_drop_percent"]
        for x in lengths
    ]
    fig = go.Figure(go.Scatter(x=lengths, y=drops, mode="lines", name="Voltage drop %"))
    fig.add_hline(y=5.0, line_dash="dash", annotation_text="5% threshold (configurable in calculator)")
    fig.update_layout(title="Voltage drop vs one-way conductor length", xaxis_title="One-way length (m)", yaxis_title="Voltage drop (%)")
    return fig


def energy_bar_figure(appliances: list[tuple[str, float]], unit_label: str = "kWh") -> go.Figure:
    names = [a[0] for a in appliances]
    vals = [a[1] for a in appliances]
    fig = go.Figure(go.Bar(x=names, y=vals, text=[f"{v:.3g}" for v in vals], textposition="outside"))
    fig.update_layout(title=f"Energy consumption by appliance ({unit_label})", xaxis_title="Appliance", yaxis_title=unit_label)
    return fig


def pf_correction_figure(p_w: float, pf_before: float, pf_after: float) -> go.Figure:
    def q(pf):
        return p_w * math.tan(math.acos(pf))

    cats = ["Before correction", "After correction"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cats, y=[pf_before, pf_after], name="Power factor"))
    fig.add_trace(go.Bar(x=cats, y=[q(pf_before) / 1000, q(pf_after) / 1000], name="Reactive power (kVAR)"))
    fig.update_layout(title="Power factor correction: before / after", barmode="group", yaxis_title="PF (bar 1) / kVAR (bar 2)")
    return fig


def efficiency_curve_figure(load_fraction_percent: list[float], efficiency_percent: list[float]) -> go.Figure:
    """Caller supplies the model points — used for transformer eta vs load (x^2 copper loss model)."""
    fig = go.Figure(go.Scatter(x=list(load_fraction_percent), y=list(efficiency_percent), mode="lines+markers"))
    fig.update_layout(title="Efficiency vs load", xaxis_title="Load (%)", yaxis_title="Efficiency (%)")
    return fig
