"""Typer CLI. All commands delegate to the same validated library used by the web UI.

Exit codes: 0 success, 2 invalid user input (message on stderr, no traceback).
"""

from __future__ import annotations

import json

import typer

from ..batch import batch_to_csv, process_batch
from ..calculators import (
    compare_energy,
    current_divider,
    efficiency,
    energy_cost,
    list_equations,
    parallel_resistance,
    power_factor_correction,
    series_resistance,
    single_phase_power,
    solve_ohms_law,
    solve_symbolic,
    three_phase_power,
    transformer_efficiency,
    turns_ratio,
    voltage_drop,
)
from ..errors import EEError
from ..reports import result_to_csv, result_to_json
from ..units import convert

app = typer.Typer(
    help="Electrical Engineering Formula Solver — validated EE calculations (learning / preliminary analysis only).", no_args_is_help=True
)


def _emit(result, as_json: bool, csv_out: bool = False) -> None:
    if as_json:
        typer.echo(result_to_json(result))
    elif csv_out:
        typer.echo(result_to_csv(result))
    else:
        typer.echo(f"[{result.category}]")
        for k, v in result.values.items():
            typer.echo(f"  {k} = {v:.6g}" if isinstance(v, float) else f"  {k} = {v}")
        for s in result.steps:
            typer.echo(f"  step: {s}")
        for w in result.warnings:
            typer.echo(f"  WARNING: {w}", err=True)


def _run(fn, as_json: bool) -> None:
    try:
        _emit(fn(), as_json)
    except EEError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


