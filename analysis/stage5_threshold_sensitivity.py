import pandas as pd, numpy as np, json
from shapely.geometry import shape
from libpysal.weights import Queen
from esda.getisord import G_Local
from statsmodels.stats.multitest import multipletests

df = pd.read_csv("../data/processed/district_vulnerability_index.csv")
cw = pd.read_csv("../docs/district_crosswalk_261_to_260.csv")
geo_to_ms = cw.set_index('geojson_district')['master_sheet_district'].to_dict()
with open("../data/raw/Ghana_New_260_District.geojson", encoding="utf-8") as fh:
    gj = json.load(fh)
geo_names = [f['properties'].get('DISTRICT') for f in gj['features']]
ms_names_ordered = [geo_to_ms.get(g) for g in geo_names]
matched_mask = [n is not None for n in ms_names_ordered]
matched_names = [n for n, m in zip(ms_names_ordered, matched_mask) if m]
matched_geoms = [shape(f['geometry']) for f, m in zip(gj['features'], matched_mask) if m]
w_raw = Queen.from_iterable(matched_geoms)
keep_idx = [i for i in range(w_raw.n) if i not in w_raw.islands]
keep_names = [matched_names[i] for i in keep_idx]
keep_geoms = [matched_geoms[i] for i in keep_idx]
w = Queen.from_iterable(keep_geoms)
w.transform = 'r'
df_indexed = df.set_index('district')
pc1_ordered = np.array([df_indexed.loc[n, 'vulnerability_pc1'] for n in keep_names])
shift = abs(pc1_ordered.min()) + 4.0
gistar = G_Local(pc1_ordered + shift, w, transform='R', star=True, permutations=999, n_jobs=1, seed=42)

p05_hot = ((gistar.Zs > 1.96) & (gistar.p_sim < 0.05)).sum()
p05_cold = ((gistar.Zs < -1.96) & (gistar.p_sim < 0.05)).sum()
p10_hot = ((gistar.Zs > 1.645) & (gistar.p_sim < 0.10)).sum()
p10_cold = ((gistar.Zs < -1.645) & (gistar.p_sim < 0.10)).sum()

rejected, p_fdr, _, _ = multipletests(gistar.p_sim, alpha=0.05, method='fdr_bh')
fdr_hot = ((gistar.Zs > 0) & rejected).sum()
fdr_cold = ((gistar.Zs < 0) & rejected).sum()

print(f"n districts analyzed: {len(pc1_ordered)}")
print(f"p<0.05 (uncorrected, 999 perm): hotspots={p05_hot}, coldspots={p05_cold}")
print(f"p<0.10 (uncorrected, 999 perm): hotspots={p10_hot}, coldspots={p10_cold}")
print(f"FDR-corrected (Benjamini-Hochberg, alpha=0.05): hotspots={fdr_hot}, coldspots={fdr_cold}")

pd.DataFrame({'threshold': ['p<0.05', 'p<0.10', 'FDR-BH'],
              'hotspots': [p05_hot, p10_hot, fdr_hot],
              'coldspots': [p05_cold, p10_cold, fdr_cold]}).to_csv("../outputs/data/hotspot_threshold_sensitivity.csv", index=False)
print("Saved: outputs/data/hotspot_threshold_sensitivity.csv")
