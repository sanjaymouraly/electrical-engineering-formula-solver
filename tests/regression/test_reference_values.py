"""Regression tests pinned to independently published/textbook-style values."""

import math

import pytest

from ee_toolkit.calculators import energy_cost, solve_ohms_law, three_phase_power


def test_reference_heater():
    # Any textbook: 230 V mains, 46 ohm element -> 5 A, 1150 W
    v = solve_ohms_law(voltage_v=230, resistance_ohm=46).values
    assert v["current_a"] == 5.0 and v["power_w"] == 1150.0


def test_reference_three_phase_motor_nameplate_style():
    # 415 V, 20 A, 0.85 PF industrial supply -> 12.22 kW (rounded nameplate-style)
    v = three_phase_power(line_voltage_v=415, line_current_a=20, power_factor_value=0.85).values
    assert v["real_power_w"] / 1000 == pytest.approx(12.22, abs=0.01)
    assert v["apparent_power_va"] / 1000 == pytest.approx(14.38, abs=0.01)


def test_reference_bill():
    # 1.5 kW heater, 8 h/day, 30-day month, $0.15/kWh -> $54.00
    v = energy_cost(power_w=1500, hours_per_day=8, days=30, tariff_per_kwh=0.15).values
    assert v["energy_kwh"] == 360.0 and v["cost"] == 54.0


def test_line_phase_never_mixed():
    # If line/phase were confused, phase voltage would equal 415 instead of 239.6
    v = three_phase_power(line_voltage_v=415, line_current_a=20, power_factor_value=0.85).values
    assert v["phase_voltage_v"] == pytest.approx(415 / math.sqrt(3))
    assert v["phase_voltage_v"] != pytest.approx(415)
