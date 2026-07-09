"""Stage 1 -- build the national master panel CSV and the district raw-covariate CSV.
Cleaning decisions per docs/datalog_phase0.md Sec 8, corrected per docs/stage0_council_verdict.md.
Reuses clean_suicide_rate() defect handling identical to Project 22 (same upstream WHO-GHO export).
"""
import pandas as pd
import numpy as np
import json

RAW = "../data/raw/"

def load_gho(fname):
    df = pd.read_csv(RAW + fname, low_memory=False)
    return df.iloc[1:].copy()  # drop HXL row

def both_sexes_or_total(df, indicator, agg=None, dim_name='Both sexes'):
    """agg=None requires exactly one row/year after the dim_name filter (raises if not).
    agg='sum' sums remaining sub-category rows (valid for additive count/DALY indicators
    with a hidden second dimension, e.g. cause-of-DALY sub-category, not exposed as its
    own column in this WHO-GHO export format). dim_name overrides 'Both sexes' for
    indicators disaggregated by a non-SEX dimension (e.g. RESIDENCEAREATYPE -> 'Total')."""
    sub = df[df['GHO (DISPLAY)'] == indicator].copy()
    if sub.empty:
        return pd.DataFrame(columns=['STARTYEAR', 'Numeric'])
    if sub['DIMENSION (NAME)'].notna().any():
        sub = sub[sub['DIMENSION (NAME)'] == dim_name]
    sub['STARTYEAR'] = pd.to_numeric(sub['STARTYEAR'], errors='coerce')
    sub['Numeric'] = pd.to_numeric(sub['Numeric'], errors='coerce')
    sub = sub[['STARTYEAR', 'Numeric']].dropna()
    dupe_years = sub.groupby('STARTYEAR').size()
    if (dupe_years > 1).any():
        if agg == 'max_is_total':
            # verified via live WHO GHO OData API (Dim2Type=GHECAUSE): the hidden dimension is
            # cause-of-DALY sub-category, and the largest value per year IS the "All Causes"
            # total (confirmed exactly equal to the sum of the other rows for AIR_7 across all
            # years; AIR_15 shows the same structure with a small ~0.3% residual, consistent
            # with one additional minor cause category not captured in this file's row window).
            # max() is correct here; sum() would double-count (total + its own components).
            sub = sub.groupby('STARTYEAR', as_index=False)['Numeric'].max()
        elif agg == 'median':
            sub = sub.groupby('STARTYEAR', as_index=False)['Numeric'].median()
        else:
            raise ValueError(f"'{indicator}': {int((dupe_years>1).sum())} years have >1 row after "
                              f"Both-sexes filter and no agg mode was specified -- hidden second "
                              f"dimension present, resolve explicitly before building the panel.")
    return sub

def clean_suicide_rate(sub):
    """2021 export anomaly: retain only the 3 CI-bearing rows per sex-stratum (identical defect to Project 22)."""
    counts = sub.groupby('STARTYEAR').size()
    bad_years = counts[counts > 3].index.tolist()
    if not bad_years:
        return sub
    keep_mask = ~sub['STARTYEAR'].isin(bad_years)
    kept_bad = sub[sub['STARTYEAR'].isin(bad_years) & sub['Low'].notna() & sub['High'].notna()]
    return pd.concat([sub[keep_mask], kept_bad], ignore_index=True)

# ---------- National panel ----------
national = {}