@app.command()
def ohms(
    voltage: float = typer.Option(None, "--voltage"),
    current: float = typer.Option(None, "--current"),
    resistance: float = typer.Option(None, "--resistance"),
    power: float = typer.Option(None, "--power"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Solve Ohm's law from any two of V, I, R, P. Example: ee-toolkit ohms --voltage 230 --resistance 46"""
    _run(lambda: solve_ohms_law(voltage_v=voltage, current_a=current, resistance_ohm=resistance, power_w=power), as_json)


@app.command("single-phase")
def single_phase(
    voltage: float = typer.Option(None, "--voltage"),
    current: float = typer.Option(None, "--current"),
    power: float = typer.Option(None, "--power"),
    apparent: float = typer.Option(None, "--apparent"),
    pf: float = typer.Option(None, "--pf"),
    pf_type: str = typer.Option("lagging", "--pf-type"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Single-phase AC power (RMS). ee-toolkit single-phase --voltage 230 --current 10 --pf 0.8"""
    _run(
        lambda: single_phase_power(
            voltage_v=voltage, current_a=current, power_w=power, apparent_va=apparent, power_factor_value=pf, pf_type=pf_type
        ),
        as_json,
    )


@app.command("three-phase")
def three_phase(
    voltage: float = typer.Option(None, "--voltage", help="Line voltage (V)"),
    current: float = typer.Option(None, "--current", help="Line current (A)"),
    power: float = typer.Option(None, "--power"),
    apparent: float = typer.Option(None, "--apparent"),
    pf: float = typer.Option(None, "--pf"),
    pf_type: str = typer.Option("lagging", "--pf-type"),
    connection: str = typer.Option("star", "--connection"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Balanced three-phase power. ee-toolkit three-phase --voltage 415 --current 20 --pf 0.85"""
    _run(
        lambda: three_phase_power(
            line_voltage_v=voltage,
            line_current_a=current,
            power_w=power,
            apparent_va=apparent,
            power_factor_value=pf,
            pf_type=pf_type,
            connection=connection,
        ),
        as_json,
    )


@app.command("voltage-drop")
def voltage_drop_cmd(
    system: str = typer.Option("single_phase", "--system", help="dc | single_phase | three_phase"),
    voltage: float = typer.Option(..., "--voltage"),
    current: float = typer.Option(..., "--current"),
    length: float = typer.Option(..., "--length", help="One-way length in metres"),
    resistance: float = typer.Option(..., "--resistance", help="ohm per km"),
    reactance: float = typer.Option(0.0, "--reactance", help="ohm per km"),
    pf: float = typer.Option(1.0, "--pf"),
    threshold: float = typer.Option(5.0, "--threshold"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Voltage-drop estimate. ee-toolkit voltage-drop --voltage 230 --current 20 --length 50 --resistance 1.2"""
    _run(
        lambda: voltage_drop(
            system=system,
            voltage_v=voltage,
            current_a=current,
            length_m=length,
            resistance_ohm_per_km=resistance,
            reactance_ohm_per_km=reactance,
            power_factor_value=pf,
            warn_threshold_percent=threshold,
        ),
        as_json,
    )


@app.command(name="efficiency")
def efficiency_cmd(
    input_power: float = typer.Option(None, "--input", help="Input power (W)"),
    output_power: float = typer.Option(None, "--output", help="Output power (W)"),
    percent: float = typer.Option(None, "--percent", help="Efficiency (%)"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Efficiency from any two of input, output, percent."""
    _run(lambda: efficiency(input_power_w=input_power, output_power_w=output_power, efficiency_percent_value=percent), as_json)


@app.command()
def energy(
    power: float = typer.Option(..., "--power", help="Power (W)"),
    hours: float = typer.Option(..., "--hours", help="Hours per day"),
    days: float = typer.Option(30.0, "--days"),
    rate: float = typer.Option(0.15, "--rate", help="Tariff per kWh"),
    duty: float = typer.Option(1.0, "--duty"),
    currency: str = typer.Option("USD", "--currency"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Energy + cost. ee-toolkit energy --power 1500 --hours 8 --rate 0.15"""
    _run(
        lambda: energy_cost(power_w=power, hours_per_day=hours, days=days, tariff_per_kwh=rate, duty_cycle=duty, currency=currency), as_json
    )


@app.command()
def compare(
    power_a: float = typer.Option(..., "--power-a"),
    power_b: float = typer.Option(..., "--power-b"),
    hours: float = typer.Option(..., "--hours"),
    days: float = typer.Option(365.0, "--days"),
    rate: float = typer.Option(0.15, "--rate"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Compare two devices' energy use and running cost."""
    _run(lambda: compare_energy(power_a_w=power_a, power_b_w=power_b, hours_per_day=hours, days=days, tariff_per_kwh=rate), as_json)


@app.command(name="convert")
def convert_cmd(
    value: float = typer.Argument(...),
    from_unit: str = typer.Argument(...),
    to_unit: str = typer.Argument(...),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Convert units, e.g. ee-toolkit convert 2.5 kW W"""
    try:
        out = convert(value, from_unit, to_unit)
    except EEError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(
        json.dumps({"value": value, "from": from_unit, "to": to_unit, "result": out})
        if as_json
        else f"{value:g} {from_unit} = {out:.6g} {to_unit}"
    )


@app.command()
def resistors(
    mode: str = typer.Argument(..., help="series | parallel"),
    values: list[float] = typer.Argument(...),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Equivalent resistance. ee-toolkit resistors series 10 20 30"""
    fn = series_resistance if mode == "series" else parallel_resistance if mode == "parallel" else None
    if fn is None:
        typer.echo("Error: mode must be 'series' or 'parallel'", err=True)
        raise typer.Exit(code=2)
    _run(lambda: fn(list(values)), as_json)


@app.command()
def divider(
    kind: str = typer.Argument(..., help="voltage | current"),
    value: float = typer.Argument(..., help="Source voltage (V) or total current (A)"),
    values: list[float] = typer.Argument(...),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Voltage/current divider for a resistor list."""
    from ..calculators import voltage_divider

    if kind == "voltage":
        _run(lambda: voltage_divider(source_v=value, resistances=list(values)), as_json)
    elif kind == "current":
        _run(lambda: current_divider(total_a=value, resistances=list(values)), as_json)
    else:
        typer.echo("Error: kind must be 'voltage' or 'current'", err=True)
        raise typer.Exit(code=2)


@app.command("pf-correction")
def pf_correction(
    power: float = typer.Option(..., "--power"),
    current_pf: float = typer.Option(..., "--current-pf"),
    target_pf: float = typer.Option(..., "--target-pf"),
    voltage: float = typer.Option(..., "--voltage"),
    frequency: float = typer.Option(50.0, "--frequency"),
    phases: int = typer.Option(1, "--phases"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Capacitor sizing for power-factor correction."""
    _run(
        lambda: power_factor_correction(
            power_w=power, current_pf=current_pf, target_pf=target_pf, voltage_v=voltage, frequency_hz=frequency, phases=phases
        ),
        as_json,
    )


@app.command()
def transformer(
    primary_v: float = typer.Option(None, "--primary-v"),
    secondary_v: float = typer.Option(None, "--secondary-v"),
    primary_turns: float = typer.Option(None, "--primary-turns"),
    secondary_turns: float = typer.Option(None, "--secondary-turns"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Transformer turns/voltage ratio."""
    _run(
        lambda: turns_ratio(primary_v=primary_v, secondary_v=secondary_v, primary_turns=primary_turns, secondary_turns=secondary_turns),
        as_json,
    )


@app.command("transformer-efficiency")
def transformer_eff(
    output: float = typer.Option(..., "--output"),
    core_loss: float = typer.Option(..., "--core-loss"),
    copper_loss: float = typer.Option(..., "--copper-loss", help="Full-load copper loss (W)"),
    load_fraction: float = typer.Option(1.0, "--load-fraction"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    _run(
        lambda: transformer_efficiency(
            output_power_w=output, core_loss_w=core_loss, full_load_copper_loss_w=copper_loss, load_fraction=load_fraction
        ),
        as_json,
    )


@app.command()
def symbolic(
    equation: str = typer.Argument(..., help=f"One of: {', '.join(list_equations())}"),
    solve_for: str = typer.Argument(...),
    values: list[str] = typer.Argument(None, help="KEY=VALUE pairs, e.g. V=230 I=5"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Whitelist symbolic solver. ee-toolkit symbolic ohms_law R V=230 I=5"""
    parsed: dict[str, float] = {}
    for item in values or []:
        if "=" not in item:
            typer.echo(f"Error: expected KEY=VALUE, got {item!r}", err=True)
            raise typer.Exit(code=2)
        k, v = item.split("=", 1)
        try:
            parsed[k.strip()] = float(v)
        except ValueError:
            typer.echo(f"Error: value for {k!r} is not a number: {v!r}", err=True)
            raise typer.Exit(code=2)  # noqa
    _run(lambda: solve_symbolic(equation, solve_for, parsed or None), as_json)


@app.command()
def equations() -> None:
    """List whitelisted symbolic equations."""
    for k, v in list_equations().items():
        typer.echo(f"{k}: {v}")


@app.command()
def batch(
    input_path: str = typer.Option(..., "--input"),
    output: str = typer.Option(..., "--output"),
    kind: str = typer.Option("energy", "--kind", help="energy | ohms | voltage_drop"),
    rate: float = typer.Option(0.15, "--rate"),
    days: float = typer.Option(30.0, "--days"),
) -> None:
    """Batch CSV processing. ee-toolkit batch --input examples/loads.csv --output results.csv"""
    try:
        df = process_batch(input_path, kind=kind, tariff_per_kwh=rate, days=days)
        batch_to_csv(df, output)
    except EEError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    ok = int((df["status"] == "ok").sum()) if "status" in df else len(df)
    typer.echo(f"Wrote {len(df)} row(s) to {output} ({ok} ok, {len(df) - ok} error(s) — see the message column).")


def main() -> None:  # console entry point
    app()


if __name__ == "__main__":
    main()
