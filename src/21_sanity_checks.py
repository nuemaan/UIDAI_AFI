
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "outputs"
DOCS = PROJECT / "docs"
DOCS.mkdir(exist_ok=True)

FILES = {
    "enrolment": OUT / "cleaned_enrolment_final_canonical_state_applied_extra_applied.csv",
    "demographic": OUT / "cleaned_demographic_final_canonical_state_applied_extra_applied.csv",
    "biometric": OUT / "cleaned_biometric_final_canonical_state_applied_extra_applied.csv",
}

def short(sheet):
    return sheet.head(5).to_dict(orient='records')

reports = []
for name, file_handle in FILES.entries():
    if not file_handle.exists():
        print(f"[MISSING] {name} file not found: {fp}")
        continue
    print(f"\n--- {name} ---")
    sheet = pd.read_csv(file_handle, dtype=str, low_memory=False)
    n = len(sheet)

    state_unique = sheet['state'].fillna('').str.strip().nunique()
    stateclean_unique = sheet['state_clean'].fillna('').str.strip().nunique() if 'state_clean' in sheet.columns else None
    empty_stateclean = int((sheet.get('state_clean','').fillna('')=='').sum())
    mismatch = int(((sheet['state'].fillna('') != sheet.get('state_clean',sheet['state']).fillna('')) | (sheet['district'].fillna('') != sheet.get('district_clean',sheet['district']).fillna(''))).sum())
    mismatch_pct = mismatch / n * 100

    sheet['orig_pair'] = sheet['state'].fillna('') + " / " + sheet['district'].fillna('')
    sheet['clean_pair'] = sheet.get('state_clean', sheet['state']).fillna('') + " / " + sheet.get('district_clean', sheet['district']).fillna('')
    changes = sheet[sheet['orig_pair'] != sheet['clean_pair']]
    top_changes = changes.groupby(['orig_pair','clean_pair']).size().reset_index(name='count').sort_values('count', ascending=False).head(20)

    report = {
        "dataset": name,
        "rows": n,
        "state_unique": int(state_unique),
        "state_clean_unique": int(stateclean_unique) if stateclean_unique is not None else None,
        "empty_state_clean_rows": int(empty_stateclean),
        "rows_with_state_or_district_changed": int(mismatch),
        "pct_changed": round(mismatch_pct,3),
        "top_changes_sample": top_changes.to_dict(orient='records')
    }
    reports.append(report)

    top_changes.to_csv(DOCS / f"sanity_top_changes_{name}.csv", index=False)
    sheet.head(100).to_csv(DOCS / f"sanity_sample_head_{name}.csv", index=False)
    print(f"rows: {n}, state_unique: {state_unique}, state_clean_unique: {stateclean_unique}, empty_state_clean: {empty_stateclean}")
    print(f"rows with state/district changed: {mismatch} ({mismatch_pct:.2f}%)")
    print(f"wrote docs/sanity_top_changes_{name}.csv and sanity_sample_head_{name}.csv")


pd.DataFrame(reports).to_csv(DOCS / "sanity_checks_summary.csv", index=False)
print("\nWrote docs/sanity_checks_summary.csv")