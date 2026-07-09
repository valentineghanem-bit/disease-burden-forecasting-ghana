"""Reproducibility checks on the pipeline's committed output files."""
import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "data")


def _read_csv(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_district_master_has_all_261_districts():
    rows = _read_csv("Ghana_BurdenForecasting2030_MASTER_district.csv")
    assert len(rows) == 261


def test_district_master_exclusion_counts():
    rows = _read_csv("Ghana_BurdenForecasting2030_MASTER_district.csv")
    excluded = [r for r in rows if r["gistar_class"] == "EXCLUDED"]
    hotspots = [r for r in rows if r["gistar_class"] == "HOTSPOT_P05"]
    coldspots = [r for r in rows if r["gistar_class"] == "COLDSPOT_P05"]
    assert len(excluded) == 6
    assert len(hotspots) == 6
    assert len(coldspots) == 0


def test_national_forecast_no_negative_confidence_intervals():
    rows = _read_csv("Ghana_BurdenForecasting2030_MASTER_national.csv")
    assert len(rows) == 21
    for row in rows:
        assert float(row["arima_ci_low"]) >= 0, row["indicator"]


def test_hotspot_threshold_sensitivity_monotonic():
    rows = _read_csv("hotspot_threshold_sensitivity.csv")
    hotspot_counts = [int(r["hotspots"]) for r in rows]
    assert hotspot_counts == sorted(hotspot_counts)
