
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"

top_changes = DOCS / "top_mapping_changes.csv"
out_csv = DOCS / "manual_revert_top_mapping_changes.csv"

if not top_changes.exists():
    raise FileNotFoundError(f"Expected {top_changes} (run mapping audit first)")

sheet = pd.read_csv(top_changes, dtype=str).fillna('')


df_out = sheet[['orig_state','orig_district']].copy()
df_out = df_out.rename(columns={'orig_state':'original_state','orig_district':'original_district'})
df_out['canonical_state'] = df_out['original_state']
df_out['canonical_district'] = df_out['original_district']

df_out.to_csv(out_csv, index=False)
print("Wrote revert mapping:", out_csv)
print("Sample rows:")
print(df_out.head(30).to_string(index=False))