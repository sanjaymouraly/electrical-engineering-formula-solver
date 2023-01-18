import csv
import json

import pytest
from typer.testing import CliRunner

from ee_toolkit.batch import process_batch
from ee_toolkit.calculators import solve_ohms_law
from ee_toolkit.cli.main import app
from ee_toolkit.errors import EEError
from ee_toolkit.reports import result_to_csv, result_to_html, result_to_json, write_report

runner = CliRunner()


def test_cli_ohms_human_and_json():
    r = runner.invoke(app, ["ohms", "--voltage", "230", "--resistance", "46"])
    assert r.exit_code == 0 and "current_a = 5" in r.stdout
    rj = runner.invoke(app, ["ohms", "--voltage", "230", "--resistance", "46", "--json"])
    assert rj.exit_code == 0
    data = json.loads(rj.stdout)
    assert data["values"]["power_w"] == pytest.approx(1150)


@pytest.mark.parametrize(
    "args",
    [
        ["three-phase", "--voltage", "415", "--current", "20", "--pf", "0.85"],
        ["energy", "--power", "1500", "--hours", "8"],
        ["voltage-drop", "--voltage", "230", "--current", "20", "--length", "50", "--resistance", "1.2"],
        ["convert", "2.5", "kW", "W"],
        ["symbolic", "ohms_law", "R", "V=230", "I=5"],
        ["resistors", "series", "10", "20", "30"],
        ["efficiency", "--input", "1000", "--output", "850"],
    ],
)
def test_cli_commands_ok(args):
    r = runner.invoke(app, args)
    assert r.exit_code == 0, r.stdout


@pytest.mark.parametrize(
    "args",
    [
        ["ohms", "--voltage", "230", "--resistance", "0"],
        ["ohms", "--voltage", "230"],
        ["convert", "1", "V", "A"],
        ["three-phase", "--voltage", "415", "--current", "20", "--pf", "1.4"],
        ["symbolic", "ohms_law", "R", "V=abc", "I=5"],
        ["batch", "--input", "does_not_exist.csv", "--output", "out.csv"],
    ],
)
def test_cli_invalid_exit_2_no_traceback(args):
    r = runner.invoke(app, args)
    assert r.exit_code == 2
    assert "Error:" in (r.stderr or r.stdout)
    assert "Traceback" not in r.stdout


def test_batch_energy_with_bad_row(tmp_path):
    src = tmp_path / "in.csv"
    src.write_text("name,power_w,hours_per_day,duty_cycle\nHeater,2000,3,1.0\nBad,oops,2,1.0\nLamp,100,5,1.0\n")
    df = process_batch(src, kind="energy", tariff_per_kwh=0.15, days=30)
    assert list(df["status"]) == ["ok", "error", "ok"]
    heater = df.iloc[0]
    assert heater["energy_kwh"] == pytest.approx(2000 * 3 * 30 / 1000)
    assert heater["cost"] == pytest.approx(27.0)
    out = tmp_path / "out.csv"
    r = runner.invoke(app, ["batch", "--input", str(src), "--output", str(out)])
    assert r.exit_code == 0 and out.is_file()
    with out.open() as fh:
        rows = list(csv.DictReader(fh))
    assert rows[1]["status"] == "error"


def test_batch_missing_column_and_file():
    with pytest.raises(EEError):
        process_batch("nope.csv")
    p = "sample_data/appliances.csv"
    with pytest.raises(EEError):
        process_batch(p, kind="ohms")


def test_sample_data_batches_run():
    df = process_batch("sample_data/appliances.csv", kind="energy")
    assert (df["status"] == "ok").sum() >= 6  # malformed example row isolated, good rows succeed
    df2 = process_batch("sample_data/feeder_batch.csv", kind="voltage_drop")
    assert (df2["status"] == "ok").all()


def test_reports_and_injection_guard(tmp_path):
    res = solve_ohms_law(voltage_v=230, resistance_ohm=46)
    assert json.loads(result_to_json(res))["values"]["current_a"] == pytest.approx(5)
    html = result_to_html(res)
    assert "1150" in html and "&lt;" not in html.split("1150")[0][-20:]
    csv_text = result_to_csv(res)
    assert "current_a" in csv_text
    for _fmt, name in [("html", "r.html"), ("json", "r.json"), ("csv", "r.csv")]:
        p = write_report(res, tmp_path / name)
        assert p.is_file() and p.stat().st_size > 50
    # spreadsheet formula injection: a malicious category string is neutralised in CSV
    res2 = solve_ohms_law(voltage_v=230, resistance_ohm=46)
    res2.category = "=2+5+cmd|calc"
    assert any(line.startswith("'=") for line in result_to_csv(res2).splitlines()[1:])


def test_charts_are_data_driven():
    import plotly.graph_objects as go

    from ee_toolkit.charts import energy_bar_figure, power_triangle_figure, voltage_drop_figure

    fig = power_triangle_figure(1840, 1380)
    assert isinstance(fig, go.Figure) and len(fig.data) >= 1
    fig2 = voltage_drop_figure(system="single_phase", voltage_v=230, current_a=20, resistance_ohm_per_km=1.2, max_length_m=100)
    assert max(fig2.data[0].y) == pytest.approx(2 * 20 * 1.2 * 0.1 / 230 * 100, rel=0.05)  # at 100 m
    fig3 = energy_bar_figure([("A", 10.0), ("B", 5.0)])
    assert list(fig3.data[0].y) == [10.0, 5.0]
