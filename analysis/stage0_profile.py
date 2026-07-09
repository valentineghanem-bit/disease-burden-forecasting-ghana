import pandas as pd
pd.set_option('display.width', 200)

gho_files = {
    "ghe": "../data/raw/global_health_estimates_life_expectancy_and_leading_causes_of_death_and_disability_indicators_gh.csv",
    "whs": "../data/raw/world_health_statistics_indicators_gha.csv",
    "health_financing": "../data/raw/health_financing_indicators_gha.csv",
    "health_systems": "../data/raw/health_systems_indicators_gha.csv",
    "tb": "../data/raw/tuberculosis_indicators_gha.csv",
    "hiv": "../data/raw/hiv_indicators_gha.csv",
    "malaria": "../data/raw/malaria_indicators_gha.csv",
    "ncd": "../data/raw/noncommunicable_diseases_indicators_gha.csv",
    "child_mortality": "../data/raw/child_mortality_indicators_gha.csv",
    "global_strategy": "../data/raw/global_strategy_indicators_gha.csv",
    "indicators": "../data/raw/indicators_gha.csv",
    "health_indicators": "../data/raw/health_indicators_gha.csv",
}

for name, path in gho_files.items():
    df = pd.read_csv(path, low_memory=False)
    print(f"\n=== {name} ({path.split('/')[-1]}) ===")
    print("raw shape (incl possible HXL row):", df.shape)
    print("columns:", list(df.columns))
    is_hxl = df.iloc[0].astype(str).str.startswith('#').any()
    print("row0 is HXL hashtag row:", is_hxl)
    body = df.iloc[1:].copy() if is_hxl else df.copy()
    if 'GHO (DISPLAY)' in body.columns:
        print("n unique indicators:", body['GHO (DISPLAY)'].nunique())
    if 'STARTYEAR' in body.columns and 'ENDYEAR' in body.columns:
        yrs = pd.to_numeric(body['STARTYEAR'], errors='coerce')
        yrs2 = pd.to_numeric(body['ENDYEAR'], errors='coerce')
        print("year range:", yrs.min(), "-", yrs2.max())
    if 'DIMENSION (TYPE)' in body.columns:
        print("dimension types:", body['DIMENSION (TYPE)'].dropna().unique()[:15])
    if 'COUNTRY (DISPLAY)' in body.columns:
        print("countries present:", body['COUNTRY (DISPLAY)'].dropna().unique()[:5])

# Non-GHO-schema files
print("\n\n########## NON-STANDARD-SCHEMA FILES ##########")

fert = pd.read_csv("../data/raw/fertility-rates_subnational_gha.csv", low_memory=False)
print("\n=== fertility_subnational ===")
print("shape:", fert.shape)
print("columns:", list(fert.columns))
print(fert.head(3).to_string())

ms = pd.read_excel("../data/raw/Master Sheet.xlsx")
print("\n=== Master Sheet ===")
print("shape:", ms.shape)
print("columns:", list(ms.columns))

import json
with open("../data/raw/Ghana_New_260_District.geojson", encoding="utf-8") as fh:
    gj = json.load(fh)
print("\n=== GeoJSON ===")
print("n features:", len(gj["features"]))
print("sample properties keys:", list(gj["features"][0]["properties"].keys()))
