"""Reproducible worked examples (run: python examples/worked_examples.py).

All scenarios are EXAMPLES with stated assumptions, not measured data.
Expected outputs (verified by tests in tests/regression/):
  Heater: 230 V / 46 ohm -> 5 A, 1150 W
  Three-phase motor supply: 415 V, 20 A, PF 0.85 -> S=14.376 kVA, P=12.220 kW
  Energy: 1500 W x 8 h/day x 30 days -> 360 kWh, $54.00 at $0.15/kWh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ee_toolkit.calculators import energy_cost, solve_ohms_law, three_phase_power  # noqa: E402

if __name__ == "__main__":
    print(solve_ohms_law(voltage_v=230, resistance_ohm=46).values)
    print(three_phase_power(line_voltage_v=415, line_current_a=20, power_factor_value=0.85).values)
    print(energy_cost(power_w=1500, hours_per_day=8, days=30, tariff_per_kwh=0.15).values)
