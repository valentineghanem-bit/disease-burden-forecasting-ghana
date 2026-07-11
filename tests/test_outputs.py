"""Reproducibility checks on the pipeline's committed output files.

NOTE (Phase 12 full-deliverable QA, 2026-07-11): the district structural-vulnerability
index and its Getis-Ord Gi* hotspot/coldspot classification were dropped from this
project's scope (Phase 0 scope-lock: unvalidated across 7 prior sibling projects). The
tests that referenced those now-archived output files
(`Ghana_BurdenForecasting2030_MASTER_district.csv`, `hotspot_threshold_sensitivity.csv`)
were removed here -- they were silently failing on every CI run since the files were
archived, because nothing had re-run the test suite against the narrowed scope until this
pass. Replaced with tests against the current, sole scope: the national 21-indicator
forecast panel.
"""
import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "data")
DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "..", "dashboard")
POSTER_DIR = os.path.join(os.path.dirname(__file__), "..", "poster")


def _read_csv(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_national_forecast_no_negative_confidence_intervals():
    rows = _read_csv("Ghana_BurdenForecasting2030_MASTER_national.csv")
    assert len(rows) == 21
    for row in rows:
        assert float(row["arima_ci_low"]) >= 0, row["indicator"]


def test_national_forecast_master_matches_production_csv():
    """The published Master CSV deliverable must not drift from the production output
    it is meant to republish (caught stale in Phase 12: the Master CSV still carried
    pre-AICc-fix ARIMA orders after the methodological correction was applied)."""
    master = _read_csv("Ghana_BurdenForecasting2030_MASTER_national.csv")
    production = _read_csv("national_forecasts_2030.csv")
    assert master == production


def test_arima_order_sensitivity_has_21_series():
    rows = _read_csv("arima_order_sensitivity.csv")
    assert len(rows) == 21


def test_exactly_one_series_matches_uniform_111():
    rows = _read_csv("arima_order_sensitivity.csv")
    matches = [r for r in rows if r["matches_111"].strip().lower() == "true"]
    assert len(matches) == 1, "the headline '1 of 21 matched (1,1,1)' finding must hold"


def test_aicc_margin_table_has_21_series_and_correct_near_tie_count():
    rows = _read_csv("aicc_margin_vs_uniform111.csv")
    assert len(rows) == 21
    near_ties = [r for r in rows if r["near_tie"].strip().lower() == "true"]
    assert len(near_ties) == 11, "the '11 of 21 near-tie' finding quoted in Results must hold"


def test_structural_break_sensitivity_headline_counts_hold():
    """Regression lock for the two structural-break findings reported in Results/Table 5:
    6 of 20 testable series show a decisive COVID-2020 break, and 2 of 7 testable series
    show a decisive currency-2022 break (malaria; World Bank life expectancy)."""
    rows = _read_csv("structural_break_sensitivity.csv")
    assert len(rows) == 21
    covid_testable = [r for r in rows if r["covid_2020_testable"].strip().lower() == "true"]
    covid_decisive = [r for r in covid_testable if float(r["covid_2020_delta_aicc"]) > 2]
    assert len(covid_testable) == 20
    assert len(covid_decisive) == 6
    currency_testable = [r for r in rows if r["currency_2022_testable"].strip().lower() == "true"]
    currency_decisive = [r for r in currency_testable if float(r["currency_2022_delta_aicc"]) > 2]
    assert len(currency_testable) == 7
    assert len(currency_decisive) == 2


def test_dashboard_and_poster_under_size_ceiling():
    """Standing repo spec: dashboard/poster hard ceiling is 60 KB, vanilla JS + inline
    SVG only (no external JS/CDN, no base64 images). Both were found at ~1.2 MB each
    with embedded base64 images before the Phase 12 rebuild."""
    dash = os.path.join(DASHBOARD_DIR, "Ghana_BurdenForecasting2030_Dashboard.html")
    poster = os.path.join(POSTER_DIR, "Ghana_BurdenForecasting2030_Poster.html")
    for path in (dash, poster):
        size_kb = os.path.getsize(path) / 1024
        assert size_kb < 60, f"{path} is {size_kb:.1f} KB, over the 60 KB ceiling"
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "base64" not in content.lower(), f"{path} contains a base64-embedded asset"
        for banned in ("cdn.", "unpkg.", "jsdelivr", "chart.js", "plotly", "d3.js"):
            assert banned not in content.lower(), f"{path} references external dependency: {banned}"
