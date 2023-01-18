"""Whitelist symbolic solver (SymPy). No arbitrary user expressions are evaluated.

Only the equations in ``EQUATIONS`` can be rearranged, only for their declared
symbols. Input values are substituted as numbers, never parsed as code.
"""

from __future__ import annotations

import sympy as sp

from ..errors import InsufficientInputError, InvalidInputError
from ..results import CalculationResult

V, I, R, P, S, PF, Q_, VL, IL = sp.symbols("V I R P S PF Q V_L I_L", real=True)

EQUATIONS: dict[str, dict] = {
    "ohms_law": {"eq": sp.Eq(V, I * R), "symbols": {"V": V, "I": I, "R": R}, "desc": "V = I*R"},
    "power_vi": {"eq": sp.Eq(P, V * I), "symbols": {"P": P, "V": V, "I": I}, "desc": "P = V*I"},
    "power_ir": {"eq": sp.Eq(P, I**2 * R), "symbols": {"P": P, "I": I, "R": R}, "desc": "P = I^2*R"},
    "ac_real_power": {"eq": sp.Eq(P, S * PF), "symbols": {"P": P, "S": S, "PF": PF}, "desc": "P = S*PF"},
    "three_phase_power": {
        "eq": sp.Eq(P, sp.sqrt(3) * VL * IL * PF),
        "symbols": {"P": P, "V_L": VL, "I_L": IL, "PF": PF},
        "desc": "P = sqrt(3)*V_L*I_L*PF",
    },
    "apparent_power": {"eq": sp.Eq(S, V * I), "symbols": {"S": S, "V": V, "I": I}, "desc": "S = V*I"},
}

# Physical domain checks applied to symbolic results.
_POSITIVE = {"V", "I", "R", "P", "S", "V_L", "I_L"}


def list_equations() -> dict[str, str]:
    return {k: v["desc"] for k, v in EQUATIONS.items()}


def solve_symbolic(equation: str, solve_for: str, values: dict[str, float] | None = None) -> CalculationResult:
    """Rearrange an approved equation and optionally evaluate it numerically.

    Example: solve_symbolic("ohms_law", "R", {"V": 230, "I": 5}) -> R = V/I = 46.
    """
    if equation not in EQUATIONS:
        raise InvalidInputError(f"Unknown equation {equation!r}. Allowed: {sorted(EQUATIONS)}")
    spec = EQUATIONS[equation]
    symbols: dict[str, sp.Symbol] = spec["symbols"]
    if solve_for not in symbols:
        raise InvalidInputError(f"Cannot solve {equation} for {solve_for!r}. Allowed: {sorted(symbols)}")
    target = symbols[solve_for]
    solutions = sp.solve(spec["eq"], target)
    if not solutions:
        raise InvalidInputError(f"No symbolic solution for {solve_for} in {equation}.")
    expr = solutions[0]
    result_values: dict[str, float] = {}
    steps = [f"Equation: {spec['desc']}", f"Rearranged: {solve_for} = {expr}"]
    numeric = None
    if values:
        unknown_keys = set(values) - set(symbols)
        if unknown_keys:
            raise InvalidInputError(f"Unknown variables for {equation}: {sorted(unknown_keys)}")
        if solve_for in values:
            raise InvalidInputError(f"Do not supply the variable being solved for ({solve_for}).")
        needed = {str(s) for s in expr.free_symbols}
        missing = needed - set(values)
        if missing:
            raise InsufficientInputError(f"Missing values needed to evaluate {solve_for}: {sorted(missing)}")
        subs = {symbols[k]: float(v) for k, v in values.items()}
        numeric = float(expr.subs(subs).evalf())
        if solve_for in _POSITIVE and numeric <= 0:
            raise InvalidInputError(f"Symbolic result {solve_for}={numeric} is not physically positive; check inputs.")
        if solve_for == "PF" and not (0 < numeric <= 1):
            raise InvalidInputError(f"Symbolic result PF={numeric} is outside (0, 1].")
        result_values[solve_for] = numeric
        steps.append("Substitution: " + ", ".join(f"{k}={v:g}" for k, v in values.items()))
        steps.append(f"{solve_for} = {expr} = {numeric:.6g}")
    return CalculationResult(
        "symbolic",
        result_values,
        [spec["desc"], f"{solve_for} = {expr}"],
        steps,
        ["Only whitelisted equations/variables are accepted; user text is never evaluated as code."],
        [] if numeric is not None else ["Symbolic rearrangement only — supply values for a numeric result."],
    )
