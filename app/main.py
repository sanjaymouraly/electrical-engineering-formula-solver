"""Streamlit dashboard for the Electrical Engineering Python Toolkit.

Run:  Streamlit run app/main.py
All calculations delegate to ee_toolkit (the same engine as the CLI).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ee_toolkit.calculators import (  # noqa: E402
    compare_energy,
    current_divider,
    efficiency,
    energy_cost,
    motor_input,
    parallel_resistance,
    power_factor_correction,
    series_resistance,
    single_phase_power,
    solve_ohms_law,
    solve_symbolic,
    three_phase_power,
    transformer_efficiency,
    turns_ratio,
    voltage_divider,
    voltage_drop,
)
from ee_toolkit.charts import (  # noqa: E402
    efficiency_curve_figure,
    energy_bar_figure,
    pf_correction_figure,
    power_triangle_figure,
    voltage_drop_figure,
)
from ee_toolkit.errors import EEError  # noqa: E402
from ee_toolkit.reports import result_to_csv, result_to_html, result_to_json  # noqa: E402
from ee_toolkit.units import SUPPORTED, convert  # noqa: E402

st.set_page_config(page_title="EE Formula Solver", page_icon="âš¡", layout="wide")
LIMITATION = "For learning and preliminary engineering analysis only â€” not certified electrical design or a substitute for qualified professional verification."

if "history" not in st.session_state:
    st.session_state.history = []


def show(result, *, chart=None) -> None:
    st.success(f"Calculated: {result.category}")
    cols = st.columns(min(len(result.values), 4) or 1)
    for i, (k, v) in enumerate(result.values.items()):
        cols[i % len(cols)].metric(k, f"{v:.4g}" if isinstance(v, float) else str(v))
    st.markdown("**Formulas:** " + " Â· ".join(f"`{f}`" for f in result.formulas))
    with st.expander("Step-by-step working", expanded=True):
        for s in result.steps:
            st.write("â€¢", s)
    with st.expander("Assumptions"):
        for a in result.assumptions:
            st.write("â€¢", a)
    for w in result.warnings:
        st.warning(w)
    if chart is not None:
        st.plotly_chart(chart, width='stretch')
    st.session_state.history.append(result)
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download HTML report", result_to_html(result), file_name=f"{result.category}.html", mime="text/html")
    c2.download_button("Download JSON", result_to_json(result), file_name=f"{result.category}.json", mime="application/json")
    c3.download_button("Download CSV", result_to_csv(result), file_name=f"{result.category}.csv", mime="text/csv")


def run(fn, chart_fn=None) -> None:
    try:
        result = fn()
        show(result, chart=chart_fn(result) if chart_fn else None)
    except EEError as exc:
        st.error(str(exc))
    except Exception as exc:  # surface, never hide, unexpected errors
        st.error(f"Unexpected error: {exc}")


st.title("âš¡ Electrical Engineering Formula Solver")
st.caption(LIMITATION)
page = st.sidebar.radio(
    "Calculator",
    [
        "Dashboard",
        "Ohm's Law & DC",
        "Resistors & Dividers",
        "Single-Phase AC",
        "Three-Phase AC",
        "Power Factor Correction",
        "Voltage Drop",
        "Efficiency & Motors",
        "Energy & Cost",
        "Transformer",
        "Unit Converter",
        "Symbolic Solver",
        "History",
    ],
)
st.sidebar.caption(LIMITATION)

if page == "Dashboard":
    st.markdown("### A validated, unit-aware electrical engineering toolkit")
    st.write(
        "Pick a calculator from the sidebar. Every result shows its formula, step-by-step working, assumptions, and warnings â€” and can be downloaded as an HTML/JSON/CSV report."
    )
    st.markdown("""
