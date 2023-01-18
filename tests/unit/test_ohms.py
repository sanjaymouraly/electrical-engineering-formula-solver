import math

import pytest

from ee_toolkit.calculators import current_divider, parallel_resistance, series_resistance, solve_ohms_law, voltage_divider
from ee_toolkit.errors import EEError


@pytest.mark.parametrize(
    "kw,exp",
    [
        ({"voltage_v": 230, "resistance_ohm": 46}, (230, 5, 46, 1150)),  # textbook: 230/46=5
        ({"voltage_v": 12, "current_a": 2}, (12, 2, 6, 24)),
        ({"current_a": 3, "resistance_ohm": 10}, (30, 3, 10, 90)),
        ({"power_w": 100, "resistance_ohm": 25}, (50, 2, 25, 100)),  # I=sqrt(100/25)=2
        ({"power_w": 1150, "voltage_v": 230}, (230, 5, 46, 1150)),
        ({"power_w": 90, "current_a": 3}, (30, 3, 10, 90)),
    ],
)
def test_ohms_solve_any_pair(kw, exp):
    v = solve_ohms_law(**kw).values
    assert (v["voltage_v"], v["current_a"], v["resistance_ohm"], v["power_w"]) == pytest.approx(exp, rel=1e-9)


def test_ohms_consistent_overdetermined():
    v = solve_ohms_law(voltage_v=230, current_a=5, resistance_ohm=46, power_w=1150).values
    assert v["power_w"] == pytest.approx(1150)


def test_ohms_inconsistent_rejected():
    with pytest.raises(EEError):
        solve_ohms_law(voltage_v=230, current_a=5, resistance_ohm=10)  # 230/5=46 != 10


@pytest.mark.parametrize(
    "kw",
    [
        {"voltage_v": 230},
        {},
        {"voltage_v": 0, "current_a": 0},
        {"voltage_v": 230, "resistance_ohm": 0},  # short circuit: not finite
        {"voltage_v": 230, "resistance_ohm": -5},
        {"voltage_v": float("inf"), "resistance_ohm": 10},
        {"voltage_v": 10, "current_a": -2},  # passive sign violation -> negative R
    ],
)
def test_ohms_invalid(kw):
    with pytest.raises(EEError):
        solve_ohms_law(**kw)


def test_series_parallel_known_values():
    assert series_resistance([10, 20, 30]).values["equivalent_resistance_ohm"] == pytest.approx(60)
    # 10||20||30: conductance 0.1+0.05+1/30
    assert parallel_resistance([10, 20, 30]).values["equivalent_resistance_ohm"] == pytest.approx(1 / (0.1 + 0.05 + 1 / 30))
    assert parallel_resistance([100]).values["equivalent_resistance_ohm"] == pytest.approx(100)


@pytest.mark.parametrize("fn", [series_resistance, parallel_resistance])
def test_resistor_network_invalid(fn):
    with pytest.raises(EEError):
        fn([])
    with pytest.raises(EEError):
        fn([10, 0])


def test_voltage_divider():
    v = voltage_divider(source_v=12, resistances=[10, 20]).values
    assert v["series_current_a"] == pytest.approx(0.4)
    assert v["voltage_r1_v"] == pytest.approx(4.0)  # 12 * 10/30
    assert v["voltage_r2_v"] == pytest.approx(8.0)


def test_current_divider_kcl():
    v = current_divider(total_a=3, resistances=[10, 20]).values
    # V = 3 * (10||20)=3*6.666=20 V -> 2 A and 1 A
    assert v["current_r1_a"] == pytest.approx(2.0)
    assert v["current_r2_a"] == pytest.approx(1.0)
    assert v["current_r1_a"] + v["current_r2_a"] == pytest.approx(3.0)


def test_power_identities_randomised():
    # Property-style check with fixed independent algebra (not the implementation's path for P from R,I)
    for v, r in [(5, 3), (100, 7), (0.5, 0.25)]:
        out = solve_ohms_law(voltage_v=v, resistance_ohm=r).values
        assert out["power_w"] == pytest.approx(out["current_a"] ** 2 * r)
        assert out["power_w"] == pytest.approx(v * v / r)
        assert math.isfinite(out["power_w"])