ghe = load_gho("global_health_estimates_life_expectancy_and_leading_causes_of_death_and_disability_indicators_gh.csv")
national['life_expectancy_birth_yrs_who'] = both_sexes_or_total(ghe, 'Life expectancy at birth (years)')
national['hale_birth_yrs'] = both_sexes_or_total(ghe, 'Healthy life expectancy (HALE) at birth (years)')
# CORRECTED (Stage 1 council gate, 2026-07-06): the CSV export's "6 duplicate rows/year" for
# this indicator is NOT an unresolvable estimation-vintage conflict -- a direct query against
# the live WHO GHO OData API (ghoapi.azureedge.net/api/MDG_0000000007) revealed the hidden
# dimension the flat CSV silently drops: Dim3Type=WEALTHQUINTILE (Q1-Q5 + Total). The CSV's
# "duplicates" are wealth-quintile-stratified sub-national-equity estimates, not repeated
# measurements of one national quantity -- taking their median (the original approach) blended
# subgroup-specific rates into a number with no defined estimand. The correct national series is
# the single WEALTHQUINTILE_TOTL row per year, confirmed via the API to give exactly 92 unique
# years with zero duplicates. Cached at data/raw/u5mr_who_api_verified.csv (fetched 2026-07-06).
u5mr_api = pd.read_csv(RAW + "u5mr_who_api_verified.csv")[['STARTYEAR', 'Numeric']]
national['u5mr_who'] = u5mr_api
national['ncd_premature_pct'] = both_sexes_or_total(ghe, 'Premature deaths due to noncommunicable diseases (NCD) as a proportion of all NCD deaths')
national['ncd_3070_probability_pct'] = both_sexes_or_total(ghe, 'Probability (%) of dying between age 30 and exact age 70 from any of cardiovascular disease, cancer, diabetes, or chronic respiratory disease')
national['total_ncd_deaths'] = both_sexes_or_total(ghe, 'Total NCD Deaths')

# suicide rate -- special anomaly handling, done on raw sex-filtered slice before Numeric-only reduction
ghe_suicide_raw = ghe[(ghe['GHO (DISPLAY)'] == 'Crude suicide rates (per 100 000 population)') & (ghe['DIMENSION (NAME)'] == 'Both sexes')].copy()
ghe_suicide_raw['STARTYEAR'] = pd.to_numeric(ghe_suicide_raw['STARTYEAR'], errors='coerce')
ghe_suicide_raw['Numeric'] = pd.to_numeric(ghe_suicide_raw['Numeric'], errors='coerce')
ghe_suicide_clean = clean_suicide_rate(ghe_suicide_raw)
national['suicide_rate_crude_who'] = ghe_suicide_clean[['STARTYEAR', 'Numeric']].dropna()
national['suicide_rate_agestd_who'] = both_sexes_or_total(ghe, 'Age-standardized suicide rates (per 100 000 population)')

tb = load_gho("tuberculosis_indicators_gha.csv")
national['tb_incidence_per100k'] = both_sexes_or_total(tb, 'Incidence of tuberculosis (per 100 000 population per year)')

hiv = load_gho("hiv_indicators_gha.csv")
national['hiv_new_infections_n'] = both_sexes_or_total(hiv, 'Number of new HIV infections')
national['hiv_new_infections_per1000'] = both_sexes_or_total(hiv, 'New HIV infections (per 1000 uninfected population)')

malaria = load_gho("malaria_indicators_gha.csv")
national['malaria_incidence_per1000atrisk'] = both_sexes_or_total(malaria, 'Estimated malaria incidence (per 1000 population at risk)')

hf = load_gho("health_financing_indicators_gha.csv")
national['oop_pct_che'] = both_sexes_or_total(hf, 'Out-of-pocket expenditure as percentage of current health expenditure (CHE) (%)')
national['oop_percapita_usd'] = both_sexes_or_total(hf, 'Out-of-pocket expenditure (OOP) per capita in US$')
national['che_pct_gdp'] = both_sexes_or_total(hf, 'Current health expenditure (CHE) as percentage of gross domestic product (GDP) (%)')
national['che_percapita_usd'] = both_sexes_or_total(hf, 'Current health expenditure (CHE) per capita in US$')

gs = load_gho("global_strategy_indicators_gha.csv")
national['uhc_service_coverage_index'] = both_sexes_or_total(gs, 'UHC Service Coverage Index (SDG 3.8.1)')

