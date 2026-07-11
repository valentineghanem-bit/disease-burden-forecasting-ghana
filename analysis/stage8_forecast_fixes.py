"""Stage 8 -- Methodological Audit fixes, executed directly (not just documented):
1. Refit non-negative-bounded indicators on log scale (fixes biologically/economically
   impossible negative CI lower bounds the Scite Skeptic confirmed in 3 series).
2. Per-series ARIMA order selection via AICc grid search (fixes the fixed-(1,1,1)-for-all-21
   critique raised independently by 4 of 5 advisors), now using the small-sample-corrected
   AICc rather than plain AIC (Phase 8 re-audit, 2026-07-10: the Spatial & ML Auditor and
   Scite Skeptic both flagged that plain AIC is not an adequate small-sample criterion at
   n/k ratios of ~6-8 seen in several of this panel's short series; AICc's extra small-sample
   penalty term was added), and now excluding non-converged fits explicitly (the run log
   showed ConvergenceWarning instances that the prior version's except-on-Exception-only
   logic did not catch, since a non-converged fit does not raise an exception).
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

def aicc(aic, n, k):
    """Small-sample-corrected AIC (Hurvich & Tsai 1989). k = number of estimated parameters.
    BUG FIX (Phase 12 council, 2026-07-11): k = m.df_model directly, NOT m.df_model + 1.
    Verified empirically: statsmodels' own reported .aic exactly equals -2*llf + 2*df_model
    for an ARIMA fit (confirmed to machine precision), proving df_model already counts sigma2
    as an estimated parameter -- the original "+1 for sigma2" comment and code were wrong,
    silently overcounting k by 1 for every candidate order in every grid search this project
    has run. Because the AICc penalty 2k(k+1)/(n-k-1) is nonlinear in k, this was not a
    constant offset that cancelled across candidates -- it could and did change which order
    was selected as AICc-optimal for some series (re-verified after this fix; see
    docs/stage8_aicc_k_bugfix.md for the full before/after comparison)."""
    denom = n - k - 1
    if denom <= 0:
        return np.inf  # AICc undefined/unstable when n <= k+1; treat as worst-possible
    return aic + (2 * k * (k + 1)) / denom

def aic_order_search(y, max_p=2, max_d=2, max_q=2):
    n = len(y)
    best_aicc, best_order, best_fit, best_aic = np.inf, None, None, None
    n_nonconverged = 0
    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                if p == 0 and q == 0:
                    continue
                try:
                    m = ARIMA(y, order=(p, d, q)).fit()
                    converged = m.mle_retvals.get("converged", True) if hasattr(m, "mle_retvals") and m.mle_retvals else True
                    if not converged:
                        n_nonconverged += 1
                        continue
                    k = m.df_model  # FIXED (was + 1, double-counting sigma2 -- see aicc() docstring)
                    c = aicc(m.aic, n, k)
                    if c < best_aicc:
                        best_aicc, best_order, best_fit, best_aic = c, (p, d, q), m, m.aic
                except Exception:
                    continue
    return best_order, best_aic, best_aicc, best_fit, n_nonconverged

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

    # AICc order search sensitivity check (on the same, possibly log, scale), non-converged fits excluded
    best_order, best_aic, best_aicc, best_fit, n_nonconverged = aic_order_search(y_fit)
    order_matches_111 = (best_order == (1, 1, 1))
    order_report.append(dict(indicator=col, n_obs=n, fixed_order_aic=arima_aic_fixed,
                              best_order=str(best_order), best_order_aic=best_aic,
                              best_order_aicc=best_aicc, n_nonconverged_excluded=n_nonconverged,
                              matches_111=order_matches_111))

    try:
        ets = ExponentialSmoothing(y_fit, trend='add', damped_trend=True).fit()
        ets_fit = ets.forecast(steps)[-1]
        ets_mean = np.exp(ets_fit) if is_nonneg else ets_fit
    except Exception:
        ets_mean = np.nan

    confidence = "LOW (short series, n<25 -- interpret with caution)" if n < 25 else "standard"
    results.append(dict(indicator=col, n_obs=n, last_year=last_year, last_value=y[-1],
                         arima_order=str(best_order), log_scale_fit=is_nonneg,
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

print(f"\n=== ARIMA order sensitivity: fixed (1,1,1) vs AICc-selected best order ===")
print(f"Series where AICc-selected order MATCHES (1,1,1): {order_df['matches_111'].sum()} of {len(order_df)}")
print(f"Total non-converged fits excluded across all series/orders: {order_df['n_nonconverged_excluded'].sum()}")
print(order_df.to_string())
