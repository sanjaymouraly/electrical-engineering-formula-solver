"""Capture GENUINE screenshots of the running Streamlit app (Playwright).

Usage: start the app first (streamlit run app/main.py --server.port 8501),
then: python scripts/capture_screenshots.py
Screenshots are real browser renders of the delivered app — never mockups.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8502"
OUT = Path(__file__).resolve().parents[1] / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)


def go(page, label):
    page.get_by_text(label, exact=True).first.click()
    page.wait_for_timeout(1200)


def shot(page, name):
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / name), full_page=True)
    print("saved", name)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 950})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(BASE, wait_until="networkidle")
    page.get_by_text("Electrical Engineering Formula Solver", exact=False).first.wait_for(timeout=30000)
    shot(page, "01-dashboard.png")
    go(page, "Ohm's Law & DC")
    page.get_by_role("button", name="Calculate Ohm's law").click(); page.wait_for_timeout(1500)
    shot(page, "02-ohms-law.png")
    go(page, "Three-Phase AC")
    page.get_by_role("button", name="Calculate three-phase power").click(); page.wait_for_timeout(2500)
    shot(page, "03-three-phase-power-triangle.png")
    go(page, "Voltage Drop")
    page.get_by_role("button", name="Calculate voltage drop").click(); page.wait_for_timeout(2500)
    shot(page, "04-voltage-drop.png")
    go(page, "Energy & Cost")
    page.get_by_role("button", name="Calculate energy & cost").click(); page.wait_for_timeout(1500)
    shot(page, "05-energy-cost.png")
    go(page, "Unit Converter")
    page.get_by_role("button", name="Convert").click(); page.wait_for_timeout(1000)
    shot(page, "06-unit-converter.png")
    print("console errors:", errors or "none")
    browser.close()

# Report screenshot: render a real generated HTML report in the browser.
from ee_toolkit.calculators import solve_ohms_law  # noqa: E402
from ee_toolkit.reports import result_to_html  # noqa: E402

report = Path(__file__).resolve().parents[1] / "docs" / "sample_report.html"
report.write_text(result_to_html(solve_ohms_law(voltage_v=230, resistance_ohm=46)), encoding="utf-8")
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1000, "height": 800})
    page.goto(report.as_uri())
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "07-html-report.png"), full_page=True)
    print("saved 07-html-report.png")
    browser.close()
