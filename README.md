# Electrical Engineering Formula Solver

A command-line toolkit for solving common electrical engineering formulas, with worked steps and unit checks.

## Features

- Ohm's law & DC: solve any two of V/I/R/P, series & parallel resistors, voltage/current dividers, resistive loads, series–parallel networks.
- AC power: single-phase and balanced three-phase power (star/Delta phase quantities reported separately), signed reactive power (lagging/leading), power triangles.
- Power-factor correction: capacitor sizing (single-phase capacitance; three-phase per-phase star and Delta bank values).
- Voltage drop: DC, single-phase, and balanced three-phase estimates with configurable % warning threshold and receiving-end voltage.
- Efficiency & machines: efficiency/losses, motor input→shaft power, transformer turns ratio and load-dependent transformer efficiency.
- Energy & cost: kWh, duty cycles, multi-appliance comparison, replacement savings, Decimal-safe money.
- Units: Pint-backed conversion (mV/V/kV, mA/A/kA, Ω/kΩ/MΩ, W/kW/MW, VA/kVA/MVA, VAR/kVAR, Wh/kWh/MWh, length, time, Hz, capacitance). Incompatible units are rejected; case matters (MW ≠ mW).

## Stack

Python, NumPy, pandas, Typer

## Clone

```bash
git clone https://github.com/sanjaymouraly/electrical-engineering-formula-solver.git
cd electrical-engineering-formula-solver
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[app,dev]"
```

## Run

```bash
streamlit run app/main.py
ee-toolkit --help
```

## Tests

```bash
pytest -q
```

## Notes

- Sample data, when included, is synthetic.

## License

MIT © 2023 [Sanjay Mouraly](https://github.com/sanjaymouraly)
