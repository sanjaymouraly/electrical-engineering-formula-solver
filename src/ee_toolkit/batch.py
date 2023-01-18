"""CSV batch calculations (pandas for I/O, NumPy for vectorised maths).

Malformed rows never abort the batch: they come back with ``status=error``
and a human-readable ``message`` so the good rows are still usable.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .errors import InvalidInputError

REQUIRED = {
    "energy": {"name", "power_w", "hours_per_day"},
    "ohms": {"name", "voltage_v", "resistance_ohm"},
    "voltage_drop": {"name", "voltage_v", "current_a", "length_m", "resistance_ohm_per_km"},
}


def _read(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.is_file():
        raise InvalidInputError(f"Input CSV not found: {p}")
    try:
        return pd.read_csv(p)
    except Exception as exc:
        raise InvalidInputError(f"Could not read CSV {p}: {exc}") from exc


def process_batch(input_path: str | Path, kind: str = "energy", tariff_per_kwh: float = 0.15, days: float = 30.0) -> pd.DataFrame:
    if kind not in REQUIRED:
        raise InvalidInputError(f"Unknown batch kind {kind!r}; choose from {sorted(REQUIRED)}")
    df = _read(input_path)
    missing = REQUIRED[kind] - set(df.columns)
    if missing:
        raise InvalidInputError(f"CSV is missing required column(s) for kind={kind}: {sorted(missing)}")
    rows: list[dict] = []
    for idx, row in df.iterrows():
        base = {"row": int(idx) + 2, "name": row.get("name", ""), "status": "ok", "message": ""}  # +2: header + 1-based
        try:
            if kind == "energy":
                power = float(row["power_w"])
                hours = float(row["hours_per_day"])
                duty = float(row.get("duty_cycle", 1.0)) if pd.notna(row.get("duty_cycle", 1.0)) else 1.0
                if power < 0 or not (0 <= hours <= 24) or not (0 <= duty <= 1):
                    raise InvalidInputError("power_w >= 0, hours_per_day in [0,24], duty_cycle in [0,1] required")
                kwh = float(np.float64(power) * hours * duty * float(days) / 1000.0)  # NumPy scalar maths
                base.update({"power_w": power, "energy_kwh": round(kwh, 6), "cost": round(kwh * float(tariff_per_kwh), 2)})
            elif kind == "ohms":
                v, r = float(row["voltage_v"]), float(row["resistance_ohm"])
                if r <= 0:
                    raise InvalidInputError("resistance_ohm must be > 0")
                base.update({"voltage_v": v, "resistance_ohm": r, "current_a": v / r, "power_w": v * v / r})
            else:
                v, i, length, r = (float(row[c]) for c in ("voltage_v", "current_a", "length_m", "resistance_ohm_per_km"))
                if v <= 0 or i < 0 or length < 0 or r < 0:
                    raise InvalidInputError("voltage_v > 0; current, length, resistance >= 0 required")
                vd = 2.0 * i * r * (length / 1000.0)
                base.update(
                    {
                        "voltage_drop_v": vd,
                        "voltage_drop_percent": vd / v * 100.0,
                        "receiving_voltage_v": v - vd,
                        "note": "2-conductor DC/single-phase estimate",
                    }
                )
        except Exception as exc:  # per-row isolation is the documented behaviour
            base.update({"status": "error", "message": str(exc)})
        rows.append(base)
    return pd.DataFrame(rows)


def batch_to_csv(df: pd.DataFrame, output_path: str | Path) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out
