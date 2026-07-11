"""Stage 9 -- generates the LaTeX source for Table 2 (order-selection sensitivity, all 21
series) and Table 3 (walk-forward validation, LSTM vs classical) directly from the real,
already-computed output CSVs, to avoid hand-transcription drift. Prints LaTeX fragments to
paste into main.tex; does not edit main.tex itself (kept as a reviewable intermediate step,
consistent with how Table 1's values were independently verified against source CSVs earlier
in this project).
"""
import pandas as pd

ROOT = r"C:\Users\VGhanem\Documents\Claude\Projects\Public Health & Epidemiology Research Skills\23. Disease Burden Forecasting Ghana"

LABELS = {
    "life_expectancy_birth_yrs_who": "Life expectancy at birth (WHO-GHO), yrs",
    "hale_birth_yrs": "Healthy life expectancy at birth, yrs",
    "u5mr_who": "Under-five mortality rate, per 1{,}000",
    "ncd_premature_pct": "NCD premature mortality, \\%",
    "ncd_3070_probability_pct": "NCD 30--70 death probability, \\%",
    "total_ncd_deaths": "Total NCD deaths, $n$",
    "suicide_rate_crude_who": "Suicide rate (crude, WHO-GHO), per 100{,}000",
    "suicide_rate_agestd_who": "Suicide rate (age-std., WHO-GHO), per 100{,}000",
    "tb_incidence_per100k": "Tuberculosis incidence, per 100{,}000",
    "hiv_new_infections_n": "HIV new infections, $n$",
    "hiv_new_infections_per1000": "HIV new infections, per 1{,}000",
    "malaria_incidence_per1000atrisk": "Malaria incidence, per 1{,}000 at risk",
    "oop_pct_che": "Out-of-pocket exp., \\% of CHE",
    "oop_percapita_usd": "Out-of-pocket exp.\\ per capita, USD",
    "che_pct_gdp": "Current health exp., \\% GDP (WHO-GHO)",
    "che_percapita_usd": "Current health exp.\\ per capita, USD",
    "life_expectancy_birth_yrs_wb": "Life expectancy at birth (World Bank), yrs",
    "suicide_rate_wb": "Suicide rate (World Bank), per 100{,}000",
    "che_pct_gdp_wb": "Current health exp., \\% GDP (World Bank)",
    "tfr_national_wb": "Total fertility rate (World Bank), births/woman",
    "pm25_exposure_wb": "PM\\textsubscript{2.5} exposure (World Bank), $\\mu$g/m$^3$",
}
# Table 1's own row order (for consistent presentation across tables)
ROW_ORDER = list(LABELS.keys())

order_cmp = pd.read_csv(ROOT + r"\outputs\data\forecast_order_comparison.csv")
sens = pd.read_csv(ROOT + r"\outputs\data\arima_order_sensitivity.csv")
margin = pd.read_csv(ROOT + r"\outputs\data\aicc_margin_vs_uniform111.csv")
merged = order_cmp.merge(sens[["indicator", "best_order"]], on="indicator") \
                   .merge(margin[["indicator", "delta_aicc", "near_tie"]], on="indicator")
merged = merged.set_index("indicator").loc[ROW_ORDER].reset_index()

def fmt_val(ind, v):
    is_count = ind in ("total_ncd_deaths", "hiv_new_infections_n")
    return f"{v:,.0f}" if is_count else f"{v:,.2f}"

print("=" * 20, "TABLE 3 LaTeX (order-comparison; numbered after the walk-forward table since it is discussed second in Methods)", "=" * 20)
print(r"""\begin{table}[htbp]
\centering
\caption{Sensitivity of each series' 2030 point forecast to model-order selection: a uniform ARIMA(1,1,1) specification versus each series' own AICc-selected order, fit on the same scale (log or raw) used for that series' final production forecast (Methods). This isolates the effect of order selection alone, holding the log/raw-scale decision fixed; it is therefore not the same comparison as the raw-scale, pre-any-correction malaria baseline (94.6 ARIMA / 125.0 exponential smoothing) quoted in the Discussion, which reflects the combined effect of both the log-scale refit and the order-selection correction together (see Discussion, ``The malaria forecast'').}
\label{tab:table3}
\resizebox{\textwidth}{!}{%
\begin{tabular}{lccrrrc}
\toprule
Indicator & Order used & $\Delta$AICc vs.\ (1,1,1) & Fixed-(1,1,1) 2030 & Own-order 2030 & \% change & Near-tie \\
\midrule""")
for _, row in merged.iterrows():
    order_str = str(row["best_order"]).replace("(", "(").replace(")", ")").replace(", ", ",")
    fixed_v = fmt_val(row["indicator"], row["fixed_111_2030"])
    own_v = fmt_val(row["indicator"], row["aic_optimal_2030"])
    pct = f"{row['pct_change']:.1f}"
    delta = f"{row['delta_aicc']:.2f}" if row["delta_aicc"] >= 0 else f"$-${abs(row['delta_aicc']):.2f}"
    tie = "Yes" if row["near_tie"] else "No"
    print(f"{LABELS[row['indicator']]} & ({order_str[1:-1]}) & {delta} & {fixed_v} & {own_v} & {pct} & {tie} \\\\")
print(r"""\bottomrule
\end{tabular}%
}
\end{table}
""")

print("=" * 20, "TABLE 2 LaTeX (walk-forward validation; discussed first in Methods)", "=" * 20)
wf = pd.read_csv(ROOT + r"\outputs\data\walkforward_validation_results.csv")
wf = wf.rename(columns={"Unnamed: 0": "indicator"})
WF_LABELS = {"u5mr_who": "Under-five mortality (long series)", "tb_incidence_per100k": "Tuberculosis incidence (short series)"}
print(r"""\begin{table}[htbp]
\centering
\caption{Walk-forward validation of classical versus LSTM forecasting methods on two representative series (Methods). MAPE = mean absolute percentage error, seed-averaged across five independent LSTM initializations per fold and hidden-layer size; SD = across-seed standard deviation of the raw (non-percentage) mean absolute error, reported on the original series' units.}
\label{tab:table2}
\resizebox{\textwidth}{!}{%
\begin{tabular}{lcccccc}
\toprule
Series & $n$ & Folds & ETS MAPE (\%) & ARIMA MAPE (\%) & LSTM$_{h=8}$ MAPE (\%) & LSTM$_{h=32}$ MAPE (\%) \\
\midrule""")
for _, row in wf.iterrows():
    # NOTE: *_mape columns in walkforward_validation_results.csv are already expressed as
    # percentage values (14.08 means 14.08%), not 0-1 fractions -- confirmed by cross-checking
    # against the manuscript's already-published "14.1% [hidden=8]... 0.18-0.29% for ETS/ARIMA"
    # figures, which only match this column's raw values, not the value x100.
    print(f"{WF_LABELS[row['indicator']]} & {int(row['n'])} & {int(row['folds'])} & "
          f"{row['ets_mape']:.2f} & {row['arima_mape']:.2f} & "
          f"{row['lstm_h8_mape']:.2f} $\\pm$ {row['lstm_h8_seed_sd']:.2f}\\textsuperscript{{a}} & "
          f"{row['lstm_h32_mape']:.2f} $\\pm$ {row['lstm_h32_seed_sd']:.2f}\\textsuperscript{{a}} \\\\")
print(r"""\bottomrule
\end{tabular}%
}
\end{table}
\textsuperscript{a}Standard deviation of the raw mean absolute error across five random LSTM initializations (original series' units, not MAPE).
""")
