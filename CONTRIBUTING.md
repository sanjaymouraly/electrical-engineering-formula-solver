# Contributing

1. Fork and clone, then set up: `python3 -m venv .venv && source .venv/bin/activate` (Linux/macOS) or `py -m venv .venv; .\.venv\Scripts\Activate.ps1` (Windows PowerShell).
2. Install: `python -m pip install -e ".[app,dev]"`
3. Run checks before opening a PR: `python -m pytest --cov=ee_toolkit`, `ruff check src app tests`, `ruff format --check src app tests`, `mypy src/ee_toolkit`.
4. Engineering rules: every new formula needs (a) a stated assumption list, (b) input validation via `ee_toolkit.validation`, (c) tests whose expected values are derived independently of the implementation, and (d) a worked example. Never hardcode outputs.
5. Keep calculation logic in `src/ee_toolkit/` free of Streamlit/Typer imports — UI and CLI are thin layers over the library.