| Area | What you can do |
|---|---|
| Ohm's Law & DC | Solve V, I, R, P from any two; resistive loads |
| AC power | Single-phase & balanced three-phase power triangles, PF correction |
| Voltage drop | DC / 1-phase / 3-phase estimates with configurable warning threshold |
| Energy | kWh, running cost, device comparison and savings |
| Units & symbolic | Pint-backed conversions; SymPy rearrangement of approved formulas |
""")
    st.info("Worked example: a 230 V supply across 46 Î© draws 5 A and dissipates 1150 W â€” try it in Ohm's Law & DC.")
    sample = pd.DataFrame(
        {
            "Example": ["Heater", "3-ph motor", "Feeder"],
            "Result": ["230 V / 46 Î© â†’ 5 A, 1150 W", "415 V, 20 A, PF 0.85 â†’ 12.22 kW", "See Voltage Drop page"],
        }
    )
    st.dataframe(sample, width='stretch')

elif page == "Ohm's Law & DC":
    st.header("Ohm's Law & DC Power")
    st.latex(r"V = IR \qquad P = VI = I^2R = \frac{V^2}{R}")
    st.write("Enter any **two** values; leave the others at 0 to leave them blank.")
    V = st.number_input("Voltage (V)", min_value=0.0, value=230.0)
    I = st.number_input("Current (A)", min_value=0.0, value=0.0)
    R = st.number_input("Resistance (Î©)", min_value=0.0, value=46.0)
    P = st.number_input("Power (W)", min_value=0.0, value=0.0)
    if st.button("Calculate Ohm's law"):
        kw = {k: v for k, v in {"voltage_v": V, "current_a": I, "resistance_ohm": R, "power_w": P}.items() if v}
        run(lambda: solve_ohms_law(**kw))

elif page == "Resistors & Dividers":
    st.header("Series / Parallel Resistors & Dividers")
    text = st.text_input("Resistances (Î©), comma separated", "10, 20, 30")

    def parse():
        vals = [float(x) for x in text.replace(";", ",").split(",") if x.strip()]
        if not vals:
            raise EEError("Enter at least one resistance.")
        return vals

    c1, c2 = st.columns(2)
    if c1.button("Series equivalent"):
        run(lambda: series_resistance(parse()))
    if c2.button("Parallel equivalent"):
        run(lambda: parallel_resistance(parse()))
    st.subheader("Voltage divider")
    vs = st.number_input("Source voltage (V)", value=12.0)
    if st.button("Voltage across each resistor"):
        run(lambda: voltage_divider(source_v=vs, resistances=parse()))
    st.subheader("Current divider")
    it = st.number_input("Total current (A)", value=3.0)
    if st.button("Current in each branch"):
        run(lambda: current_divider(total_a=it, resistances=parse()))

elif page == "Single-Phase AC":
    st.header("Single-Phase AC Power")
    st.latex(r"S = VI \qquad P = S\cos\theta \qquad Q = S\sin\theta")
    V = st.number_input("RMS voltage (V)", min_value=0.0, value=230.0)
    I = st.number_input("RMS current (A)", min_value=0.0, value=10.0)
    pf = st.slider("Power factor", 0.05, 1.0, 0.8)
    kind = st.selectbox("PF type", ["lagging", "leading", "unity"])
    if st.button("Calculate single-phase power"):
        run(
            lambda: single_phase_power(voltage_v=V, current_a=I, power_factor_value=pf, pf_type=kind),
            lambda r: power_triangle_figure(r.values["real_power_w"], r.values["reactive_power_var"]),
        )

elif page == "Three-Phase AC":
    st.header("Balanced Three-Phase Power")
    st.latex(r"P = \sqrt{3}\,V_L I_L \,\mathrm{PF} \qquad S = \sqrt{3}\,V_L I_L")
    st.warning("Balanced loads only. Line and phase quantities are reported separately â€” never mix them.")
    VL = st.number_input("Line voltage V_L (V)", min_value=0.0, value=415.0)
    IL = st.number_input("Line current I_L (A)", min_value=0.0, value=20.0)
    pf = st.slider("Power factor", 0.05, 1.0, 0.85)
    kind = st.selectbox("PF type", ["lagging", "leading", "unity"])
    conn = st.selectbox("Connection (for phase quantities)", ["star", "Delta"])
    if st.button("Calculate three-phase power"):
        run(
            lambda: three_phase_power(line_voltage_v=VL, line_current_a=IL, power_factor_value=pf, pf_type=kind, connection=conn),
            lambda r: power_triangle_figure(r.values["real_power_w"], r.values["reactive_power_var"], "Three-Phase Power Triangle"),
        )

elif page == "Power Factor Correction":
    st.header("Power Factor Correction (capacitor sizing)")
    P = st.number_input("Real power (W)", min_value=0.0, value=10000.0)
    pf1 = st.slider("Current PF", 0.05, 1.0, 0.75)
    pf2 = st.slider("Target PF", 0.05, 1.0, 0.95)
    V = st.number_input("Voltage (V) â€” line voltage for 3-phase", min_value=0.0, value=230.0)
    f = st.number_input("Frequency (Hz)", min_value=1.0, value=50.0)
    phases = st.selectbox("Phases", [1, 3])
    if st.button("Size correction capacitor"):
        run(
            lambda: power_factor_correction(power_w=P, current_pf=pf1, target_pf=pf2, voltage_v=V, frequency_hz=f, phases=int(phases)),
            lambda r: pf_correction_figure(P, pf1, pf2),
        )

elif page == "Voltage Drop":
    st.header("Voltage Drop Calculator")
    st.write(
        "One-way route length. DC/single-phase use the 2-conductor loop; balanced three-phase uses âˆš3. Estimate only â€” not ampacity or compliance."
    )
    system = st.selectbox("System", ["dc", "single_phase", "three_phase"])
    V = st.number_input("Source voltage (V)", min_value=0.0, value=230.0)
    I = st.number_input("Current (A)", min_value=0.0, value=20.0)
    L = st.number_input("One-way length (m)", min_value=0.0, value=50.0)
    r = st.number_input("Resistance (Î©/km)", min_value=0.0, value=1.2)
    x = st.number_input("Reactance (Î©/km)", min_value=0.0, value=0.08)
    pf = st.slider("Power factor (AC)", 0.05, 1.0, 0.9)
    thr = st.number_input("Warning threshold (%)", min_value=0.1, value=5.0)
    if st.button("Calculate voltage drop"):
        run(
            lambda: voltage_drop(
                system=system,
                voltage_v=V,
                current_a=I,
                length_m=L,
                resistance_ohm_per_km=r,
                reactance_ohm_per_km=x,
                power_factor_value=pf,
                warn_threshold_percent=thr,
            ),
            lambda r_: voltage_drop_figure(
                system=system,
                voltage_v=V,
                current_a=I,
                resistance_ohm_per_km=r,
                reactance_ohm_per_km=x,
                power_factor_value=pf,
                max_length_m=max(L * 2, 100.0),
            ),
        )

elif page == "Efficiency & Motors":
    st.header("Efficiency, Losses & Motors")
    st.latex(r"\eta = \frac{P_{out}}{P_{in}}")
    mode = st.radio("Mode", ["Efficiency (any two)", "Motor input â†’ shaft output"])
    if mode.startswith("Efficiency"):
        pin = st.number_input("Input power (W) â€” 0 to leave blank", min_value=0.0, value=1000.0)
        pout = st.number_input("Output power (W) â€” 0 to leave blank", min_value=0.0, value=850.0)
        eff = st.number_input("Efficiency (%) â€” 0 to leave blank", min_value=0.0, max_value=100.0, value=0.0)
        if st.button("Calculate efficiency"):
            kw = {}
            if pin:
                kw["input_power_w"] = pin
            if pout:
                kw["output_power_w"] = pout
            if eff:
                kw["efficiency_percent_value"] = eff
            run(lambda: efficiency(**kw))
    else:
        phases = st.selectbox("Phases", [3, 1])
        V = st.number_input("Voltage (V) â€” line for 3-phase", min_value=0.0, value=415.0)
        I = st.number_input("Current (A) â€” line for 3-phase", min_value=0.0, value=20.0)
        pf = st.slider("Power factor", 0.05, 1.0, 0.85)
        eff = st.slider("Motor efficiency (%)", 1.0, 100.0, 90.0)
        if st.button("Calculate motor powers"):
            run(lambda: motor_input(phases=int(phases), voltage_v=V, current_a=I, power_factor_value=pf, efficiency_percent_value=eff))

elif page == "Energy & Cost":
    st.header("Energy Consumption & Cost")
    st.latex(r"E\,(\mathrm{kWh}) = \frac{P\,(\mathrm{W}) \times hours \times duty}{1000}")
    st.write("Assumptions: month = 30 days, year = 365 days, flat-rate tariff.")
    P = st.number_input("Power (W)", min_value=0.0, value=1500.0)
    h = st.number_input("Hours per day", min_value=0.0, max_value=24.0, value=8.0)
    days = st.number_input("Days", min_value=1.0, value=30.0)
    rate = st.number_input("Tariff per kWh", min_value=0.0, value=0.15)
    duty = st.slider("Duty cycle", 0.0, 1.0, 1.0)
    currency = st.text_input("Currency code", "USD")
    if st.button("Calculate energy & cost"):
        run(lambda: energy_cost(power_w=P, hours_per_day=h, days=days, tariff_per_kwh=rate, duty_cycle=duty, currency=currency))
    st.subheader("Compare two devices / estimate multi-appliance use")
    st.write("Enter appliances as `name, watts, hours/day` â€” one per line.")
    blob = st.text_area("Appliances", "Heater, 2000, 4\nLED lighting, 100, 6\nRefrigerator, 150, 24")
    rows, bad = [], []
    for line in blob.splitlines():
        if not line.strip():
            continue
        try:
            name, w, hh = [p.strip() for p in line.split(",")]
            rows.append((name, float(w), float(hh)))
        except Exception:
            bad.append(line)
    if bad:
        st.warning(f"Skipped malformed line(s): {bad}")
    if rows and st.button("Chart appliance energy (30 days)"):
        data = [(n, energy_cost(power_w=w, hours_per_day=hh, days=30, tariff_per_kwh=rate).values["energy_kwh"]) for n, w, hh in rows]
        st.plotly_chart(energy_bar_figure(data), width='stretch')
        st.dataframe(pd.DataFrame(data, columns=["Appliance", "Energy (kWh / 30 days)"]), width='stretch')
    st.subheader("Replacement savings")
    pa = st.number_input("Old device power (W)", min_value=0.0, value=2000.0)
    pb = st.number_input("New device power (W)", min_value=0.0, value=1200.0)
    if st.button("Calculate annual savings"):
        run(lambda: compare_energy(power_a_w=pa, power_b_w=pb, hours_per_day=h, days=365, tariff_per_kwh=rate, currency=currency))

elif page == "Transformer":
    st.header("Transformer: Turns Ratio & Efficiency")
    c1, c2, c3, c4 = st.columns(4)
    vp = c1.number_input("Primary V (0=blank)", min_value=0.0, value=415.0)
    vs = c2.number_input("Secondary V (0=blank)", min_value=0.0, value=0.0)
    np_ = c3.number_input("Primary turns (0=blank)", min_value=0.0, value=0.0)
    ns = c4.number_input("Secondary turns (0=blank)", min_value=0.0, value=0.0)
    if st.button("Calculate turns ratio"):
        kw = {k: v for k, v in {"primary_v": vp, "secondary_v": vs, "primary_turns": np_, "secondary_turns": ns}.items() if v}
        run(lambda: turns_ratio(**kw))
    st.subheader("Efficiency vs load (copper loss âˆ loadÂ²)")
    pout = st.number_input("Output power at chosen load (W)", min_value=0.0, value=9000.0)
    core = st.number_input("Core loss (W)", min_value=0.0, value=120.0)
    cu = st.number_input("Full-load copper loss (W)", min_value=0.0, value=280.0)
    lf = st.slider("Load fraction", 0.0, 1.5, 1.0)
    if st.button("Calculate transformer efficiency"):

        def chart(_r):
            loads = [i / 10 for i in range(1, 16)]
            effs = [
                transformer_efficiency(
                    output_power_w=pout * (x / lf if lf else 0), core_loss_w=core, full_load_copper_loss_w=cu, load_fraction=x
                ).values["efficiency_percent"]
                if lf
                else 0
                for x in loads
            ]
            return efficiency_curve_figure([x * 100 for x in loads], effs)

        run(lambda: transformer_efficiency(output_power_w=pout, core_loss_w=core, full_load_copper_loss_w=cu, load_fraction=lf), chart)

elif page == "Unit Converter":
    st.header("Unit Converter (Pint â€” dimensionally checked)")
    st.write("Supported: " + "; ".join(SUPPORTED))
    st.caption("Case matters: MW = megawatt, mW = milliwatt. Incompatible units are rejected.")
    val = st.number_input("Value", value=2.5)
    fu = st.text_input("From unit", "kW")
    tu = st.text_input("To unit", "W")
    if st.button("Convert"):
        try:
            out = convert(val, fu, tu)
            st.success(f"{val:g} {fu} = {out:.6g} {tu}")
            st.session_state.history.append({"category": "unit_conversion", "text": f"{val:g} {fu} = {out:.6g} {tu}"})
        except EEError as exc:
            st.error(str(exc))

elif page == "Symbolic Solver":
    st.header("Symbolic Formula Solver (SymPy, whitelisted)")
    st.write("Only approved equations can be rearranged â€” arbitrary expressions are never evaluated.")
    from ee_toolkit.calculators.symbolic import list_equations

    eqs = list_equations()
    eq = st.selectbox("Equation", list(eqs), format_func=lambda k: f"{k}: {eqs[k]}")
    solve_for = st.text_input("Solve for (e.g. R)", "R")
    vals_text = st.text_input("Values, e.g. V=230, I=5", "V=230, I=5")
    if st.button("Solve symbolically"):

        def do():
            vals = {}
            for part in vals_text.split(","):
                if "=" in part:
                    k, v = part.split("=", 1)
                    vals[k.strip()] = float(v)
            return solve_symbolic(eq, solve_for.strip(), vals or None)

        run(do)

elif page == "History":
    st.header("Calculation history (this session)")
    st.write("History is kept only in memory for this browser session â€” nothing is uploaded or saved to disk unless you download a report.")
    if not st.session_state.history:
        st.info("No calculations yet this session.")
    for i, item in enumerate(reversed(st.session_state.history), 1):
        if hasattr(item, "category"):
            with st.expander(f"{i}. {item.category}"):
                st.json(item.to_dict())
                st.download_button(f"Download JSON #{i}", result_to_json(item), file_name=f"history_{i}.json", key=f"hist_{i}")
        else:
            st.write(f"{i}. {item.get('text', item)}")
    if st.button("Clear history"):
        st.session_state.history = []
        st.rerun()

