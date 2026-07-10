"""Stage 0 re-audit fix: Stage 0 promised a region-level Getis-Ord/LISA cluster analysis
on the 16-region DHS fertility panel -- never executed anywhere in the project. A genuine
multi-timepoint cluster-SHIFT analysis is not valid here because Ghana's regions changed
from 10 to 16 partway through 1988-2022 (no consistent boundary set across all 9 survey
rounds). This script runs the honestly-scoped alternative: a single-timepoint (2022, the
only round using the current 16-region frame) cross-sectional Moran's I / Getis-Ord Gi*
on total fertility rate -- the same single-cross-section scoping already used for the
district structural-vulnerability index, for the same underlying reason (no consistent
multi-timepoint boundary set).
"""
import json
import re
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
from libpysal.weights import Queen
from esda.moran import Moran
from esda.getisord import G_Local

with open("../data/raw/Ghana_New_260_District.geojson", encoding="utf-8") as f:
    gj = json.load(f)
gdf = gpd.GeoDataFrame.from_features(gj["features"])
region_gdf = gdf.dissolve(by="REGION").reset_index()
print("Dissolved to", len(region_gdf), "region polygons")

fert = pd.read_csv("../data/processed/region_fertility_panel.csv")
row2022 = fert[fert["SurveyYear"] == 2022].iloc[0]

# map the panel's messy 2022-round column names to the GeoJSON's standard REGION names
col_to_region = {
    "....Northeast": "NORTHERN EAST", "....Northern(post 2022)": "NORTHERN",
    "....Savannah": "SAVANNAH", "..Ahafo": "AHAFO", "..Bono": "BONO",
    "..Bono East": "BONO EAST", "..Oti": "OTI", "..Upper East": "UPPER EAST",
    "..Upper West": "UPPER WEST", "..Volta (post 2022)": "VOLTA",
    "..Western (post 2022)": "WESTERN", "..Western North": "WESTERN NORTH",
    "Ashanti": "ASHANTI", "Central": "CENTRAL", "Eastern": "EASTERN",
    "Greater Accra": "GREATER ACCRA",
}
tfr_2022 = {}
for col, region in col_to_region.items():
    val = row2022.get(col)
    if pd.notna(val):
        tfr_2022[region] = float(val)

print(f"\n2022 TFR by region ({len(tfr_2022)} of 16 regions matched):")
for r, v in sorted(tfr_2022.items()):
    print(f"  {r}: {v}")

region_gdf["tfr_2022"] = region_gdf["REGION"].map(tfr_2022)
missing = region_gdf[region_gdf["tfr_2022"].isna()]["REGION"].tolist()
print(f"\nUnmatched regions (no 2022 TFR): {missing}")
assert len(missing) == 0, "all 16 regions must match -- fix col_to_region mapping"

w = Queen.from_dataframe(region_gdf, use_index=False)
w.transform = "r"

moran = Moran(region_gdf["tfr_2022"].values, w, permutations=999)
print(f"\nGlobal Moran's I (2022 regional TFR): I={moran.I:.4f}, z={moran.z_norm:.3f}, p={moran.p_norm:.4f}")

gistar = G_Local(region_gdf["tfr_2022"].values, w, transform="R", star=True, permutations=999, n_jobs=1, seed=42)
region_gdf["gistar_z"] = gistar.Zs
region_gdf["gistar_p"] = gistar.p_sim
region_gdf["gistar_class"] = np.where(
    (gistar.Zs > 1.96) & (gistar.p_sim < 0.05), "HOTSPOT_P05",
    np.where((gistar.Zs < -1.96) & (gistar.p_sim < 0.05), "COLDSPOT_P05", "NOT_SIGNIFICANT")
)
n_hot = (region_gdf["gistar_class"] == "HOTSPOT_P05").sum()
n_cold = (region_gdf["gistar_class"] == "COLDSPOT_P05").sum()
print(f"Getis-Ord Gi* (p<0.05): {n_hot} hotspot regions, {n_cold} coldspot regions")
print(region_gdf[["REGION", "tfr_2022", "gistar_z", "gistar_class"]].sort_values("tfr_2022", ascending=False).to_string())

out = region_gdf[["REGION", "tfr_2022", "gistar_z", "gistar_p", "gistar_class"]].copy()
out.to_csv("../outputs/data/regional_fertility_gistar_2022.csv", index=False)
print("\nSaved outputs/data/regional_fertility_gistar_2022.csv")
