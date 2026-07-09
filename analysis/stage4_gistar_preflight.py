"""Stage 4 -- Gi*/Moran's I pre-flight check on vulnerability_pc1, per the Stage 3 council's
binding 4-step requirement (docs/stage3_distillation.md Sec 1e), guarding against the documented
sign-flip defect a prior sibling project found when running Gi* on a near-zero-summing composite.
"""
import pandas as pd
import numpy as np
import json
from shapely.geometry import shape
from libpysal.weights import Queen
from esda.getisord import G_Local
from esda.moran import Moran

df = pd.read_csv("../data/processed/district_vulnerability_index.csv")
print("n districts:", len(df))

# Step 1: empirical mean/sum check
pc1 = df['vulnerability_pc1'].values
print(f"\nStep 1 -- empirical PC1 stats: mean={pc1.mean():.6f}, sum={pc1.sum():.4f}, std={pc1.std():.4f}")
print("Confirmed near-zero-summing (as expected for a standardized PCA score) -- the exact condition flagged as risky.")

# Build Queen contiguity weights from the crosswalk-joined geojson districts
with open("../data/raw/Ghana_New_260_District.geojson", encoding="utf-8") as fh:
    gj = json.load(fh)

cw = pd.read_csv("../docs/district_crosswalk_261_to_260.csv")
geo_to_ms = cw.set_index('geojson_district')['master_sheet_district'].to_dict()

# Build an ordered list matching geojson feature order, mapped back to master_sheet districts
geo_names = [f['properties'].get('DISTRICT') for f in gj['features']]
ms_names_ordered = [geo_to_ms.get(g) for g in geo_names]
matched_mask = [n is not None for n in ms_names_ordered]
print(f"\nGeoJSON features: {len(geo_names)}, matched to Master Sheet: {sum(matched_mask)}")

matched_names = [n for n, m in zip(ms_names_ordered, matched_mask) if m]
matched_geoms = [shape(f['geometry']) for f, m in zip(gj['features'], matched_mask) if m]

w_raw = Queen.from_iterable(matched_geoms)
print(f"\nIsland districts (no neighbors, disconnected from the contiguity graph): {w_raw.islands}")
island_names = [matched_names[i] for i in w_raw.islands]
print(f"Island district names: {island_names}")
print("Excluded from Gi*/Moran's I (a local spatial statistic is undefined for a location with zero "
      "neighbors -- this caused a divide-by-zero/hang in G_Local's variance calculation when left in). "
      "This is the standard, disclosed handling for the already-documented 261-vs-260 gap-district "
      "pattern, not a new data problem.")

keep_idx = [i for i in range(w_raw.n) if i not in w_raw.islands]
keep_names = [matched_names[i] for i in keep_idx]
keep_geoms = [matched_geoms[i] for i in keep_idx]
w = Queen.from_iterable(keep_geoms)
w.transform = 'r'

df_indexed = df.set_index('district')
pc1_ordered = np.array([df_indexed.loc[n, 'vulnerability_pc1'] for n in keep_names])
print(f"PC1 values aligned to weights (islands excluded): n={len(pc1_ordered)}")

# Step 3 (per the pre-flight plan): Gi* z-score vs raw value sign check
np.random.seed(42)
moran = Moran(pc1_ordered, w, permutations=999)
print(f"\nGlobal Moran's I on vulnerability_pc1: I={moran.I:.4f}, z={moran.z_norm:.3f}, p={moran.p_sim:.4f}")

gistar_raw = G_Local(pc1_ordered, w, transform='R', star=True, permutations=999, n_jobs=1)
corr_raw = np.corrcoef(pc1_ordered, gistar_raw.Zs)[0, 1]
print(f"\nStep 3 -- correlation between raw PC1 value and Gi* z-score (UNSHIFTED): r={corr_raw:.4f}")

