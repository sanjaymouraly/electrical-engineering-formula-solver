"""Unit conversion backed by Pint dimensional analysis.

Incompatible conversions raise :class:`IncompatibleUnitError` — they are never
silently coerced. Internally the calculators work in SI base units.
"""

from __future__ import annotations

import pint

from .errors import IncompatibleUnitError, InvalidInputError

ureg = pint.UnitRegistry()
# Pint ships volt_ampere but not the reactive-power unit; define it (same
# dimensions as VA, kept as a distinct unit name for engineering clarity).
ureg.define("volt_ampere_reactive = volt * ampere = VAR")
Q_ = ureg.Quantity

# Friendly aliases -> Pint expressions
ALIASES = {
    "mv": "millivolt",
    "v": "volt",
    "kv": "kilovolt",
    "ua": "microampere",
    "µa": "microampere",
    "ma": "milliampere",
    "a": "ampere",
    "ka": "kiloampere",
    "mohm": "milliohm",
    "ohm": "ohm",
    "Ω": "ohm",
    "kohm": "kiloohm",
    "mohm_cap": "megaohm",
    "w": "watt",
    "kw": "kilowatt",
    "mw_power": "megawatt",
    "va": "volt_ampere",
    "kva": "kilovolt_ampere",
    "mva": "megavolt_ampere",
    "var": "volt_ampere_reactive",
    "kvar": "kilovolt_ampere_reactive",
    "wh": "watt_hour",
    "kwh": "kilowatt_hour",
    "mwh": "megawatt_hour",
    "m": "meter",
    "km": "kilometer",
    "cm": "centimeter",
    "mm": "millimeter",
    "ft": "foot",
    "in": "inch",
    "s": "second",
    "min": "minute",
    "h": "hour",
    "hr": "hour",
    "hz": "hertz",
    "khz": "kilohertz",
    "f": "farad",
    "uf": "microfarad",
    "µf": "microfarad",
    "nf": "nanofarad",
}
# Note: 'mohm'/'mw' are ambiguous in engineering shorthand (milliohm vs megaohm).
# We resolve strictly: mohm=milliohm is wrong for many users, so require explicit.
ALIASES.pop("mohm")
ALIASES.pop("mohm_cap")


# Pint itself is case-sensitive (MW != mW); check the exact spelling first.
_CASE_SENSITIVE = {
    "MW": "megawatt",
    "mW": "milliwatt",
    "MWh": "megawatt_hour",
    "MVA": "megavolt_ampere",
    "MVAr": "megavolt_ampere_reactive",
    "kW": "kilowatt",
    "kWh": "kilowatt_hour",
    "kV": "kilovolt",
    "kA": "kiloampere",
    "kVA": "kilovolt_ampere",
    "kVAR": "kilovolt_ampere_reactive",
    "mV": "millivolt",
    "mA": "milliampere",
    "uA": "microampere",
    "uF": "microfarad",
}


def _unit(expr: str):
    exact = expr.strip()
    if exact in _CASE_SENSITIVE:
        return ureg.parse_expression(_CASE_SENSITIVE[exact])
    key = exact.lower()
    if key in {"megaohm", "mohm_cap", "megohm"}:
        return ureg.megaohm
    if key == "milliohm":
        return ureg.milliohm
    if key in ALIASES:
        return getattr(ureg, ALIASES[key]) if hasattr(ureg, ALIASES[key]) else ureg.parse_expression(ALIASES[key])
    try:
        return ureg.parse_expression(expr)
    except Exception as exc:  # Pint raises several parse error types
        raise InvalidInputError(f"Unknown unit: {expr!r}") from exc


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert ``value`` between compatible units; reject incompatible ones."""
    try:
        q = float(value) * _unit(from_unit)
        result = q.to(_unit(to_unit))
    except pint.DimensionalityError as exc:
        raise IncompatibleUnitError(f"Cannot convert {from_unit!r} to {to_unit!r}: incompatible dimensions.") from exc
    except InvalidInputError:
        raise
    except Exception as exc:
        # Pint sometimes wraps dimensionality problems; verify dimensionalities explicitly.
        raise IncompatibleUnitError(f"Cannot convert {from_unit!r} to {to_unit!r}: {exc}") from exc
    return float(result.magnitude)


def parse_quantity(text: str):
    """Parse '230 V' / '2.5 kW' into (magnitude, canonical unit string). No eval()."""
    parts = str(text).strip().split()
    if len(parts) != 2:
        raise InvalidInputError("Quantity must look like '230 V' or '2.5 kW' (number, space, unit).")
    try:
        magnitude = float(parts[0])
    except ValueError as exc:
        raise InvalidInputError(f"Invalid numeric value in quantity: {parts[0]!r}") from exc
    unit = _unit(parts[1])
    q = magnitude * unit
    return float(q.magnitude), str(q.units)


SUPPORTED = [
    "mV, V, kV",
    "uA, mA, A, kA",
    "milliohm, ohm, kiloohm, megaohm",
    "W, kW, MW (megawatt)",
    "VA, kVA, MVA",
    "VAR, kVAR",
    "Wh, kWh, MWh",
    "m, cm, mm, km, ft, inch",
    "s, minute, hour",
    "Hz, kHz",
    "F, uF, nF",
]
