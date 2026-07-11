"""Stage 13 -- structural-break sensitivity analysis (Plan A restructure, reviewer M5).

Tests whether a level-shift dummy at the 2020 COVID-19 onset or the 2022 Ghana
macroeconomic/currency-crisis onset materially improves each series' fit relative to
the baseline (no-intervention) AICc-selected ARIMA order, and how much the 2030 point
forecast changes if the break is modelled. Honestly reports where the test is
underpowered (few post-break observations) rather than only where it succeeds.
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.arima.model import ARIMA

def aicc(aic, n, k):
    denom = n - k - 1
    if denom <= 0:
        return np.inf
    return aic + (2 * k * (k + 1)) / denom

panel = pd.read_csv("../data/processed/national_panel.csv")
sens = pd.read_csv("../outputs/data/arima_order_sensitivity.csv")
EXCLUDED = ['uhc_service_coverage_index', 'pm25_conc_ugm3', 'air_pollution_ambient_daly',
            'air_pollution_household_daly']
NON_NEGATIVE = ['hiv_new_infections_n', 'hiv_new_infections_per1000', 'malaria_incidence_per1000atrisk',
    'oop_percapita_usd', 'oop_pct_che', 'che_percapita_usd', 'che_pct_gdp', 'che_pct_gdp_wb',
    'tb_incidence_per100k', 'u5mr_who', 'total_ncd_deaths', 'suicide_rate_crude_who',
    'suicide_rate_agestd_who', 'suicide_rate_wb', 'ncd_premature_pct', 'ncd_3070_probability_pct',
    'tfr_national_wb', 'pm25_exposure_wb']

def parse_order(s):
    return tuple(int(x) for x in s.strip("()").split(","))

rows = []
for _, srow in sens.iterrows():
    col = srow["indicator"]
    if col in EXCLUDED:
        continue
    order = parse_order(srow["best_order"])
    s = panel[["year", col]].dropna().sort_values("year")
    n = len(s)
    years = s["year"].values
    y = s[col].values
    is_nonneg = col in NON_NEGATIVE
    y_fit = np.log(np.maximum(y, 1e-6)) if is_nonneg else y

    # baseline (no intervention), own AICc-selected order, refit here for a clean AICc comparison
    try:
        m0 = ARIMA(y_fit, order=order).fit()
        k0 = m0.df_model  # FIXED (Phase 12 council, 2026-07-11): was +1, double-counting sigma2 --
        # verified empirically that statsmodels' own .aic equals -2*llf + 2*df_model exactly.
        aicc0 = aicc(m0.aic, n, k0)
    except Exception:
        aicc0 = np.inf

    result = dict(indicator=col, n_obs=n, order=str(order), baseline_aicc=aicc0)

    for break_year, label in [(2020, "covid_2020"), (2022, "currency_2022")]:
        n_post = int((years >= break_year).sum())
        n_pre = n - n_post
        if n_post < 2 or n_pre < 5 or years.max() < break_year:
            result[f"{label}_n_post"] = n_post
            result[f"{label}_testable"] = False
            result[f"{label}_delta_aicc"] = np.nan
            result[f"{label}_pct_change_2030"] = np.nan
            continue
        dummy = (years >= break_year).astype(float).reshape(-1, 1)
        try:
            m1 = ARIMA(y_fit, order=order, exog=dummy).fit()
            k1 = m1.df_model  # FIXED -- see k0 above; verified the exog case too (df_model
            # correctly increments by 1 per added regressor and statsmodels' aic still equals
            # -2*llf + 2*df_model exactly with exog present).
            aicc1 = aicc(m1.aic, n, k1)
            steps = 2030 - int(years.max())
            fc_exog = np.ones((steps, 1))
            fc0 = m0.get_forecast(steps=steps).predicted_mean[-1]
            fc1 = m1.get_forecast(steps=steps, exog=fc_exog).predicted_mean[-1]
            if is_nonneg:
                fc0, fc1 = np.exp(fc0), np.exp(fc1)
            pct_change = (fc1 - fc0) / fc0 * 100 if fc0 != 0 else np.nan
            result[f"{label}_n_post"] = n_post
            result[f"{label}_testable"] = True
            result[f"{label}_delta_aicc"] = aicc0 - aicc1  # positive = intervention model preferred
            result[f"{label}_pct_change_2030"] = pct_change
        except Exception:
            result[f"{label}_n_post"] = n_post
            result[f"{label}_testable"] = False
            result[f"{label}_delta_aicc"] = np.nan
            result[f"{label}_pct_change_2030"] = np.nan
    rows.append(result)

out = pd.DataFrame(rows)
out.to_csv("../outputs/data/structural_break_sensitivity.csv", index=False)
pd.set_option("display.width", 200)
print(out.to_string(index=False))
print()
testable_covid = out[out["covid_2020_testable"]]
testable_currency = out[out["currency_2022_testable"]]
print(f"COVID-2020 break testable for {len(testable_covid)} of {len(out)} series")
print(f"  of those, intervention model preferred (delta AICc > 2) for: "
      f"{(testable_covid['covid_2020_delta_aicc'] > 2).sum()}")
print(f"Currency-2022 break testable for {len(testable_currency)} of {len(out)} series")
print(f"  of those, intervention model preferred (delta AICc > 2) for: "
      f"{(testable_currency['currency_2022_delta_aicc'] > 2).sum()}")
print("Saved: ../outputs/data/structural_break_sensitivity.csv")
