
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "outputs"
DOCS = PROJECT / "docs"


ENR_CANDIDATES = [
    OUT / "cleaned_enrolment_final_reverted.csv",
    OUT / "cleaned_enrolment_final_fixed.csv",
    OUT / "cleaned_enrolment_final_nodrop.csv",
    OUT / "cleaned_enrolment_final.csv",
]

def pick_file(cands):
    for p in cands:
        if p.exists():
            return p
    return None

ENR = pick_file(ENR_CANDIDATES)
if ENR is None:
    raise FileNotFoundError("No enrolment cleaned file found. Expected one of: " + ", ".join(str(p.name) for p in ENR_CANDIDATES))

def load_enrol(file_handle):
    sheet = pd.read_csv(file_handle, dtype=str, low_memory=False).fillna('')

    if 'enrol_total' in sheet.columns:
        sheet['enrol_total'] = pd.to_numeric(sheet['enrol_total'], errors='coerce').fillna(0)
    else:
        age_cols = ['age_0_5','age_5_17','age_18_greater','enrol_age_5_17']
        for c in age_cols:
            if c in sheet.columns:
                sheet[c] = pd.to_numeric(sheet[c].fillna(0), errors='coerce').fillna(0)
            else:
                sheet[c] = 0
        if sheet['enrol_age_5_17'].sum() > 0:
            sheet['age_5_17'] = sheet['enrol_age_5_17']
        sheet['enrol_total'] = sheet[['age_0_5','age_5_17','age_18_greater']].sum(axis=1)
    sheet['enrol_total'] = pd.to_numeric(sheet['enrol_total'], errors='coerce').fillna(0)
    return sheet

def main():
    print("Audit will use enrolment file:", ENR)
    sheet = load_enrol(ENR)
    mask = (sheet['district'].astype(str).str.strip() != sheet['district_clean'].astype(str).str.strip()) |\
           (sheet['state'].astype(str).str.strip() != sheet['state_clean'].astype(str).str.strip())
    changed = sheet[mask].copy()
    if changed.empty:
        print("No mapping changes detected.")
        return
    changed['orig_pair'] = list(zip(changed['state'], changed['district']))
    changed['clean_pair'] = list(zip(changed['state_clean'], changed['district_clean']))
    grouped = changed.groupby(['orig_pair','clean_pair'])['enrol_total'].sum().reset_index()
    grouped = grouped.sort_values('enrol_total', ascending=False)
    grouped[['orig_state','orig_district']] = pd.DataFrame(grouped['orig_pair'].tolist(), index=grouped.index)
    grouped[['clean_state','clean_district']] = pd.DataFrame(grouped['clean_pair'].tolist(), index=grouped.index)
    grouped = grouped[['orig_state','orig_district','clean_state','clean_district','enrol_total']]
    out_fp = DOCS / "top_mapping_changes.csv"
    grouped.to_csv(out_fp, index=False)
    print(f"Wrote {out_fp}")
    print("\nTop 30 mapping changes by enrol_total:")
    print(grouped.head(30).to_string(index=False))

if __name__ == "__main__":
    main()