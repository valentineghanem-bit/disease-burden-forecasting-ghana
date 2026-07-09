"""Stage 6 -- Interpretation: publication figures.
Anti-slop standards applied (data-viz-pro / global CLAUDE.md Sec 16): colorblind-safe diverging
palette, title states the finding not the data type, no chartjunk, direct labels, 300 DPI.
"""
import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from shapely.geometry import shape
import geopandas as gpd

plt.rcParams.update({"font.size": 9, "font.family": "sans-serif"})

# ============ FIGURE 1: District structural vulnerability + Gi* hotspots ============
df = pd.read_csv("../data/processed/district_vulnerability_index.csv")
gistar_df = pd.read_csv("../outputs/data/vulnerability_gistar_results.csv")
cw = pd.read_csv("../docs/district_crosswalk_261_to_260.csv")
with open("../data/raw/Ghana_New_260_District.geojson", encoding="utf-8") as fh:
    gj = json.load(fh)

gdf = gpd.GeoDataFrame.from_features(gj["features"])
ms_map = cw.set_index("geojson_district")["master_sheet_district"].to_dict()
gdf["ms_district"] = gdf["DISTRICT"].map(ms_map)
gdf = gdf.merge(df[["district", "vulnerability_pc1"]], left_on="ms_district", right_on="district", how="left")
gdf = gdf.merge(gistar_df[["district", "gistar_z"]], left_on="ms_district", right_on="district", how="left", suffixes=("", "_g"))

fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))

# Panel A: PC1 choropleth (diverging, colorblind-safe: PuOr)
ax = axes[0]
norm = TwoSlopeNorm(vmin=gdf["vulnerability_pc1"].min(), vcenter=0, vmax=gdf["vulnerability_pc1"].max())
gdf.plot(column="vulnerability_pc1", cmap="PuOr_r", linewidth=0.15, edgecolor="white",
         ax=ax, norm=norm, missing_kwds={"color": "lightgrey", "label": "No data"})
sm = plt.cm.ScalarMappable(cmap="PuOr_r", norm=norm)
cbar = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02)
cbar.set_label("Structural vulnerability (PC1, standardized)", fontsize=8)
ax.set_title("A. Poverty, illiteracy, and dependency cluster\nin northern districts", fontsize=10, loc="left")
ax.axis("off")

# Panel B: Gi* classification (categorical, colorblind-safe: hotspot=vermillion, coldspot=blue, NS=grey)
ax = axes[1]
def classify(z):
    if pd.isna(z):
        return "No data"
    if z > 1.96:
        return "Hotspot (p<0.05)"
    elif z < -1.96:
        return "Coldspot (p<0.05)"
    else:
        return "Not significant"
gdf["gistar_class"] = gdf["gistar_z"].apply(classify)
colors = {"Hotspot (p<0.05)": "#d55e00", "Coldspot (p<0.05)": "#0072b2",
          "Not significant": "#e0e0e0", "No data": "#f7f7f7"}
from matplotlib.patches import Patch
legend_handles = []
for cls, color in colors.items():
    sub = gdf[gdf["gistar_class"] == cls]
    if len(sub) > 0:
        sub.plot(ax=ax, color=color, linewidth=0.15, edgecolor="white")
        legend_handles.append(Patch(facecolor=color, edgecolor="none", label=cls))
ax.legend(handles=legend_handles, loc="lower left", fontsize=7, frameon=False)
ax.set_title("B. 6 hotspot districts at p<0.05 -- but this count\ntriples to 20 at p<0.10 (see Discussion)", fontsize=10, loc="left")
ax.axis("off")

fig.suptitle("Figure 1. District structural vulnerability index and local spatial clustering (Getis-Ord Gi*, N=255 of 261 districts)", fontsize=10, y=1.02)
fig.tight_layout()
fig.savefig("../manuscript/figures/figure1_vulnerability_hotspots.png", dpi=300, bbox_inches="tight")
fig.savefig("../manuscript/figures/figure1_vulnerability_hotspots.pdf", bbox_inches="tight")
print("Saved Figure 1 (PNG + PDF)")

# ============ FIGURE 2: National forecast trends ============
panel = pd.read_csv("../data/processed/national_panel.csv")
fc = pd.read_csv("../outputs/data/national_forecasts_2030.csv")

fig2, axes2 = plt.subplots(1, 3, figsize=(13, 4))

# Panel A: U5MR with SDG 3.2 line
ax = axes2[0]
s = panel[["year", "u5mr_who"]].dropna()
ax.plot(s["year"], s["u5mr_who"], color="#0072b2", lw=1.8, label="Observed")
row = fc[fc["indicator"] == "u5mr_who"].iloc[0]
ax.plot([s["year"].max(), 2030], [s["u5mr_who"].iloc[-1], row["arima_2030"]], "--", color="#0072b2", lw=1.5, label="ARIMA forecast")
ax.axhline(25, color="#d55e00", lw=1.2, ls=":", label="SDG 3.2 target (25/1,000)")
ax.set_title("A. Under-5 mortality narrowly misses\nthe 2030 SDG target", fontsize=9.5, loc="left")
ax.set_ylabel("Deaths per 1,000 live births")
ax.legend(fontsize=6.5, frameon=False)
ax.spines[["top", "right"]].set_visible(False)

# Panel B: TB incidence
ax = axes2[1]
s = panel[["year", "tb_incidence_per100k"]].dropna()
ax.plot(s["year"], s["tb_incidence_per100k"], color="#009e73", lw=1.8, label="Observed")
row = fc[fc["indicator"] == "tb_incidence_per100k"].iloc[0]
ax.plot([s["year"].max(), 2030], [s["tb_incidence_per100k"].iloc[-1], row["arima_2030"]], "--", color="#009e73", lw=1.5, label="ARIMA forecast")
ax.set_title("B. TB incidence continues its\n2000-2024 decline", fontsize=9.5, loc="left")
ax.set_ylabel("Cases per 100,000 population")
ax.legend(fontsize=6.5, frameon=False)
ax.spines[["top", "right"]].set_visible(False)

# Panel C: Malaria - show BOTH models diverging (honest disclosure)
ax = axes2[2]
s = panel[["year", "malaria_incidence_per1000atrisk"]].dropna()
ax.plot(s["year"], s["malaria_incidence_per1000atrisk"], color="#cc79a7", lw=1.8, label="Observed")
row = fc[fc["indicator"] == "malaria_incidence_per1000atrisk"].iloc[0]
ax.plot([s["year"].max(), 2030], [s["malaria_incidence_per1000atrisk"].iloc[-1], row["arima_2030"]], "--", color="#cc79a7", lw=1.5, label="ARIMA")
ax.plot([s["year"].max(), 2030], [s["malaria_incidence_per1000atrisk"].iloc[-1], row["ets_2030"]], ":", color="#cc79a7", lw=1.5, label="Exp. smoothing")
ax.set_title("C. Malaria forecast: model gap narrowed\nby correct order selection (see Discussion)", fontsize=9.5, loc="left")
ax.set_ylabel("Cases per 1,000 population at risk")
ax.legend(fontsize=6.5, frameon=False)
ax.spines[["top", "right"]].set_visible(False)

fig2.suptitle("Figure 2. National indicator trends and 2030 forecasts", fontsize=10, y=1.03)
fig2.tight_layout()
fig2.savefig("../manuscript/figures/figure2_national_forecasts.png", dpi=300, bbox_inches="tight")
fig2.savefig("../manuscript/figures/figure2_national_forecasts.pdf", bbox_inches="tight")
print("Saved Figure 2 (PNG + PDF)")
