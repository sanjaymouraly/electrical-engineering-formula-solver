import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ee_toolkit.calculators import solve_symbolic
from ee_toolkit.errors import EEError
from ee_toolkit.units import convert, parse_quantity


@pytest.mark.parametrize(
    "value,src,dst,expected",
    [
        (1, "kW", "W", 1000),
        (1, "MW", "W", 1_000_000),
        (1, "mW", "W", 0.001),  # case matters
        (230, "V", "kV", 0.23),
        (1500, "mA", "A", 1.5),
        (2, "kohm", "ohm", 2000),
        (1, "megaohm", "kohm", 1000),
        (1, "kWh", "Wh", 1000),
        (1, "MWh", "kWh", 1000),
        (3, "kVA", "VA", 3000),
        (500, "VAR", "kVAR", 0.5),
        (100, "cm", "m", 1.0),
        (2, "hour", "minute", 120),
        (1, "uF", "F", 1e-6),
        (60, "Hz", "Hz", 60),
    ],
)
def test_convert_known(value, src, dst, expected):
    assert convert(value, src, dst) == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize("src,dst", [("V", "A"), ("W", "V"), ("kWh", "A"), ("ohm", "W"), ("m", "s")])
def test_convert_incompatible_rejected(src, dst):
    with pytest.raises(EEError):
        convert(1, src, dst)


def test_convert_unknown_unit():
    with pytest.raises(EEError):
        convert(1, "furlong", "W")


def test_parse_quantity():
    mag, unit = parse_quantity("2.5 kW")
    assert mag == pytest.approx(2.5) and "kilowatt" in unit
    with pytest.raises(EEError):
        parse_quantity("__import__('os')")  # never evaluated
    with pytest.raises(EEError):
        parse_quantity("hello")


@settings(max_examples=40, deadline=None)
@given(v=st.floats(min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False))
def test_kw_w_roundtrip_property(v):
    assert convert(convert(v, "kW", "W"), "W", "kW") == pytest.approx(v, rel=1e-9)


def test_symbolic_rearrangements():
    r = solve_symbolic("ohms_law", "R", {"V": 230, "I": 5})
    assert r.values["R"] == pytest.approx(46)
    assert any("R = V/I" in s for s in r.steps)
    r2 = solve_symbolic("three_phase_power", "I_L", {"P": 12219.618, "V_L": 415, "PF": 0.85})
    assert r2.values["I_L"] == pytest.approx(20, rel=1e-5)
    r3 = solve_symbolic("ohms_law", "R")  # symbolic only
    assert r3.values == {} and r3.warnings


@pytest.mark.parametrize(
    "eq,for_,vals",
    [
        ("ohms_law", "X", {"V": 1}),
        ("eval_hack", "R", {}),
        ("ohms_law", "R", {"V": 230}),  # missing I
        ("ohms_law", "R", {"V": 230, "I": 5, "Z": 1}),  # unknown variable
        ("ac_real_power", "PF", {"P": 5000, "S": 4000}),  # PF > 1 impossible
    ],
)
def test_symbolic_rejected(eq, for_, vals):
    with pytest.raises(EEError):
        solve_symbolic(eq, for_, vals)
