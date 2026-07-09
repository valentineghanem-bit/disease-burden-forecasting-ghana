# Forecasting Ghana's National Health and Demographic Indicators to 2030, with District-Level Structural-Vulnerability Context

[![CI](https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/actions/workflows/ci.yml/badge.svg)](https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--8332--0220-green.svg)](https://orcid.org/0009-0002-8332-0220)

**Author:** Valentine Golden Ghanem | Ghana COCOBOD Cocoa Clinic, Accra, Ghana
**ORCID:** [0009-0002-8332-0220](https://orcid.org/0009-0002-8332-0220)
**Affiliation:** Ghana COCOBOD Cocoa Clinic, Accra, Ghana
**Reporting standard:** STROBE, RECORD-Spatial
**Date:** 2026
**Status:** Manuscript in preparation

## 1. Abstract

A validated multi-indicator time-series analysis forecasts 21 of Ghana's national health, mortality, and health-financing indicators to 2030, using a forecasting methodology whose method choice (classical time-series vs. LSTM) and per-series model order were both empirically validated rather than assumed. A companion, explicitly non-integrated district-level structural-vulnerability index (principal component analysis, 6 socioeconomic covariates, 261 districts) provides a screening-layer signal for future disease-surveillance and data-linkage investment. Under-five mortality is projected to decline to 28.6 per 1,000 live births by 2030, narrowly missing the SDG 3.2 target. A per-series AIC order-selection correction narrowed the malaria forecast's ARIMA-versus-exponential-smoothing gap from ~24% to ~9%, showing most of an apparent cross-model disagreement was a specification artefact rather than a genuine conflict. The district index's first principal component shows strong positive spatial autocorrelation (Moran's I = 0.80), with a hotspot count that is markedly threshold-sensitive (6 at p<0.05, 20 at p<0.10, 45 hotspots/32 coldspots under Benjamini-Hochberg FDR correction).

## 2. Research Question & Aims

1. Forecast Ghana's confirmed-available national disease, mortality, and health-financing indicators to 2030 using a data-length-appropriate, empirically validated methodology applied uniformly across all 21 series.
2. Characterise the socioeconomic structural-vulnerability pattern across Ghana's 261 districts as a screening-layer signal for future disease-surveillance investment, not a district-level disease-burden estimate.
3. Synthesise both findings against this research programme's 21 prior projects and the external epidemiological literature, disclosing every data limitation and methodological constraint directly.

## 3. Methods Summary

| Method | Tool | Purpose |
|---|---|---|
| Walk-forward validation (expanding window, multi-seed, multi-architecture) | Python (statsmodels, PyTorch) | Empirically test LSTM vs. classical (ARIMA/ETS) method choice |
| Akaike Information Criterion grid search | statsmodels | Per-series ARIMA order selection (not a uniform order) |
| Principal component analysis | scikit-learn | District structural-vulnerability index (6 covariates) |
| Global Moran's I / local Getis-Ord Gi* | esda, libpysal | Spatial autocorrelation and hotspot/coldspot classification |
| Benjamini-Hochberg FDR correction | statsmodels | Multiple-testing correction for hotspot significance |
| Bootstrap resampling | NumPy | Confidence interval on composite-vs-single-covariate validation |

## 4. Data Sources

| Source | Variables | Year | Access |
|---|---|---|---|
| WHO Global Health Observatory / Global Health Estimates / World Health Statistics | Life expectancy, TB/HIV/malaria incidence, NCD mortality, U5MR, suicide rate, health financing | 1932–2024 | Public domain |
| World Bank World Development Indicators | Cross-source life expectancy, suicide rate, health expenditure, TFR, PM2.5 | Varies | Public domain |
| USAID DHS StatCompiler | Regional fertility indicators (16 regions, 9 survey rounds) | 1988–2022 | Public domain |
| Ghana Statistical Service 2021 Population and Housing Census | District socioeconomic covariates (261 districts) | 2021 | Public domain |

## 5. Key Findings

| Metric | Value |
|---|---|
| U5MR 2030 forecast | 28.6 per 1,000 live births (95% CI 26.6–30.9) |
| TB incidence 2030 forecast | 109.3 per 100,000 (95% CI 104.2–114.5) |
| Malaria model gap, before/after per-series order correction | ~24% → ~9% |
| District PC1 Moran's I | 0.80 (z=19.3, p=0.001) |
| Hotspot count, p<0.05 / p<0.10 / FDR-BH | 6 / 20 / 45 (+32 coldspots under FDR) |
| National indicators forecast under one validated methodology | 21 |

## 6. Repository Structure

```
disease-burden-forecasting-ghana/
├── README.md
├── CITATION.cff
├── LICENSE
├── requirements.txt
├── Dockerfile
├── .github/workflows/ci.yml
├── analysis/            # Python analysis scripts (Stage 0-8 pipeline)
├── data/raw/            # 15 public-domain source datasets
├── outputs/data/        # Forecast outputs, master CSVs, spatial results
├── dashboard/           # HI-EI interactive dashboard (offline HTML)
├── poster/              # A0 conference poster (offline HTML)
└── tests/               # Reproducibility checks
```

## 7. Reproducibility

### 7.1 Requirements
Python 3.12+. See `requirements.txt` for pinned minimum versions.

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
python stage3_build_vulnerability_index.py
python stage4_walkforward_validation.py
python stage4_gistar_preflight.py
python stage8_forecast_fixes.py
python stage8_final_forecasts.py
```

### 7.4 Run the test suite
```bash
pytest tests/
```

### 7.5 Launch the interactive Dash application
Not applicable — this repository ships a fully offline, self-contained HTML dashboard rather than a live Dash server (see 7.6).

### 7.6 Open the static HTML dashboard
```bash
python -m http.server 8000 --directory dashboard
# then open http://localhost:8000/Ghana_BurdenForecasting2030_Dashboard.html
```

## 8. Outputs

| Output | Description |
|---|---|
| `outputs/data/Ghana_BurdenForecasting2030_MASTER_national.csv` | 21-indicator national forecast panel to 2030 (ARIMA/ETS, per-series AIC order, 95% CIs) |
| `outputs/data/Ghana_BurdenForecasting2030_MASTER_district.csv` | 261-district structural-vulnerability index, PCA components, Gi* classification |
| `outputs/data/hotspot_threshold_sensitivity.csv` | Hotspot/coldspot counts across 3 significance thresholds |
| `dashboard/Ghana_BurdenForecasting2030_Dashboard.html` | Interactive HI-EI dashboard (offline, self-contained) |
| `poster/Ghana_BurdenForecasting2030_Poster.html` | A0 conference poster (offline, self-contained) |

## 8a. Downloadable Artefacts (HTML)

| Artefact | View on GitHub | Live preview | Direct download |
|---|---|---|---|
| Interactive dashboard | [dashboard/Ghana_BurdenForecasting2030_Dashboard.html](https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/blob/main/dashboard/Ghana_BurdenForecasting2030_Dashboard.html) | [Preview](https://htmlpreview.github.io/?https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/blob/main/dashboard/Ghana_BurdenForecasting2030_Dashboard.html) | [Download](https://raw.githubusercontent.com/valentineghanem-bit/disease-burden-forecasting-ghana/main/dashboard/Ghana_BurdenForecasting2030_Dashboard.html) |
| Conference poster | [poster/Ghana_BurdenForecasting2030_Poster.html](https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/blob/main/poster/Ghana_BurdenForecasting2030_Poster.html) | [Preview](https://htmlpreview.github.io/?https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana/blob/main/poster/Ghana_BurdenForecasting2030_Poster.html) | [Download](https://raw.githubusercontent.com/valentineghanem-bit/disease-burden-forecasting-ghana/main/poster/Ghana_BurdenForecasting2030_Poster.html) |

## 9. Reporting Standard

STROBE (Strengthening the Reporting of Observational Studies in Epidemiology) for the observational national-panel and district cross-sectional components; RECORD-Spatial extension for the spatial clustering analysis (Getis-Ord Gi*/Moran's I).

## 10. Ethical Statement

This analysis uses exclusively public-domain, aggregate, de-identified secondary data (WHO, World Bank, USAID DHS StatCompiler, Ghana Statistical Service). No individual-level records were accessed at any point in this pipeline. This analysis is anticipated to qualify for a Ghana Health Service Ethics Review Board exemption as secondary analysis of de-identified, publicly available data.

## 11. Citation

Ghanem VG. Forecasting Ghana's National Health and Demographic Indicators to 2030, with District-Level Structural-Vulnerability Context: A Validated Multi-Indicator Time-Series Analysis. 2026.

```bibtex
@misc{ghanem2026burdenforecasting,
  author = {Ghanem, Valentine Golden},
  title  = {Forecasting Ghana's National Health and Demographic Indicators to 2030, with District-Level Structural-Vulnerability Context: A Validated Multi-Indicator Time-Series Analysis},
  year   = {2026},
  url    = {https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana}
}
```

See also `CITATION.cff` for machine-readable citation metadata.

## 12. License

Code: MIT License (see `LICENSE`). Outputs and figures: CC BY 4.0.

## 13. Author & Contact

Valentine Golden Ghanem, Ghana COCOBOD Cocoa Clinic, Accra, Ghana. Email: valentineghanem@gmail.com. ORCID: [0009-0002-8332-0220](https://orcid.org/0009-0002-8332-0220).

## 14. Acknowledgements

This project draws on internal corroborating context from 21 prior projects within the same research programme, each cited distinctly from external literature throughout the accompanying manuscript.
