import math

import pytest

from ee_toolkit.calculators import compare_energy, efficiency, energy_cost, motor_input, transformer_efficiency, turns_ratio, voltage_drop
from ee_toolkit.errors import EEError


def test_voltage_drop_single_phase_textbook():
    v = voltage_drop(system="single_phase", voltage_v=230, current_a=20, length_m=50, resistance_ohm_per_km=1.2).values
    assert v["voltage_drop_v"] == pytest.approx(2 * 20 * 1.2 * 0.05)  # 2.4 V
    assert v["voltage_drop_percent"] == pytest.approx(2.4 / 230 * 100)
    assert v["receiving_voltage_v"] == pytest.approx(227.6)


def test_voltage_drop_dc_ignores_reactance_with_warning():
    r = voltage_drop(system="dc", voltage_v=48, current_a=10, length_m=20, resistance_ohm_per_km=2.0, reactance_ohm_per_km=0.5)
    assert r.values["voltage_drop_v"] == pytest.approx(2 * 10 * 2.0 * 0.02)
    assert r.warnings


def test_voltage_drop_three_phase_sqrt3_factor():
    v = voltage_drop(
        system="three_phase",
        voltage_v=400,
        current_a=32,
        length_m=100,
        resistance_ohm_per_km=0.9,
        reactance_ohm_per_km=0.08,
        power_factor_value=0.9,
    ).values
    sin = math.sqrt(1 - 0.9**2)
    expected = math.sqrt(3) * 32 * 0.1 * (0.9 * 0.9 + 0.08 * sin)
    assert v["voltage_drop_v"] == pytest.approx(expected)
    # three-phase line drop must NOT use the 2-conductor factor on the same data
    assert v["voltage_drop_v"] != pytest.approx(2 * 32 * 0.1 * (0.9 * 0.9 + 0.08 * sin))


def test_voltage_drop_threshold_warning():
    r = voltage_drop(
        system="single_phase", voltage_v=230, current_a=100, length_m=500, resistance_ohm_per_km=1.2, warn_threshold_percent=5.0
    )
    assert r.values["exceeds_threshold"] == 1.0 and r.warnings


def test_efficiency_known_and_impossible():
    v = efficiency(input_power_w=1000, output_power_w=850).values
    assert v["efficiency_percent"] == pytest.approx(85.0)
    assert v["losses_w"] == pytest.approx(150)
    assert efficiency(input_power_w=1000, efficiency_percent_value=85).values["output_power_w"] == pytest.approx(850)
    assert efficiency(output_power_w=850, efficiency_percent_value=85).values["input_power_w"] == pytest.approx(1000)
    with pytest.raises(EEError):
        efficiency(input_power_w=100, output_power_w=150)
    with pytest.raises(EEError):
        efficiency(input_power_w=100, efficiency_percent_value=101)
    with pytest.raises(EEError):
        efficiency(output_power_w=10, efficiency_percent_value=0)


def test_energy_hand_calc_and_money_rounding():
    v = energy_cost(power_w=1500, hours_per_day=8, days=30, tariff_per_kwh=0.15).values
    assert v["energy_kwh"] == pytest.approx(360.0)
    assert v["cost"] == pytest.approx(54.00)
    # 333 W * 1 h = 0.333 kWh * 0.15 = 0.04995 -> Decimal ROUND_HALF_UP to 0.05
    v2 = energy_cost(power_w=333, hours_per_day=1, days=1, tariff_per_kwh=0.15).values
    assert v2["cost"] == pytest.approx(0.05)


def test_energy_duty_and_validation():
    v = energy_cost(power_w=1000, hours_per_day=10, days=10, duty_cycle=0.5).values
    assert v["energy_kwh"] == pytest.approx(50.0)
    with pytest.raises(EEError):
        energy_cost(power_w=100, hours_per_day=25)
    with pytest.raises(EEError):
        energy_cost(power_w=100, hours_per_day=1, duty_cycle=1.5)


def test_compare_energy_savings():
    v = compare_energy(power_a_w=2000, power_b_w=1000, hours_per_day=2, days=365, tariff_per_kwh=0.2).values
    assert v["energy_saving_kwh"] == pytest.approx((2000 - 1000) * 2 * 365 / 1000)
    assert v["cost_saving"] == pytest.approx(v["energy_saving_kwh"] * 0.2, abs=0.01)


def test_transformer_ratio_and_efficiency():
    assert turns_ratio(primary_v=415, secondary_v=110).values["turns_ratio_np_over_ns"] == pytest.approx(415 / 110)
    v = transformer_efficiency(output_power_w=9000, core_loss_w=120, full_load_copper_loss_w=280, load_fraction=0.5).values
    assert v["copper_loss_w"] == pytest.approx(0.25 * 280)  # x^2 law
    assert v["efficiency_percent"] == pytest.approx(9000 / (9000 + 120 + 70) * 100)


def test_motor_distinguishes_pf_and_efficiency():
    # 3-ph input sqrt3*415*20*0.85=12219.6 W; at 90% eff shaft = 10997.7 W (PF is not efficiency)
    v = motor_input(phases=3, voltage_v=415, current_a=20, power_factor_value=0.85, efficiency_percent_value=90).values
    assert v["input_power_w"] == pytest.approx(math.sqrt(3) * 415 * 20 * 0.85)
    assert v["output_power_w"] == pytest.approx(math.sqrt(3) * 415 * 20 * 0.85 * 0.9)