hi = load_gho("health_indicators_gha.csv")
national['pm25_conc_ugm3'] = both_sexes_or_total(hi, 'Concentrations of fine particulate matter (PM2.5)', dim_name='Total')
# CORRECTED (Stage 1 council gate, 2026-07-06): a live WHO GHO API query (indicator codes AIR_7,
# AIR_15) confirmed the hidden dimension is Dim2Type=GHECAUSE (cause-of-DALY sub-category), and
# the largest of the ~6 rows per year IS the "All Causes" total -- verified exactly equal to the
# sum of the other rows for AIR_7 across every year, and equal within ~0.3% for AIR_15 (consistent
# with one additional minor cause category not captured in this file's row window). The original
# sum()-of-all-6-rows approach was WRONG: it double-counted (total + its own components ~= 2x the
# true value). max() correctly selects the All-Causes total. Both indicators remain
# secondary/contextual (the Stage 0 all-cause-DALY gap is already disclosed), not a primary
# forecast target.
national['air_pollution_ambient_daly'] = both_sexes_or_total(hi, 'Ambient air pollution attributable DALYs', agg='max_is_total')
national['air_pollution_household_daly'] = both_sexes_or_total(hi, 'Household air pollution attributable DALYs', agg='max_is_total')

# World Bank WDI cross-source series (parallel, not merged)
wb = pd.read_csv(RAW + "indicators_gha.csv", low_memory=False).iloc[1:].copy()
wb['Year'] = pd.to_numeric(wb['Year'], errors='coerce')
wb['Value'] = pd.to_numeric(wb['Value'], errors='coerce')

def wb_series(indicator_name):
    # indicators_gha.csv carries each row twice (exact duplicate, verified: identical Value for
    # every checked case, e.g. TFR 1960 = 6.89 both times) -- a straight file-level duplication
    # artefact, not a multi-vintage issue like the WHO-GHO files. drop_duplicates() is safe here.
    sub = wb[wb['Indicator Name'] == indicator_name][['Year', 'Value']].dropna().drop_duplicates()
    sub = sub.rename(columns={'Year': 'STARTYEAR', 'Value': 'Numeric'})
    dupe_years = sub.groupby('STARTYEAR').size()
    if (dupe_years > 1).any():
        raise ValueError(f"WB '{indicator_name}': {int((dupe_years>1).sum())} years still have "
                          f">1 distinct value after de-duplication -- genuine conflicting WB "
                          f"observations, must resolve explicitly, not silently averaged.")
    return sub

national['life_expectancy_birth_yrs_wb'] = wb_series('Life expectancy at birth, total (years)')
national['suicide_rate_wb'] = wb_series('Suicide mortality rate (per 100,000 population)')
national['che_pct_gdp_wb'] = wb_series('Current health expenditure (% of GDP)')
national['tfr_national_wb'] = wb_series('Fertility rate, total (births per woman)')
national['pm25_exposure_wb'] = wb_series('PM2.5 air pollution, mean annual exposure (micrograms per cubic meter)')

# Assemble wide national panel
panel = None
for name, sub in national.items():
    s = sub.rename(columns={'Numeric': name}).set_index('STARTYEAR')
    panel = s if panel is None else panel.join(s, how='outer')
panel = panel.sort_index()
panel.index.name = 'year'
panel.to_csv("../data/processed/national_panel.csv")
print("National panel shape:", panel.shape)
print(panel.tail(8))

# ---------- District raw-covariate CSV (structural vulnerability inputs -- NOT the composite index; that's Stage 3) ----------
ms = pd.read_excel(RAW + "Master Sheet.xlsx")
ms = ms.rename(columns={
    "Metropolitan, Municipal, and District Assemblies (MMDA's)": "district",
    "Region": "region", "Class": "class", "Latitude": "lat", "Longitude": "lon",
    "Employed Population": "employed", "Unemployed Population": "unemployed",
    "Incidence of Poverty": "poverty_incidence", "Intensity of Poverty": "poverty_intensity",
    "Illiterate Population": "illiterate_pop", "Uninsured Population": "uninsured_pop",
    "Male Population 0-14": "m_0_14", "Female Population 0-14": "f_0_14",
    "Male Population 15-64": "m_15_64", "Female Population 15-64": "f_15_64",
    "Male Population 65+": "m_65p", "Female Population 65+": "f_65p",
    "Total Population": "total_pop",
})
ms['literacy_rate'] = 1 - (ms['illiterate_pop'] / ms['total_pop'])
ms['uninsured_rate'] = ms['uninsured_pop'] / ms['total_pop']
ms['elderly_share_65plus'] = (ms['m_65p'] + ms['f_65p']) / ms['total_pop']
ms['unemployment_rate'] = ms['unemployed'] / (ms['employed'] + ms['unemployed'])

