"""Stage 5 -- Synthesis: produce the actual 2030 national forecasts using the Stage 4-locked
methodology (ARIMA/ETS primary pair; LSTM fully excluded). Series with n<15 (UHC Service Coverage
Index n=7; air-pollution indicators n=10) are EXCLUDED from formal forecasting -- per the standing
Stage 0 scoping, these remain descriptive/contextual only, consistent with not fabricating
confidence in a forecast the data cannot support. Series with 15<=n<25 receive a forecast but are
explicitly flagged low-confidence/short-series per the Stage 1 tiering rule.
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

panel = pd.read_csv("../data/processed/national_panel.csv")
HORIZON_YEARS = list(range(2025, 2031))  # forecast to 2030

EXCLUDED = ['uhc_service_coverage_index', 'pm25_conc_ugm3', 'air_pollution_ambient_daly',
            'air_pollution_household_daly']

forecast_targets = [c for c in panel.columns if c != 'year' and c not in EXCLUDED]

results = []
for col in forecast_targets:
    s = panel[['year', col]].dropna().sort_values('year')
    n = len(s)
    if n < 15:
        continue
    y = s[col].values
    last_year = int(s['year'].max())
    steps = 2030 - last_year
    if steps <= 0:
        continue

    try:
        arima = ARIMA(y, order=(1, 1, 1)).fit()
        arima_fc = arima.get_forecast(steps=steps)
        arima_mean = arima_fc.predicted_mean[-1]
        arima_ci = arima_fc.conf_int(alpha=0.05)[-1]
    except Exception as e:
        arima_mean, arima_ci = np.nan, (np.nan, np.nan)

    try:
        ets = ExponentialSmoothing(y, trend='add', damped_trend=True).fit()
        ets_fc = ets.forecast(steps)
        ets_mean = ets_fc[-1]
    except Exception:
        ets_mean = np.nan

    confidence = "LOW (short series, n<25 -- interpret with caution)" if n < 25 else "standard"
    results.append(dict(
        indicator=col, n_obs=n, last_year=last_year, last_value=y[-1],
        arima_2030=arima_mean, arima_ci_low=arima_ci[0], arima_ci_high=arima_ci[1],
        ets_2030=ets_mean, confidence=confidence
    ))

out = pd.DataFrame(results)
out.to_csv("../outputs/data/national_forecasts_2030.csv", index=False)
print(f"Forecast {len(out)} indicators to 2030 (excluded {len(EXCLUDED)} as too sparse for formal forecasting: {EXCLUDED})")
print(out[['indicator', 'n_obs', 'last_year', 'last_value', 'arima_2030', 'ets_2030', 'confidence']].to_string())
