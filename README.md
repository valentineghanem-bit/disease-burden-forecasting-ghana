# A Reproducible Workflow and Source-Provenance Audit for Forecasting Short National Health-Indicator Panels: A Worked Example from Ghana Using WHO Global Health Observatory and World Bank Data

[![CI](https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/actions/workflows/ci.yml/badge.svg)](https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--8332--0220-green.svg)](https://orcid.org/0009-0002-8332-0220)

**Author:** Valentine Golden Ghanem | Ghana COCOBOD Cocoa Clinic, Accra, Ghana
**ORCID:** [0009-0002-8332-0220](https://orcid.org/0009-0002-8332-0220)
**Affiliation:** Ghana COCOBOD Cocoa Clinic, Accra, Ghana
**Reporting standard:** STROBE (observational panel components)
**Date:** 2026
**Status:** Analysis complete; manuscript in preparation for journal submission

## 1. Abstract

Public-domain WHO Global Health Observatory (GHO) and World Bank exports are the default empirical basis for national health-indicator forecasting, but these files carry undocumented structural pitfalls that silently corrupt an analysis if uncorrected, and forecasting choices — method, model order, fitting scale — are typically made ad hoc and per-indicator with no shared, reproducible protocol. This project assembles a Ghana national indicator panel from nine public-domain WHO GHO/Global Health Estimates and World Bank World Development Indicators sources, documents and verifies every data-integrity correction required to reach an analysis-ready panel (six were required), and specifies a data-length-tiered forecasting protocol: fixed eligibility thresholds, small-sample-corrected (AICc) per-series ARIMA order selection, log-scale fitting for non-negative-bounded series, interval-reliability flags tied to series length, and a structural-break sensitivity test for the 2020 COVID-19 and 2022 Ghana currency-crisis candidate breaks. Of 25 indicators assembled, 21 met the 15-year minimum for formal forecasting. A uniformly-applied ARIMA(1,1,1) was the AICc-optimal order for only 1 of these 21 series; per-series order selection shifted the 2030 point forecast by up to ~24% for the most affected indicator. Separately, a naive raw-scale ARIMA-versus-exponential-smoothing disagreement for malaria (~24%) was closed mostly by log-scale fitting alone (this project's protocol for non-negative-bounded series), leaving a smaller ~9% gap after also selecting the series' own order: a fitting-scale artefact, most of it, with order selection contributing comparatively little. Testing rather than assuming away structural breaks, a decisive 2022 currency-crisis break shifted the malaria forecast by a further +26.5% (larger than its order-selection effect), and a decisive break at both candidate dates was found for the World Bank life-expectancy series, though most series' break tests were underpowered on 2–5 post-break observations. An LSTM neural network did not outperform classical methods on either of two representative series tested by walk-forward validation. **The contribution is a reusable, documented workflow and a named set of source-specific pitfalls — not novelty in order selection itself.** The Ghana-specific 2030 forecasts are a worked demonstration, not planning inputs.

## 2. Research Question & Aim

Document the data-integrity corrections required to move from raw WHO GHO/World Bank export to an analysis-ready national indicator panel for Ghana, and specify a data-length-appropriate, empirically validated forecasting protocol built on that cleaned panel — so that the workflow, and its pitfalls, can be reused by another analyst rather than rediscovered. The Ghana-specific 2030 forecasts serve only to demonstrate, on real data, how much each documented choice changes the result; they are not offered as planning inputs.

## 3. Methods Summary

| Method | Tool | Purpose |
|---|---|---|
| Source-provenance audit (structural verification against export format, not inference) | pandas, WHO GHO OData API | Identify and correct 6 silent data-integrity pitfalls before any model is fit |
| Walk-forward validation (expanding window, multi-seed, multi-architecture) | Python (statsmodels, PyTorch) | Empirically test LSTM vs. classical (ARIMA/ETS) method choice |
| Akaike Information Criterion (small-sample-corrected, AICc) grid search | statsmodels | Per-series ARIMA order selection (not a uniform order) |

## 4. Data Sources

Nine public-domain sources: seven WHO Global Health Observatory (GHO)/Global Health Estimates (GHE) export files (life expectancy, tuberculosis, HIV, malaria, health-financing, a global-strategy export covering the UHC Service Coverage Index, and a consolidated health-indicators export covering air-pollution series), one indicator (under-five mortality) drawn directly from the live WHO GHO OData API, and one World Bank World Development Indicators (WDI) export used as an independent cross-source check for life expectancy, suicide mortality, total fertility rate, and health-expenditure series. All sources are public-domain, aggregate, de-identified data spanning 1932–2024.

## 5. Key Findings

| Metric | Value |
|---|---|
| Documented source-provenance corrections required (Table 1) | 6 |
| Indicators assembled / met the 15-year formal-forecasting minimum | 25 / 21 |
| Under-five mortality, 2030 forecast | 29.3 per 1,000 live births (95% CI 26.3–32.7) |
| Tuberculosis incidence, 2030 forecast | 108.2 per 100,000 (95% CI 103.1–113.7) |
| Malaria ARIMA-vs-ETS gap: naive raw-scale → log-scale fixed-order → log-scale own-order | ~24% → ~3.5% → ~9% (mostly a scale, not order, effect) |
| Series where a uniform ARIMA(1,1,1) order matched the AICc-optimal order | 1 of 21 |
| Largest per-series-order effect on the 2030 point forecast | ~23.5% (out-of-pocket expenditure, % of CHE) |
| Series with a standard-confidence forecast (n≥25 years) | 7 of 21 |
| Decisive 2022 currency-crisis structural break, malaria 2030 forecast shift (Table 5) | +26.5% (larger than the order-selection effect) |
| Decisive structural break at both 2020 and 2022, World Bank life-expectancy series (Table 5) | Yes -- plausible partial explanation for its divergence from WHO-GHO life expectancy |
| LSTM vs. classical methods, walk-forward validation | LSTM did not outperform on either series tested |

## 6. Repository Structure

```
disease-burden-forecasting-ghana/
├── README.md
├── CITATION.cff
├── LICENSE
├── requirements.txt
├── Dockerfile
├── .github/workflows/ci.yml
├── analysis/            # Python analysis scripts (Stage 0-12 pipeline)
├── data/raw/            # Public-domain source datasets
├── outputs/data/        # Forecast outputs and master CSV
├── dashboard/           # Interactive dashboard (offline, self-contained HTML)
├── poster/              # Conference poster (offline, self-contained HTML)
└── tests/               # Reproducibility checks
```

## 7. Reproducibility

### 7.1 Requirements
Python 3.13 (as used to produce the reported results; see `requirements.txt` for pinned minimum package versions — floor pins mean a fresh install may resolve to newer point releases than exactly what produced the manuscript's numbers).

### 7.2 Clone & install
```bash
git clone https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana.git
cd disease-burden-forecasting-ghana
pip install -r requirements.txt
```

### 7.3 Run the analytical pipeline
```bash
cd analysis
python stage1_build_master_panel.py
python stage4_walkforward_validation.py
python stage8_forecast_fixes.py
python stage9_aicc_margin_table.py
python stage8_final_forecasts.py
python stage13_structural_break_sensitivity.py
python stage9_build_tables2_3.py
python stage6_figures.py
python stage10_build_docx.py
python stage12_build_dashboard_poster.py
```
Note: `stage0_*`, `stage3_build_vulnerability_index.py`, `stage4_gistar_preflight.py`, `stage5_threshold_sensitivity.py`, and `stage13_fanchart_paths.py` are retained from an earlier, dropped scope (a district-level vulnerability index and a fan-chart figure, both removed from the current manuscript) and are not part of this pipeline; they are not deleted so the exploratory history remains auditable, but running them is not required to reproduce any table or figure in the current paper. `stage5_national_forecasts_2030.py` is likewise excluded: it is an earlier, pre-AICc-fix forecasting script superseded by `stage8_forecast_fixes.py`/`stage8_final_forecasts.py` (no per-series AICc order selection, no log-scale fitting, no structural-break test) that happens to write to the same output path; running it after the pipeline above would silently overwrite the correct numbers with stale ones, so it is intentionally not in the documented run order.

### 7.4 Run the test suite
```bash
pytest tests/
```

### 7.5 Open the static HTML dashboard
```bash
python -m http.server 8000 --directory dashboard
# then open http://localhost:8000/Ghana_BurdenForecasting2030_Dashboard.html
```

## 8. Outputs

| Output | Description |
|---|---|
| `outputs/data/Ghana_BurdenForecasting2030_MASTER_national.csv` | 21-indicator national forecast panel to 2030 (ARIMA/ETS, per-series AICc order, 95% CIs) |
| `outputs/data/arima_order_sensitivity.csv` | Per-series AICc order-search results, all 21 series |
| `outputs/data/aicc_margin_vs_uniform111.csv` | AICc difference between each series' own order and a uniform ARIMA(1,1,1), all 21 series |
| `outputs/data/forecast_order_comparison.csv` | 2030 forecast under uniform vs. own-order specification, all 21 series |
| `outputs/data/walkforward_validation_results.csv` | LSTM-vs-classical walk-forward validation results, 2 representative series |
| `dashboard/Ghana_BurdenForecasting2030_Dashboard.html` | Interactive dashboard (offline, self-contained, vanilla JS + inline SVG, <60 KB) |
| `poster/Ghana_BurdenForecasting2030_Poster.html` | Conference poster (offline, self-contained, vanilla JS + inline SVG, <60 KB) |

## 8a. Downloadable Artefacts (HTML)

| Artefact | View on GitHub | Live preview | Direct download |
|---|---|---|---|
| Interactive dashboard | [dashboard/Ghana_BurdenForecasting2030_Dashboard.html](https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/blob/main/dashboard/Ghana_BurdenForecasting2030_Dashboard.html) | [Preview](https://htmlpreview.github.io/?https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/blob/main/dashboard/Ghana_BurdenForecasting2030_Dashboard.html) | [Download](https://raw.githubusercontent.com/valentineghanem-bit/disease-burden-forecasting-ghana/main/dashboard/Ghana_BurdenForecasting2030_Dashboard.html) |
| Conference poster | [poster/Ghana_BurdenForecasting2030_Poster.html](https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/blob/main/poster/Ghana_BurdenForecasting2030_Poster.html) | [Preview](https://htmlpreview.github.io/?https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/blob/main/poster/Ghana_BurdenForecasting2030_Poster.html) | [Download](https://raw.githubusercontent.com/valentineghanem-bit/disease-burden-forecasting-ghana/main/poster/Ghana_BurdenForecasting2030_Poster.html) |

## 9. Reporting Standard

STROBE (Strengthening the Reporting of Observational Studies in Epidemiology) for the observational national-panel components, applied where relevant to this ecological time-series design.

## 10. Ethical Statement

This analysis uses exclusively public-domain, aggregate, de-identified secondary data (WHO, World Bank). No individual-level records were accessed at any point in this pipeline. Consistent with standard practice for secondary analysis of publicly available, aggregate, de-identified data involving no human-participant contact, no ethics committee approval was sought or required.

**Competing interests.** The author declares no competing interests. No funding was received for this work.

## 11. Citation

Ghanem VG. A reproducible workflow and source-provenance audit for forecasting short national health-indicator panels: a worked example from Ghana using WHO Global Health Observatory and World Bank data. 2026.

```bibtex
@misc{ghanem2026burdenforecasting,
  author = {Ghanem, Valentine Golden},
  title  = {A reproducible workflow and source-provenance audit for forecasting short national health-indicator panels: a worked example from Ghana using WHO Global Health Observatory and World Bank data},
  year   = {2026},
  url    = {https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana}
}
```

See also `CITATION.cff` for machine-readable citation metadata.

## 12. License

Code: MIT License (see `LICENSE`). Outputs and figures: CC BY 4.0.

## 13. Author & Contact

Valentine Golden Ghanem, Ghana COCOBOD Cocoa Clinic, Accra, Ghana. Email: valentineghanem@gmail.com. ORCID: [0009-0002-8332-0220](https://orcid.org/0009-0002-8332-0220).
