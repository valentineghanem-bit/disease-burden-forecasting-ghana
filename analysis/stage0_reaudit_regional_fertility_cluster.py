"""Stage 0 re-audit fix: Stage 0 promised a region-level Getis-Ord/LISA cluster analysis
on the 16-region DHS fertility panel -- never executed anywhere in the project. A genuine
multi-timepoint cluster-SHIFT analysis is not valid here because Ghana's regions changed
from 10 to 16 partway through 1988-2022 (no consistent boundary set across all 9 survey
rounds). This script runs the honestly-scoped alternative: a single-timepoint (2022, the
only round using the current 16-region frame) cross-sectional Moran's I / Getis-Ord Gi*
on total fertility rate -- the same single-cross-section scoping already used for the
district structural-vulnerability index, for the same underlying reason (no consistent
multi-timepoint boundary set).

CORRECTED after methodical re-verification (2026-07-09): the original version of this
script built Queen contiguity weights via libpysal's exact-vertex-touching algorithm,
which reported Eastern region as a topological island (0 neighbors). Direct shapely
distance checks (region-pair minimum boundary distance) showed this was WRONG -- Eastern
genuinely touches 6 other regions (Ashanti, Bono East, Central, Greater Accra, Oti,
Volta) at distance 0.0, confirmed by three independent methods (shapely .touches(),
min-distance, and nearest-centroid KNN). The exact-vertex Queen algorithm was failing on
a boundary-precision artifact specific to this GeoJSON, not a real topological gap (a
narrower, previously-undocumented version of the same file-quality issue that produced
the 3 known district-level islands, but affecting cross-region district edges only,
which is why it never surfaced in the district-level Gi* analysis -- Eastern's districts
still had same-region neighbors there). Rebuilt using a distance-based robust adjacency
check (tolerance 1e-6) instead of exact-vertex Queen. Zero regions are islands under this
corrected method.
"""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from libpysal.weights import W
from esda.moran import Moran
from esda.getisord import G_Local

with open("../data/raw/Ghana_New_260_District.geojson", encoding="utf-8") as f:
    gj = json.load(f)
gdf = gpd.GeoDataFrame.from_features(gj["features"])
region_gdf = gdf.dissolve(by="REGION").reset_index()
n = len(region_gdf)
regions = region_gdf["REGION"].tolist()
print("Dissolved to", n, "region polygons")

# robust distance-based adjacency (exact-vertex Queen was found, on methodical
# re-verification, to falsely report Eastern as an island -- see module docstring)
TOL = 1e-6
neighbor_dict = {}
weight_dict = {}
for i in range(n):
    neighbors = []
    for j in range(n):
        if i == j:
            continue
        d = region_gdf.geometry.iloc[i].distance(region_gdf.geometry.iloc[j])
        if d < TOL:
            neighbors.append(j)
    neighbor_dict[i] = neighbors
    weight_dict[i] = [1.0] * len(neighbors)

islands = [regions[i] for i in range(n) if not neighbor_dict[i]]
print("Islands under robust distance-based adjacency:", islands)
assert not islands, "unexpected island found -- do not silently proceed"

w = W(neighbor_dict, weight_dict, id_order=list(range(n)))
w.transform = "r"

fert = pd.read_csv("../data/processed/region_fertility_panel.csv")
row2022 = fert[fert["SurveyYear"] == 2022].iloc[0]

# verified against the 1988 row (pre-reorganisation): these "post 2022"-labelled columns
# are correctly NaN before the 2018-2019 administrative reorganisation and populated only
# from the round(s) using the current 16-region frame -- confirmed, not assumed, at the
# 2026-07-09 re-audit.
col_to_region = {
    "....Northeast": "NORTHERN EAST", "....Northern(post 2022)": "NORTHERN",
    "....Savannah": "SAVANNAH", "..Ahafo": "AHAFO", "..Bono": "BONO",
    "..Bono East": "BONO EAST", "..Oti": "OTI", "..Upper East": "UPPER EAST",
    "..Upper West": "UPPER WEST", "..Volta (post 2022)": "VOLTA",
    "..Western (post 2022)": "WESTERN", "..Western North": "WESTERN NORTH",
    "Ashanti": "ASHANTI", "Central": "CENTRAL", "Eastern": "EASTERN",
    "Greater Accra": "GREATER ACCRA",
}
tfr_2022 = {region: float(row2022[col]) for col, region in col_to_region.items() if pd.notna(row2022[col])}
print(f"\n2022 TFR by region ({len(tfr_2022)} of 16 regions matched)")
assert len(tfr_2022) == 16, "all 16 regions must match"

region_gdf["tfr_2022"] = region_gdf["REGION"].map(tfr_2022)
values = region_gdf["tfr_2022"].values

moran = Moran(values, w, permutations=999)
print(f"\nGlobal Moran's I (2022 regional TFR, corrected adjacency): I={moran.I:.4f}, z={moran.z_norm:.3f}, p={moran.p_norm:.4f}")

gistar = G_Local(values, w, transform="R", star=True, permutations=999, n_jobs=1, seed=42)
region_gdf["gistar_z"] = gistar.Zs
region_gdf["gistar_p"] = gistar.p_sim
region_gdf["gistar_class"] = np.where(
    (gistar.Zs > 1.96) & (gistar.p_sim < 0.05), "HOTSPOT_P05",
    np.where((gistar.Zs < -1.96) & (gistar.p_sim < 0.05), "COLDSPOT_P05", "NOT_SIGNIFICANT")
)
n_hot = (region_gdf["gistar_class"] == "HOTSPOT_P05").sum()
n_cold = (region_gdf["gistar_class"] == "COLDSPOT_P05").sum()
print(f"Getis-Ord Gi* (p<0.05, corrected adjacency): {n_hot} hotspot regions, {n_cold} coldspot regions")
print(region_gdf[["REGION", "tfr_2022", "gistar_z", "gistar_class"]].sort_values("tfr_2022", ascending=False).to_string())

out = region_gdf[["REGION", "tfr_2022", "gistar_z", "gistar_p", "gistar_class"]].copy()
out.to_csv("../outputs/data/regional_fertility_gistar_2022.csv", index=False)
print("\nSaved outputs/data/regional_fertility_gistar_2022.csv (all 16 regions, 0 excluded)")
