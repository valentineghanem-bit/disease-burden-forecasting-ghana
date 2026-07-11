"""Stage 6 -- Interpretation: publication figures.
Anti-slop standards applied (data-viz-pro / global CLAUDE.md Sec 16): colorblind-safe diverging
palette, title states the finding not the data type, no chartjunk, direct labels, 300 DPI.

NOTE (Plan A restructure, 2026-07-11): the previous fan-chart "worked-example forecasts" figure
and its supporting Table 5 were dropped from the manuscript per the accepted BMJ Public Health
restructuring plan (the paper's contribution is the workflow, not the forecasts themselves).
Figure numbering was reassigned: Figure 1 is now the reproducible-workflow diagram, Figure 2 is
the order-selection AICc-margin audit (unchanged content, retitled), Figure 3 is new (per-indicator
% change in the 2030 point forecast attributable to order selection), and Figure 4 is new
(walk-forward validation MAPE by method). The old fan-chart figure files were archived, not
deleted (../manuscript/figures/_archive/).
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 9, "font.family": "sans-serif"})

# ============ FIGURE 1: reproducible workflow diagram (schematic, no data) ============
fig1, ax = plt.subplots(figsize=(9, 3.6))
ax.set_xlim(0, 9)
ax.set_ylim(0, 3.2)
ax.axis("off")

steps = [
    (0.3, "Step 1\nSource-provenance audit",
     "Six documented corrections\n(HXL row, stratification,\nexport anomaly, re-exports)\n-> analysis-ready panel", "#0072b2"),
    (3.3, "Step 2\nMethod selection",
     "Walk-forward validation:\nclassical (ETS, ARIMA)\nvs. LSTM on 2 series", "#009e73"),
    (6.3, "Step 3\nOrder selection & fitting",
     "Per-series AICc order search;\nlog-scale fit for non-negative\nseries; 95% CI reported", "#cc79a7"),
]
box_w, box_h = 2.6, 2.6
for x, title, body, color in steps:
    ax.add_patch(plt.Rectangle((x, 0.3), box_w, box_h, facecolor=color, alpha=0.12,
                                edgecolor=color, linewidth=1.5))
    ax.text(x + box_w / 2, 0.3 + box_h - 0.35, title, ha="center", va="top",
            fontsize=9.5, fontweight="bold", color=color)
    ax.text(x + box_w / 2, 0.3 + box_h - 0.85, body, ha="center", va="top", fontsize=7.6)

for x0 in (0.3 + box_w, 3.3 + box_w):
    ax.annotate("", xy=(x0 + 0.3, 1.6), xytext=(x0, 1.6),
                arrowprops=dict(arrowstyle="-|>", lw=1.6, color="black"))

ax.text(4.5, 3.05, "Raw WHO GHO / World Bank exports  $\\rightarrow$  reliability-flagged 2030 forecasts",
        ha="center", va="top", fontsize=8.8, style="italic")
fig1.tight_layout()
fig1.savefig("../manuscript/figures/figure1_workflow_diagram.png", dpi=300, bbox_inches="tight")
fig1.savefig("../manuscript/figures/figure1_workflow_diagram.pdf", bbox_inches="tight")
print("Saved Figure 1 (workflow diagram, PNG + PDF)")

# ============ FIGURE 2: AICc margin vs uniform (1,1,1), all 21 series ============
margin = pd.read_csv("../outputs/data/aicc_margin_vs_uniform111.csv")
margin = margin.sort_values("delta_aicc", ascending=True)

LABELS_SHORT = {
    "life_expectancy_birth_yrs_who": "Life expectancy (WHO-GHO)",
    "hale_birth_yrs": "Healthy life expectancy",
    "u5mr_who": "Under-five mortality",
    "ncd_premature_pct": "NCD premature mortality",
    "ncd_3070_probability_pct": "NCD 30-70 death probability",
    "total_ncd_deaths": "Total NCD deaths",
    "suicide_rate_crude_who": "Suicide rate, crude (WHO-GHO)",
    "suicide_rate_agestd_who": "Suicide rate, age-std. (WHO-GHO)",
    "tb_incidence_per100k": "Tuberculosis incidence",
    "hiv_new_infections_n": "HIV new infections, n",
    "hiv_new_infections_per1000": "HIV new infections, per 1,000",
    "malaria_incidence_per1000atrisk": "Malaria incidence",
    "oop_pct_che": "Out-of-pocket exp., % of CHE",
    "oop_percapita_usd": "Out-of-pocket exp. per capita",
    "che_pct_gdp": "Current health exp., % GDP (WHO-GHO)",
    "che_percapita_usd": "Current health exp. per capita",
    "life_expectancy_birth_yrs_wb": "Life expectancy (World Bank)",
    "suicide_rate_wb": "Suicide rate (World Bank)",
    "che_pct_gdp_wb": "Current health exp., % GDP (World Bank)",
    "tfr_national_wb": "Total fertility rate (World Bank)",
    "pm25_exposure_wb": "PM2.5 exposure (World Bank)",
}
margin["label"] = margin["indicator"].map(LABELS_SHORT)

fig2, ax = plt.subplots(figsize=(7, 6.5))
colors = ["#0072b2" if nt else "#d55e00" for nt in margin["near_tie"]]
ax.barh(margin["label"], margin["delta_aicc"], color=colors, height=0.65)
ax.axvline(2, color="black", lw=1, ls=":", zorder=0)
ax.text(2.3, 0.4, "near-tie threshold\n(ΔAICc = 2)", fontsize=7, va="bottom")
ax.set_xlabel("AICc difference vs. uniform ARIMA(1,1,1) on the same data")
ax.set_title("Figure 2. Order-selection audit: most series diverge from a\nuniform order, and the largest correction is the panel's\nlongest series, not its shortest", fontsize=9.5, loc="left")
ax.spines[["top", "right"]].set_visible(False)
from matplotlib.patches import Patch
legend_elems = [Patch(facecolor="#0072b2", label="Near-tie (ΔAICc < 2): uniform order not decisively rejected"),
                Patch(facecolor="#d55e00", label="Decisive (ΔAICc ≥ 2): series-specific order clearly preferred")]
ax.legend(handles=legend_elems, fontsize=7, frameon=False, loc="lower right")
fig2.tight_layout()
fig2.savefig("../manuscript/figures/figure2_aicc_margin.png", dpi=300, bbox_inches="tight")
fig2.savefig("../manuscript/figures/figure2_aicc_margin.pdf", bbox_inches="tight")
print("Saved Figure 2 (AICc margin, PNG + PDF)")

# ============ FIGURE 3: % change in 2030 point forecast from order selection, by indicator ============
fc = pd.read_csv("../outputs/data/forecast_order_comparison.csv")
fc["label"] = fc["indicator"].map(LABELS_SHORT)
fc = fc.sort_values("pct_change", ascending=True)

fig3, ax = plt.subplots(figsize=(7, 6.5))
colors3 = ["#d55e00" if v >= 10 else "#0072b2" for v in fc["pct_change"]]
ax.barh(fc["label"], fc["pct_change"], color=colors3, height=0.65)
ax.set_xlabel("% change in 2030 point forecast: own-order vs. uniform ARIMA(1,1,1)")
ax.set_title("Figure 3. Order selection is negligible for most series but shifts\na minority (out-of-pocket exp., malaria, HIV) by more than 10%", fontsize=9.5, loc="left")
ax.spines[["top", "right"]].set_visible(False)
legend_elems3 = [Patch(facecolor="#0072b2", label="Change < 10%"),
                 Patch(facecolor="#d55e00", label="Change ≥ 10%")]
ax.legend(handles=legend_elems3, fontsize=7, frameon=False, loc="lower right")
fig3.tight_layout()
fig3.savefig("../manuscript/figures/figure3_forecast_pct_change.png", dpi=300, bbox_inches="tight")
fig3.savefig("../manuscript/figures/figure3_forecast_pct_change.pdf", bbox_inches="tight")
print("Saved Figure 3 (forecast % change by indicator, PNG + PDF)")

# ============ FIGURE 4: walk-forward validation, MAPE by method and series ============
wf = pd.read_csv("../outputs/data/walkforward_validation_results.csv").rename(columns={"Unnamed: 0": "indicator"})
WF_LABELS = {"u5mr_who": "Under-five mortality\n(long series, n=92)", "tb_incidence_per100k": "Tuberculosis incidence\n(short series, n=25)"}

fig4, axes4 = plt.subplots(1, 2, figsize=(8, 4), sharey=False)
methods = ["ets_mape", "arima_mape", "lstm_h8_mape", "lstm_h32_mape"]
method_labels = ["ETS", "ARIMA", "LSTM (h=8)", "LSTM (h=32)"]
method_colors = ["#0072b2", "#009e73", "#d55e00", "#cc79a7"]
seed_sd_cols = {"lstm_h8_mape": "lstm_h8_seed_sd", "lstm_h32_mape": "lstm_h32_seed_sd"}

for ax, (_, row) in zip(axes4, wf.iterrows()):
    vals = [row[m] for m in methods]
    errs = [0, 0, row["lstm_h8_seed_sd"] / row["lstm_h8_mae"] * row["lstm_h8_mape"] if row["lstm_h8_mae"] else 0,
            row["lstm_h32_seed_sd"] / row["lstm_h32_mae"] * row["lstm_h32_mape"] if row["lstm_h32_mae"] else 0]
    ax.bar(method_labels, vals, yerr=errs, color=method_colors, capsize=3)
    ax.set_title(WF_LABELS[row["indicator"]], fontsize=9)
    ax.set_ylabel("MAPE (%)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=7.5)

fig4.suptitle("Figure 4. LSTM does not outperform classical methods on either\nrepresentative series; error bars are across-seed MAPE (5 initializations)", fontsize=9.5, y=1.03)
fig4.tight_layout()
fig4.savefig("../manuscript/figures/figure4_walkforward_validation.png", dpi=300, bbox_inches="tight")
fig4.savefig("../manuscript/figures/figure4_walkforward_validation.pdf", bbox_inches="tight")
print("Saved Figure 4 (walk-forward validation, PNG + PDF)")
