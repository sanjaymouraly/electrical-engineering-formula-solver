"""Streamlit UI smoke tests using Streamlit's official AppTest framework."""

import pytest

pytest.importorskip("streamlit")

from pathlib import Path

APP = str(Path(__file__).resolve().parents[2] / "app" / "main.py")


def _run(page=None):
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    if page:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception
    return at


def test_dashboard_loads():
    at = _run()
    assert any("Formula Solver" in t.value for t in at.title)


@pytest.mark.parametrize(
    "page,needle",
    [
        ("Ohm's Law & DC", "Calculated: ohms_law"),
        ("Three-Phase AC", "Calculated: three_phase_ac"),
        ("Voltage Drop", "Calculated: voltage_drop"),
        ("Energy & Cost", "Calculated: energy_cost"),
    ],
)
def test_calculator_pages_calculate(page, needle):
    at = _run(page)
    assert at.button, f"no button on {page}"
    at.button[0].click().run()
    assert not at.exception
    assert any(needle in s.value for s in at.success), [s.value for s in at.success]


def test_unit_converter_page():
    at = _run("Unit Converter")
    at.button[0].click().run()
    assert not at.exception
    assert any("2500" in s.value for s in at.success)


def test_history_page_loads():
    at = _run("Ohm's Law & DC")
    at.button[0].click().run()
    at.sidebar.radio[0].set_value("History").run()
    assert not at.exception
