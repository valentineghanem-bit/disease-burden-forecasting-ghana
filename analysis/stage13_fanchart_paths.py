"""Stage 13 -- extracts the actual year-by-year ARIMA forecast path (not just the 2030
endpoint) with 95% CI at each step, for the three headline Figure 1 series, addressing
reviewer m3 ('Figure 1's forecast path is a straight-line visual simplification ... show
the actual path with a fan chart')."""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.arima.model import ARIMA

panel = pd.read_csv("../data/processed/national_panel.csv")
sens = pd.read_csv("../outputs/data/arima_order_sensitivity.csv").set_index("indicator")

SERIES = ["u5mr_who", "tb_incidence_per100k", "malaria_incidence_per1000atrisk"]
# Must match stage8_forecast_fixes.py's NON_NEGATIVE list exactly -- all three headline
# series are log-scale fit in production (caught a bug here: an earlier version of this
# script only log-fit malaria, producing a 2030 point that silently disagreed with the
# verified Table 1 value for u5mr and TB).
NON_NEGATIVE = {"hiv_new_infections_n", "hiv_new_infections_per1000", "malaria_incidence_per1000atrisk",
    "oop_percapita_usd", "oop_pct_che", "che_percapita_usd", "che_pct_gdp", "che_pct_gdp_wb",
    "tb_incidence_per100k", "u5mr_who", "total_ncd_deaths", "suicide_rate_crude_who",
    "suicide_rate_agestd_who", "suicide_rate_wb", "ncd_premature_pct", "ncd_3070_probability_pct",
    "tfr_national_wb", "pm25_exposure_wb"}

rows = []
for col in SERIES:
    order = tuple(int(x) for x in sens.loc[col, "best_order"].strip("()").split(","))
    s = panel[["year", col]].dropna().sort_values("year")
    y = s[col].values
    last_year = int(s["year"].max())
    steps = 2030 - last_year
    is_nonneg = col in NON_NEGATIVE
    y_fit = np.log(np.maximum(y, 1e-6)) if is_nonneg else y
    m = ARIMA(y_fit, order=order).fit()
    fc = m.get_forecast(steps=steps)
    mean = fc.predicted_mean
    ci = fc.conf_int(alpha=0.05)
    for i in range(steps):
        yr = last_year + i + 1
        mu, lo, hi = mean[i], ci[i][0], ci[i][1]
        if is_nonneg:
            mu, lo, hi = np.exp(mu), np.exp(lo), np.exp(hi)
        rows.append(dict(indicator=col, year=yr, mean=mu, ci_low=lo, ci_high=hi))

out = pd.DataFrame(rows)
out.to_csv("../outputs/data/figure1_fanchart_paths.csv", index=False)
print(out.to_string(index=False))
print("Saved: ../outputs/data/figure1_fanchart_paths.csv")
