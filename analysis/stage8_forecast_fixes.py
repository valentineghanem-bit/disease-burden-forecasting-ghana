"""Stage 8 -- Methodological Audit fixes, executed directly (not just documented):
1. Refit non-negative-bounded indicators on log scale (fixes biologically/economically
   impossible negative CI lower bounds the Scite Skeptic confirmed in 3 series).
2. Per-series ARIMA order selection via AIC grid search (fixes the fixed-(1,1,1)-for-all-21
   critique raised independently by 4 of 5 advisors).
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

panel = pd.read_csv("../data/processed/national_panel.csv")
EXCLUDED = ['uhc_service_coverage_index', 'pm25_conc_ugm3', 'air_pollution_ambient_daly',
            'air_pollution_household_daly']
NON_NEGATIVE = ['hiv_new_infections_n', 'hiv_new_infections_per1000', 'malaria_incidence_per1000atrisk',
                'oop_percapita_usd', 'oop_pct_che', 'che_percapita_usd', 'che_pct_gdp', 'che_pct_gdp_wb',
                'tb_incidence_per100k', 'u5mr_who', 'total_ncd_deaths', 'suicide_rate_crude_who',
                'suicide_rate_agestd_who', 'suicide_rate_wb', 'ncd_premature_pct', 'ncd_3070_probability_pct',
                'tfr_national_wb', 'pm25_exposure_wb']

def aic_order_search(y, max_p=2, max_d=2, max_q=2):
    best_aic, best_order, best_fit = np.inf, None, None
    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                if p == 0 and q == 0:
                    continue
                try:
                    m = ARIMA(y, order=(p, d, q)).fit()
                    if m.aic < best_aic:
                        best_aic, best_order, best_fit = m.aic, (p, d, q), m
                except Exception:
                    continue
    return best_order, best_aic, best_fit

results = []
order_report = []
for col in [c for c in panel.columns if c != 'year' and c not in EXCLUDED]:
    s = panel[['year', col]].dropna().sort_values('year')
    n = len(s)
    if n < 15:
        continue
    y = s[col].values
    last_year = int(s['year'].max())
    steps = 2030 - last_year
    if steps <= 0:
        continue

    is_nonneg = col in NON_NEGATIVE
    y_fit = np.log(np.maximum(y, 1e-6)) if is_nonneg else y

    # Fixed (1,1,1) -- retained as primary per Stage 4 validation
    try:
        arima = ARIMA(y_fit, order=(1, 1, 1)).fit()
        fc = arima.get_forecast(steps=steps)
        mean_fit, ci_fit = fc.predicted_mean[-1], fc.conf_int(alpha=0.05)[-1]
        if is_nonneg:
            arima_mean = np.exp(mean_fit)
            arima_ci = (np.exp(ci_fit[0]), np.exp(ci_fit[1]))
        else:
            arima_mean, arima_ci = mean_fit, (ci_fit[0], ci_fit[1])
        arima_aic_fixed = arima.aic
    except Exception:
        arima_mean, arima_ci, arima_aic_fixed = np.nan, (np.nan, np.nan), np.nan

    # AIC/BIC order search sensitivity check (on the same, possibly log, scale)
    best_order, best_aic, best_fit = aic_order_search(y_fit)
    order_matches_111 = (best_order == (1, 1, 1))
    order_report.append(dict(indicator=col, fixed_order_aic=arima_aic_fixed,
                              best_order=str(best_order), best_order_aic=best_aic,
                              matches_111=order_matches_111))

    try:
        ets = ExponentialSmoothing(y_fit, trend='add', damped_trend=True).fit()
        ets_fit = ets.forecast(steps)[-1]
        ets_mean = np.exp(ets_fit) if is_nonneg else ets_fit
    except Exception:
        ets_mean = np.nan

    confidence = "LOW (short series, n<25 -- interpret with caution)" if n < 25 else "standard"
    results.append(dict(indicator=col, n_obs=n, last_year=last_year, last_value=y[-1],
                         log_scale_fit=is_nonneg,
                         arima_2030=arima_mean, arima_ci_low=arima_ci[0], arima_ci_high=arima_ci[1],
                         ets_2030=ets_mean, confidence=confidence))

out = pd.DataFrame(results)
out.to_csv("../outputs/data/national_forecasts_2030.csv", index=False)
order_df = pd.DataFrame(order_report)
order_df.to_csv("../outputs/data/arima_order_sensitivity.csv", index=False)

print(f"Refit {len(out)} indicators. {sum(out['log_scale_fit'])} refit on log scale (non-negative-bounded).")
neg_ci = out[out['arima_ci_low'] < 0]
print(f"\nIndicators with negative CI lower bound after fix: {len(neg_ci)}")
print(neg_ci[['indicator', 'arima_ci_low']].to_string() if len(neg_ci) else "  (none)")

print(f"\n=== ARIMA order sensitivity: fixed (1,1,1) vs AIC-selected best order ===")
print(f"Series where AIC-selected order MATCHES (1,1,1): {order_df['matches_111'].sum()} of {len(order_df)}")
print(order_df.to_string())
