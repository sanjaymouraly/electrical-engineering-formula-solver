import math

import pytest

from ee_toolkit.calculators import power_factor_correction, single_phase_power, three_phase_efficiency, three_phase_power
from ee_toolkit.errors import EEError


def test_single_phase_known():
    v = single_phase_power(voltage_v=230, current_a=10, power_factor_value=0.8).values
    assert v["apparent_power_va"] == pytest.approx(2300)
    assert v["real_power_w"] == pytest.approx(1840)  # 2300*0.8
    assert v["reactive_power_var"] == pytest.approx(1380)  # 2300*0.6 (3-4-5 triangle)
    assert v["phase_angle_deg"] == pytest.approx(math.degrees(math.acos(0.8)))


def test_single_phase_leading_negative_q():
    v = single_phase_power(voltage_v=230, current_a=10, power_factor_value=0.8, pf_type="leading").values
    assert v["reactive_power_var"] == pytest.approx(-1380)
    assert v["phase_angle_deg"] < 0


def test_single_phase_from_p_and_pf():
    v = single_phase_power(power_w=1840, power_factor_value=0.8).values
    assert v["apparent_power_va"] == pytest.approx(2300)


def test_single_phase_no_pf_warns_not_fabricates():
    r = single_phase_power(voltage_v=230, current_a=10)
    assert r.values["apparent_power_va"] == pytest.approx(2300)
    assert "real_power_w" not in r.values and r.warnings


@pytest.mark.parametrize(
    "kw",
    [
        {"voltage_v": 230, "current_a": 10, "power_factor_value": 1.5},
        {"voltage_v": 230, "current_a": 10, "power_factor_value": 0},
        {"voltage_v": -230, "current_a": 10},
        {"voltage_v": 230},
    ],
)
def test_single_phase_invalid(kw):
    with pytest.raises(EEError):
        single_phase_power(**kw)


def test_three_phase_star_and_delta():
    s = three_phase_power(line_voltage_v=415, line_current_a=20, power_factor_value=0.85, connection="star").values
    assert s["apparent_power_va"] == pytest.approx(math.sqrt(3) * 415 * 20)
    assert s["real_power_w"] == pytest.approx(math.sqrt(3) * 415 * 20 * 0.85)
    assert s["phase_voltage_v"] == pytest.approx(415 / math.sqrt(3))
    assert s["phase_current_a"] == pytest.approx(20)
    d = three_phase_power(line_voltage_v=415, line_current_a=20, power_factor_value=0.85, connection="Delta").values
    assert d["phase_voltage_v"] == pytest.approx(415)
    assert d["phase_current_a"] == pytest.approx(20 / math.sqrt(3))
    assert d["real_power_w"] == pytest.approx(s["real_power_w"])  # same line quantities -> same total power


def test_three_phase_invalid_connection():
    with pytest.raises(EEError):
        three_phase_power(line_voltage_v=415, line_current_a=20, power_factor_value=0.9, connection="mesh")


def test_pf_correction_hand_calc():
    # 10 kW, 0.75 -> 0.95: tan(acos.75)=0.8819, tan(acos.95)=0.3287 => Qc=5532 VAR (independent calc)
    v = power_factor_correction(power_w=10000, current_pf=0.75, target_pf=0.95, voltage_v=230, frequency_hz=50).values
    expected_qc = 10000 * (math.tan(math.acos(0.75)) - math.tan(math.acos(0.95)))
    assert v["capacitor_reactive_power_var"] == pytest.approx(expected_qc, rel=1e-9)
    assert v["capacitor_reactive_power_var"] == pytest.approx(5532, rel=0.01)
    expected_c = expected_qc / (2 * math.pi * 50 * 230**2)
    assert v["capacitance_f"] == pytest.approx(expected_c, rel=1e-9)


def test_pf_correction_three_phase_capacitance_relation():
    v = power_factor_correction(power_w=10000, current_pf=0.75, target_pf=0.95, voltage_v=415, frequency_hz=50, phases=3).values
    # Star capacitors see VL/sqrt(3), so for the same per-phase VAR they need 3x the Delta capacitance.
    assert v["capacitance_per_phase_star_f"] == pytest.approx(3 * v["capacitance_per_phase_delta_f"], rel=1e-9)


@pytest.mark.parametrize(
    "kw",
    [
        {"power_w": 1000, "current_pf": 0.95, "target_pf": 0.75, "voltage_v": 230},  # target worse
        {"power_w": 1000, "current_pf": 1.2, "target_pf": 0.95, "voltage_v": 230},
        {"power_w": 1000, "current_pf": 0.8, "target_pf": 0.95, "voltage_v": 230, "phases": 2},
    ],
)
def test_pf_correction_invalid(kw):
    with pytest.raises(EEError):
        power_factor_correction(**kw)


def test_three_phase_efficiency():
    # Input = sqrt3*415*20*0.85 = 12219.6 W; output 11000 -> 90.02%
    v = three_phase_efficiency(output_power_w=11000, line_voltage_v=415, line_current_a=20, power_factor_value=0.85).values
    p_in = math.sqrt(3) * 415 * 20 * 0.85
    assert v["efficiency_percent"] == pytest.approx(11000 / p_in * 100)
    assert v["losses_w"] == pytest.approx(p_in - 11000)
    with pytest.raises(EEError):
        three_phase_efficiency(output_power_w=99999, line_voltage_v=415, line_current_a=20, power_factor_value=0.85)
