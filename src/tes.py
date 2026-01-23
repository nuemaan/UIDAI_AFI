import pandas as pd
m = pd.read_csv('outputs/merged_for_afi.csv', dtype=str, low_memory=False)
print('merged rows:', len(m))
print('states in merged:', m['state_canonical'].nunique())
print(m[['period','state_canonical','district_clean','enrol_total','demo_total','bio_total']].head(10))

if 'afi' in m.columns:
    print(m.sort_values('afi', ascending=False).head(20)[['state_canonical','district_clean','afi']])