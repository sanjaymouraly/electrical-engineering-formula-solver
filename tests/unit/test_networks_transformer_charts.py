import math

import pytest
from typer.testing import CliRunner

from ee_toolkit.batch import process_batch
from ee_toolkit.calculators import resistive_load, series_parallel_network, turns_ratio
from ee_toolkit.calculators.transformer import transformer_efficiency
from ee_toolkit.charts import efficiency_curve_figure, pf_correction_figure
from ee_toolkit.cli.main import app
from ee_toolkit.errors import EEError

runner = CliRunner()


def test_resistive_load():
    v = resistive_load(voltage_v=230, resistance_ohm=46).values
    assert v["current_a"] == pytest.approx(5) and v["power_w"] == pytest.approx(1150)


def test_series_parallel_network_branches_sum():
    # 10 ohm series + (20 || 20)=10 ohm -> total 20 ohm, I=1.2A at 24V, Vpar=12V, branches 0.6A each
    v = series_parallel_network(source_v=24, series_ohm=10, parallel_ohms=[20, 20]).values
    assert v["total_current_a"] == pytest.approx(1.2)
    assert v["branch_current_1_a"] + v["branch_current_2_a"] == pytest.approx(v["total_current_a"])
    assert v["parallel_voltage_v"] == pytest.approx(12)


def test_network_invalid():
    with pytest.raises(EEError):
        series_parallel_network(source_v=24, parallel_ohms=[])
    with pytest.raises(EEError):
        series_parallel_network(source_v=24, series_ohm=-30, parallel_ohms=[10])


def test_turns_ratio_variants():
    v = turns_ratio(primary_v=230, primary_turns=1000, secondary_turns=100).values
    assert v["turns_ratio_np_over_ns"] == pytest.approx(10)
    v2 = turns_ratio(secondary_v=24, primary_turns=1000, secondary_turns=100).values
    assert v2["primary_v"] == pytest.approx(240)
    v3 = turns_ratio(primary_v=415, secondary_v=110, primary_current_a=10).values
    assert v3["secondary_current_a"] == pytest.approx(10 * 415 / 110)
    with pytest.raises(EEError):
        turns_ratio(primary_v=230)
    with pytest.raises(EEError):
        turns_ratio(primary_v=230, secondary_turns=100)  # no matching pair
    with pytest.raises(EEError):
        transformer_efficiency(output_power_w=100, core_loss_w=10, full_load_copper_loss_w=10, load_fraction=2)


def test_charts_pf_and_efficiency():
    fig = pf_correction_figure(10000, 0.75, 0.95)
    assert len(fig.data) == 2
    assert fig.data[1].y[0] == pytest.approx(10000 * math.tan(math.acos(0.75)) / 1000)
    fig2 = efficiency_curve_figure([50, 100], [90.0, 93.0])
    assert list(fig2.data[0].y) == [90.0, 93.0]


def test_batch_ohms_and_voltage_drop(tmp_path):
    p = tmp_path / "o.csv"
    p.write_text("name,voltage_v,resistance_ohm\nA,230,46\nB,230,-1\n")
    df = process_batch(p, kind="ohms")
    assert df.iloc[0]["power_w"] == pytest.approx(1150) and df.iloc[1]["status"] == "error"
    p2 = tmp_path / "v.csv"
    p2.write_text("name,voltage_v,current_a,length_m,resistance_ohm_per_km\nF,230,20,50,1.2\n")
    df2 = process_batch(p2, kind="voltage_drop")
    assert df2.iloc[0]["voltage_drop_v"] == pytest.approx(2.4)
    with pytest.raises(EEError):
        process_batch(p, kind="bogus")


@pytest.mark.parametrize(
    "args",
    [
        ["voltage-drop", "--help"],
        ["batch", "--help"],
        ["--help"],
        ["compare", "--power-a", "2000", "--power-b", "1000", "--hours", "2"],
        ["divider", "voltage", "12", "10", "20"],
        ["divider", "current", "3", "10", "20"],
        ["pf-correction", "--power", "10000", "--current-pf", "0.75", "--target-pf", "0.95", "--voltage", "230"],
        ["transformer", "--primary-v", "415", "--secondary-v", "110"],
        ["transformer-efficiency", "--output", "9000", "--core-loss", "120", "--copper-loss", "280"],
        ["equations"],
        ["single-phase", "--voltage", "230", "--current", "10", "--pf", "0.8", "--json"],
    ],
)
def test_cli_more_commands(args):
    r = runner.invoke(app, args)
    assert r.exit_code == 0, r.stdout


def test_cli_bad_divider_and_symbolic_format():
    assert runner.invoke(app, ["divider", "bogus", "12", "10"]).exit_code == 2
    assert runner.invoke(app, ["resistors", "bogus", "10"]).exit_code == 2
    assert runner.invoke(app, ["symbolic", "ohms_law", "R", "V230"]).exit_code == 2