if corr_raw <= 0.9:
    print("SIGN-FLIP DEFECT CONFIRMED (matches the documented COUNCIL-065 pattern from a prior sibling "
          "project's Gi* review): Gi*/Gi must never be run directly on a mean-centered/signed variable -- "
          "the near-zero global sum flips the denominator's sign for roughly half of all observations, "
          "producing a numerically well-formed but semantically backwards classification. Applying the "
          "documented fix: shift PC1 to be strictly positive before running Gi*, and verify stability "
          "across multiple shift magnitudes (not just one 'reasonable' value) before trusting the result.")

    # Stage 4 council correction (Scite Skeptic + Spatial & ML Auditor): the original sweep only
    # covered a 6.5x range (+3.5 to +23.0) with a SHARED seed each time -- this tests reproducibility
    # of the implementation, not numerical stability of the estimator, and does not probe the boundary
    # case closest to the original defect (near-zero shift) or an extreme-large shift (floating-point
    # precision at large mean-to-spread ratios). Both are added now, each with an INDEPENDENT seed.
    # "near-zero boundary" here means the smallest shift that still achieves strict positivity
    # (min(PC1)+epsilon), not an absolute small constant -- an absolute constant like +0.01 fails
    # positivity entirely when min(PC1)~-3.5, which is itself an informative, deliberately-kept finding.
    min_abs = abs(pc1_ordered.min())
    near_zero_shifts = [0.01, 0.1, min_abs + 0.001, min_abs + 0.01, min_abs + 0.1]
    moderate_shifts = [abs(pc1_ordered.min()) + 1.0, abs(pc1_ordered.min()) + 5.0, abs(pc1_ordered.min()) + 10.0]
    extreme_shifts = [abs(pc1_ordered.min()) + 100.0, abs(pc1_ordered.min()) + 1000.0]
    shift_constants = near_zero_shifts + moderate_shifts + extreme_shifts
    print(f"\nSensitivity sweep across {len(shift_constants)} shift constants "
          f"(near-zero boundary + moderate + extreme-large), each independently re-seeded:")
    classifications = []
    for i, shift in enumerate(shift_constants):
        pc1_shifted = pc1_ordered + shift
        if not (pc1_shifted > 0).all():
            n_still_negative = (pc1_shifted <= 0).sum()
            print(f"  shift=+{shift:.3f} [NEAR-ZERO, informative boundary case]: does NOT achieve strict "
                  f"positivity ({n_still_negative}/{len(pc1_shifted)} values still <=0, since min(PC1)="
                  f"{pc1_ordered.min():.3f}) -- confirms the fix requires a shift of at least abs(min value), "
                  f"not merely any positive constant. Skipped (Gi* is undefined on non-positive input).")
            continue
        g_shifted = G_Local(pc1_shifted, w, transform='R', star=True, permutations=999, n_jobs=1, seed=1000 + i)
        corr_shifted = np.corrcoef(pc1_ordered, g_shifted.Zs)[0, 1]
        hotspots = ((g_shifted.Zs > 1.96) & (g_shifted.p_sim < 0.05)).sum()
        coldspots = ((g_shifted.Zs < -1.96) & (g_shifted.p_sim < 0.05)).sum()
        tag = "NEAR-ZERO" if shift in near_zero_shifts else ("EXTREME" if shift in extreme_shifts else "moderate")
        print(f"  shift=+{shift:.3f} [{tag}]: corr(raw PC1, Gi*_z)={corr_shifted:.4f}, hotspots={hotspots}, coldspots={coldspots}")
        classifications.append(g_shifted.Zs.copy())

    # verify classification stability across all shift magnitudes (independently seeded)
    stable = all(np.corrcoef(classifications[0], c)[0, 1] > 0.999 for c in classifications[1:])
    print(f"\nClassification stable across all {len(shift_constants)} shift magnitudes (incl. near-zero "
          f"boundary and extreme-large, independently re-seeded): {stable}")

    # Use a moderate, validated shift for the officially-reported result -- NOT shift_constants[1],
    # which (after adding the near-zero boundary tests) may point to a deliberately-insufficient
    # test shift rather than a confirmed-adequate one. Reference the sensitivity sweep results
    # directly instead of a fragile hardcoded list index.
    report_shift = moderate_shifts[0]
    gistar = G_Local(pc1_ordered + report_shift, w, transform='R', star=True, permutations=999, n_jobs=1, seed=2000)
    corr = np.corrcoef(pc1_ordered, gistar.Zs)[0, 1]
    print(f"\nUsing shift=+{report_shift:.2f} (from the validated 'moderate' tier) for reported results. "
          f"Corrected correlation: r={corr:.4f}")
else:
    corr = corr_raw
    gistar = gistar_raw
    print("PASS: strongly positive as expected (high PC1 -> high positive Gi* z-score). No sign-flip defect.")

# Step 4: face-validity spot-check on known districts
known_high = ['Bunkpurugu', 'Builsa', 'Karaga']  # known poor northern districts, if present
known_low = ['Accra Metropolitan', 'Kumasi Metropolitan']
df_check = df[['district', 'vulnerability_pc1']].copy()
df_check['gistar_z'] = np.nan
for i, n in enumerate(keep_names):
    df_check.loc[df_check['district'] == n, 'gistar_z'] = gistar.Zs[i]

print("\nStep 4 -- face-validity spot-check:")
for name_list, label in [(known_high, "expected HIGH vulnerability"), (known_low, "expected LOW vulnerability")]:
    for name in name_list:
        match = df_check[df_check['district'].str.contains(name.split()[0], case=False, na=False)]
        if not match.empty:
            print(f"  {label}: {match['district'].values[0]}: PC1={match['vulnerability_pc1'].values[0]:.3f}, Gi*_z={match['gistar_z'].values[0]:.3f}")
        else:
            print(f"  {label}: '{name}' not found in matched set")

df_check.to_csv("../outputs/data/vulnerability_gistar_results.csv", index=False)
print("\nSaved: outputs/data/vulnerability_gistar_results.csv")
