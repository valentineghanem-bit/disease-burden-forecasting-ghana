"""Stage 9 -- computes and saves, as a permanent reproducible artefact, the AICc margin
between each series' own selected order and a fixed-(1,1,1) refit on the same data. This
was originally computed ad hoc during the Phase 9 conceptual audit (verifying whether the
"1 of 21 matched (1,1,1)" headline finding is uniformly decisive or includes near-ties) but
never saved as a file -- re-running it here so Table 2 and Figure 2 have a real, checked-in
data source rather than a number quoted from an earlier interactive session.
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

rows = []
for col in [c for c in panel.columns if c != 'year' and c not in EXCLUDED]:
    s = panel[['year', col]].dropna().sort_values('year')
    n = len(s)
    if n < 15:
        continue
    y = s[col].values
    is_nonneg = col in NON_NEGATIVE
    y_fit = np.log(np.maximum(y, 1e-6)) if is_nonneg else y
    try:
        m = ARIMA(y_fit, order=(1, 1, 1)).fit()
        converged = m.mle_retvals.get("converged", True) if hasattr(m, "mle_retvals") and m.mle_retvals else True
        k = m.df_model  # FIXED (Phase 12 council, 2026-07-11): was +1, double-counting sigma2
        fixed_aicc = aicc(m.aic, n, k)
    except Exception:
        fixed_aicc, converged = np.nan, None
    row = sens[sens['indicator'] == col]
    best_aicc = row['best_order_aicc'].values[0] if len(row) else np.nan
    best_order = row['best_order'].values[0] if len(row) else None
    delta = fixed_aicc - best_aicc if pd.notna(fixed_aicc) else np.nan
    rows.append(dict(indicator=col, n_obs=n, best_order=best_order, fixed_111_converged=converged,
                      fixed_111_aicc=fixed_aicc, best_order_aicc=best_aicc, delta_aicc=delta,
                      near_tie=bool(pd.notna(delta) and delta < 2)))

out = pd.DataFrame(rows).sort_values("delta_aicc", ascending=False)
out.to_csv("../outputs/data/aicc_margin_vs_uniform111.csv", index=False)
print(out.to_string(index=False))
print()
print(f"Near-tie (delta AICc < 2): {out['near_tie'].sum()} of {len(out)}")
print(f"Decisive (delta AICc >= 2): {(~out['near_tie']).sum()} of {len(out)}")
print("Saved: ../outputs/data/aicc_margin_vs_uniform111.csv")
