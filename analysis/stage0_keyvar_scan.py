import pandas as pd
pd.set_option('display.width', 220)
pd.set_option('display.max_rows', 200)

files = {
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
    "health_indicators": "../data/raw/health_indicators_gha.csv",
}

keywords = [
    "life expectancy", "DALY", "leading cause", "Tuberculosis incidence", "TB treatment",
    "HIV", "Malaria", "premature", "30-70", "suicide", "fertility rate", "Total fertility",
    "under-five", "U5MR", "neonatal", "infant mortality", "current health expenditure",
    "out-of-pocket", "UHC", "universal health coverage", "service coverage index",
    "air pollution", "PM2.5",
]

hits = {}
for name, path in files.items():
    df = pd.read_csv(path, low_memory=False)
    body = df.iloc[1:].copy()
    inds = body['GHO (DISPLAY)'].dropna().unique()
    for kw in keywords:
        matches = [i for i in inds if kw.lower() in str(i).lower()]
        if matches:
            hits.setdefault(kw, []).append((name, matches[:6], len(matches)))

for kw in keywords:
    print(f"\n### '{kw}' ###")
    if kw in hits:
        for fname, matches, n in hits[kw]:
            print(f"  [{fname}] n_indicator_variants={n}")
            for m in matches:
                print(f"      - {m}")
    else:
        print("  NOT FOUND in any of the 11 GHO-schema files")

# indicators_gha.csv (World-Bank style long format) - separate scan
print("\n\n########## indicators_gha.csv (World Bank style long format) ##########")
wb = pd.read_csv("../data/raw/indicators_gha.csv", low_memory=False)
body = wb.iloc[1:].copy()
print("n unique Indicator Name:", body['Indicator Name'].nunique())
print("year range:", pd.to_numeric(body['Year'], errors='coerce').min(), "-", pd.to_numeric(body['Year'], errors='coerce').max())
for kw in ["life expectancy", "fertility", "mortality", "health expenditure", "PM2.5", "air pollution", "immuniz"]:
    matches = [i for i in body['Indicator Name'].dropna().unique() if kw.lower() in str(i).lower()]
    print(f"\n'{kw}': {len(matches)} matches")
    for m in matches[:8]:
        print(f"   - {m}")

# fertility subnational - check resolution + years
print("\n\n########## fertility-rates_subnational_gha.csv ##########")
fert = pd.read_csv("../data/raw/fertility-rates_subnational_gha.csv", low_memory=False)
body = fert.iloc[1:].copy()
print("unique CharacteristicCategory:", body['CharacteristicCategory'].dropna().unique())
print("unique CharacteristicLabel (region names) sample:", body[body['CharacteristicCategory']=='Region']['CharacteristicLabel'].dropna().unique())
print("survey years:", sorted(pd.to_numeric(body['SurveyYear'], errors='coerce').dropna().unique()))
print("unique Indicator:", body['Indicator'].dropna().unique())
