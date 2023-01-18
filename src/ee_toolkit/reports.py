"""Local report/export generation: HTML, JSON, CSV.

All user-supplied text is HTML-escaped in HTML reports, and spreadsheet
formula injection (cells starting with =, +, -, @) is neutralised in CSV.
"""

from __future__ import annotations

import csv
import html
import io
import json
from datetime import UTC, datetime
from pathlib import Path

from .results import CalculationResult


def _safe_cell(value: object) -> object:
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def result_to_json(result: CalculationResult) -> str:
    payload = {"generated_at_utc": datetime.now(UTC).isoformat(), **result.to_dict()}
    return json.dumps(payload, indent=2)


def result_to_csv(result: CalculationResult) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["category", "quantity", "value"])
    for k, v in result.values.items():
        w.writerow([_safe_cell(result.category), _safe_cell(k), v])
    return buf.getvalue()


def result_to_html(result: CalculationResult, *, title: str = "Electrical Engineering Calculation Report") -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    rows = "".join(
        f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(f'{v:.6g}' if isinstance(v, float) else str(v))}</td></tr>"
        for k, v in result.values.items()
    )

    def lst(items):
        return "".join(f"<li>{html.escape(str(i))}</li>" for i in items) or "<li>None</li>"

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{font-family:system-ui,Arial,sans-serif;margin:2rem;max-width:900px}}table{{border-collapse:collapse}}td,th{{border:1px solid #999;padding:.4rem .7rem}}h1{{color:#0b5394}}</style></head>
<body><h1>{html.escape(title)}</h1>
<p><strong>Category:</strong> {html.escape(result.category)} &middot; <strong>Generated:</strong> {now}</p>
<h2>Results</h2><table><tr><th>Quantity</th><th>Value (SI units as named)</th></tr>{rows}</table>
<h2>Formulas</h2><ul>{lst(result.formulas)}</ul>
<h2>Steps</h2><ol>{lst(result.steps)}</ol>
<h2>Assumptions</h2><ul>{lst(result.assumptions)}</ul>
<h2>Warnings</h2><ul>{lst(result.warnings)}</ul>
<p><em>For learning and preliminary engineering analysis only — not certified electrical design or a substitute for qualified professional verification.</em></p>
</body></html>"""


def write_report(result: CalculationResult, path: str | Path, fmt: str | None = None) -> Path:
    p = Path(path)
    fmt = (fmt or p.suffix.lstrip(".")).lower()
    content = {"json": result_to_json, "csv": result_to_csv, "html": result_to_html, "htm": result_to_html}.get(fmt)
    if content is None:
        raise ValueError(f"Unsupported report format {fmt!r}; use html, json, or csv.")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content(result), encoding="utf-8")
    return p
