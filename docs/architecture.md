# Architecture

```mermaid
flowchart TD
    UI[Streamlit app<br/>app/main.py] --> LIB
    CLI[Typer CLI<br/>ee_toolkit.cli.main] --> LIB
    BATCH[CSV batch<br/>ee_toolkit.batch] --> LIB
    LIB[Calculation library<br/>ee_toolkit.calculators] --> VAL[Validation<br/>ee_toolkit.validation]
    LIB --> RES[CalculationResult<br/>values + formulas + steps + assumptions + warnings]
    LIB --> UNITS[Pint units<br/>ee_toolkit.units]
    LIB --> SYM[Whitelist SymPy solver<br/>calculators.symbolic]
    RES --> REP[Reports<br/>HTML / JSON / CSV]
    RES --> CHARTS[Plotly charts<br/>ee_toolkit.charts]
    UI --> CHARTS
    UI --> REP
```

Design rules: one validated calculation engine powers the UI, CLI, and batch
paths (no duplicated formulas); calculators never import Streamlit or Typer;
all results carry their formulas, steps, assumptions, and warnings so every
number is auditable. Internal arithmetic is full float precision — rounding
happens only at presentation, except money, which uses `Decimal` quantised
to cents (ROUND_HALF_UP).
