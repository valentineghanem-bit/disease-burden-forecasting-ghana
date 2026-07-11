"""Stage 8 final production forecasts: use each series' own AIC-optimal ARIMA order
(from arima_order_sensitivity.csv) rather than a fixed (1,1,1) applied uniformly.
Non-negative-bounded indicators fit on log scale (fixes the negative-CI defect).
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import ast

panel = pd.read_csv("../data/processed/national_panel.csv")
order_df = pd.read_csv("../outputs/data/arima_order_sensitivity.csv")
order_map = dict(zip(order_df['indicator'], order_df['best_order'].apply(ast.literal_eval)))

EXCLUDED = ['uhc_service_coverage_index', 'pm25_conc_ugm3', 'air_pollution_ambient_daly', 'air_pollution_household_daly']
NON_NEGATIVE = ['hiv_new_infections_n', 'hiv_new_infections_per1000', 'malaria_incidence_per1000atrisk',
                'oop_percapita_usd', 'oop_pct_che', 'che_percapita_usd', 'che_pct_gdp', 'che_pct_gdp_wb',
                'tb_incidence_per100k', 'u5mr_who', 'total_ncd_deaths', 'suicide_rate_crude_who',
                'suicide_rate_agestd_who', 'suicide_rate_wb', 'ncd_premature_pct', 'ncd_3070_probability_pct',
                'tfr_national_wb', 'pm25_exposure_wb']

results = []
comparison = []
for col, best_order in order_map.items():
    s = panel[['year', col]].dropna().sort_values('year')
    n = len(s)
    y = s[col].values
    last_year = int(s['year'].max())
    steps = 2030 - last_year
    if steps <= 0:
        continue

    is_nonneg = col in NON_NEGATIVE
    y_fit = np.log(np.maximum(y, 1e-6)) if is_nonneg else y

    # Fixed (1,1,1), for comparison
    try:
        m_fixed = ARIMA(y_fit, order=(1, 1, 1)).fit()
        fc_fixed = m_fixed.get_forecast(steps=steps).predicted_mean[-1]
        fixed_2030 = np.exp(fc_fixed) if is_nonneg else fc_fixed
    except Exception:
        fixed_2030 = np.nan

    # AIC-optimal order, final production forecast
    try:
        m_best = ARIMA(y_fit, order=best_order).fit()
        fc_best = m_best.get_forecast(steps=steps)
        best_mean, best_ci = fc_best.predicted_mean[-1], fc_best.conf_int(alpha=0.05)[-1]
        if is_nonneg:
            best_2030, ci_low, ci_high = np.exp(best_mean), np.exp(best_ci[0]), np.exp(best_ci[1])
        else:
            best_2030, ci_low, ci_high = best_mean, best_ci[0], best_ci[1]
    except Exception:
        best_2030, ci_low, ci_high = np.nan, np.nan, np.nan

    try:
        ets = ExponentialSmoothing(y_fit, trend='add', damped_trend=True).fit()
        ets_fit = ets.forecast(steps)[-1]
        ets_2030 = np.exp(ets_fit) if is_nonneg else ets_fit
    except Exception:
        ets_2030 = np.nan

    pct_change = abs(best_2030 - fixed_2030) / abs(fixed_2030) * 100 if fixed_2030 not in (0, np.nan) and not np.isnan(fixed_2030) else np.nan
    comparison.append(dict(indicator=col, order_used=str(best_order), fixed_111_2030=fixed_2030,
                            aic_optimal_2030=best_2030, pct_change=pct_change))

    confidence = "LOW (short series, n<25 -- interpret with caution)" if n < 25 else "standard"
    results.append(dict(indicator=col, n_obs=n, last_year=last_year, last_value=y[-1],
                         arima_order=str(best_order), log_scale_fit=is_nonneg,
                         arima_2030=best_2030, arima_ci_low=ci_low, arima_ci_high=ci_high,
                         ets_2030=ets_2030, confidence=confidence))

out = pd.DataFrame(results)
out.to_csv("../outputs/data/national_forecasts_2030.csv", index=False)
# Also publish as the Master CSV deliverable, so this one script is the sole source of both
# files and they can never drift apart (Phase 12 finding: the Master CSV had been hand-copied
# once and gone stale after a later methodological correction re-ran this script alone).
out.to_csv("../outputs/data/Ghana_BurdenForecasting2030_MASTER_national.csv", index=False)
comp_df = pd.DataFrame(comparison)
comp_df.to_csv("../outputs/data/forecast_order_comparison.csv", index=False)

print("Final production forecasts (AIC-optimal order per series):")
print(out[['indicator', 'arima_order', 'arima_2030', 'arima_ci_low', 'arima_ci_high', 'ets_2030']].to_string())
print(f"\nMax negative CI check: {(out['arima_ci_low'] < 0).sum()} indicators with negative CI lower bound")
print(f"\nForecast change from fixed (1,1,1) to AIC-optimal order (top 5 by % change):")
print(comp_df.sort_values('pct_change', ascending=False).head(5).to_string())