# pop_density -- RESOLVED at Stage 1 (Stage 1 council gate flagged deferring this to Stage 6 as
# an avoidable risk: a join failure diagnosed calmly now gets a clean fix; the same failure at
# Stage 6, under deadline pressure while the choropleth is due, risks a silent bad join. Reusing
# the already-vetted 261-to-260 crosswalk (docs/district_crosswalk_261_to_260.csv, copied from
# Project 22) resolves it now rather than deferring.
crosswalk = pd.read_csv("../docs/district_crosswalk_261_to_260.csv")

def poly_area_deg2(coords):
    ring = coords[0] if isinstance(coords[0][0][0], (int, float)) else coords[0][0]
    x = [p[0] for p in ring]; y = [p[1] for p in ring]
    n = len(x)
    a = 0.0
    for i in range(n):
        j = (i + 1) % n
        a += x[i]*y[j] - x[j]*y[i]
    return abs(a) / 2.0

with open(RAW + "Ghana_New_260_District.geojson", encoding="utf-8") as fh:
    gj = json.load(fh)

areas = {}
for feat in gj['features']:
    name = feat['properties'].get('DISTRICT')
    geom = feat['geometry']
    a = poly_area_deg2(geom['coordinates']) if geom['type'] == 'Polygon' else sum(poly_area_deg2(p) for p in geom['coordinates'])
    areas[name] = areas.get(name, 0) + a

cw = crosswalk.set_index('master_sheet_district')['geojson_district']
ms['geojson_district'] = ms['district'].map(cw)
ms['geojson_area_deg2'] = ms['geojson_district'].map(areas)
n_matched = ms['geojson_area_deg2'].notna().sum()
print(f"\nDistrict rows: {len(ms)} | geojson area matched via crosswalk: {n_matched}/{len(ms)}")
unmatched = ms.loc[ms['geojson_area_deg2'].isna(), 'district'].tolist()
if unmatched:
    print(f"  unmatched districts (expected -- 260-vs-261 gap-district-to-parent-polygon merge, "
          f"per the standing [[ghana-261-districts]] rule): {unmatched}")

# pop_density: population per unit geojson polygon area (relative/ordinal density proxy across
# districts -- deg^2 is not a true projected area unit, valid for within-country ranking only,
# not for absolute km^2-based reporting; that conversion is a Stage 6 display-layer concern, not
# a Stage 1 data concern).
ms['pop_density_relative'] = ms['total_pop'] / ms['geojson_area_deg2']

ms.to_csv("../data/processed/district_raw_covariates.csv", index=False)
print("District covariates shape:", ms.shape)
print(ms[['district','poverty_incidence','literacy_rate','uninsured_rate','elderly_share_65plus','total_pop']].head(5).to_string())

# ---------- Region-level fertility panel (DHS, 9 rounds) ----------
fert = pd.read_csv(RAW + "fertility-rates_subnational_gha.csv", low_memory=False).iloc[1:].copy()
fert = fert[fert['CharacteristicCategory'] == 'Region']
fert['SurveyYear'] = pd.to_numeric(fert['SurveyYear'], errors='coerce')
fert['Value'] = pd.to_numeric(fert['Value'], errors='coerce')
fert_tfr = fert[fert['Indicator'] == 'Total fertility rate 15-49'][['SurveyYear', 'CharacteristicLabel', 'Value']]
fert_wide = fert_tfr.pivot_table(index='SurveyYear', columns='CharacteristicLabel', values='Value')
fert_wide.to_csv("../data/processed/region_fertility_panel.csv")
print("\nRegion fertility panel shape:", fert_wide.shape)
