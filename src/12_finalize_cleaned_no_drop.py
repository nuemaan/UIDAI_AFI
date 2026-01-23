
import pandas as pd
from pathlib import Path
import re

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "outputs"
DOCS = PROJECT / "docs"


INPUT_FILES = {
    "enrolment": OUT / "cleaned_enrolment_applied_autoaccepts.csv",
    "demographic": OUT / "cleaned_demographic_applied_autoaccepts.csv",
    "biometric": OUT / "cleaned_biometric_applied_autoaccepts.csv"
}


MAPPING_FILES = [
    DOCS / "state_district_mapping_auto_enrolment.csv",
    DOCS / "state_district_mapping_enrolment.csv",
    DOCS / "state_district_mapping_suggestions_enrolment.csv",
    DOCS / "state_district_mapping_suggestions_demographic.csv",
    DOCS / "state_district_mapping_suggestions_biometric.csv",
    DOCS / "state_district_mapping_auto_enrolment.csv",
    DOCS / "state_district_mapping_demographic.csv",
    DOCS / "state_district_mapping_biometric.csv",
    DOCS / "state_district_mapping_suggestions_enrolment.csv",
    DOCS / "state_district_bulk_suggestions_enrolment.csv",
    DOCS / "state_district_bulk_suggestions_demographic.csv",
    DOCS / "state_district_bulk_suggestions_biometric.csv",
    DOCS / "suspicious_resolution_candidates.csv",
]

def title_case(s):
    if pd.isna(s) or s is None:
        return ''
    s = str(s).strip()
    s = re.sub(r'\s+', ' ', s)
    return ' '.join([w.capitalize() for w in s.split()])

def load_mappings():

    mapping = {}
    for mp in MAPPING_FILES:
        if not mp.exists():
            continue
        try:
            sheet = pd.read_csv(mp, dtype=str).fillna('')
        except Exception:
            continue

        for _, r in sheet.iterrows():
            orig_s = r.get('original_state') or r.get('state') or r.get('original_state_name') or ''
            orig_d = r.get('original_district') or r.get('district') or ''

            canon_s = r.get('canonical_state') or r.get('canonical_state_suggestion') or r.get('proposed_canonical_state') or r.get('suggested_state') or ''
            canon_d = r.get('canonical_district') or r.get('canonical_district_suggestion') or r.get('proposed_canonical_district') or r.get('proposed_canonical_district') or r.get('suggested_district') or ''
            key = (orig_s, orig_d)

            if key not in mapping:
                if canon_s or canon_d:
                    mapping[key] = (canon_s.strip(), canon_d.strip())
            else:

                ex_s, ex_d = mapping[key]
                new_s = canon_s.strip() if canon_s.strip() else ex_s
                new_d = canon_d.strip() if canon_d.strip() else ex_d
                mapping[key] = (new_s, new_d)
    return mapping

def finalize_dataset(name, in_fp):
    if not in_fp.exists():
        print(f"[WARN] input missing: {in_fp}  (skipping {name})")
        return None
    print(f"Processing {name} -> final_nodrop")
    df_iter = pd.read_csv(in_fp, chunksize=500000, dtype=str, low_memory=False)
    out_fp = OUT / f"cleaned_{name}_final_nodrop.csv"
    summary_rows = []
    mapping = load_mappings()
    total = 0
    applied = 0
    kept_original = 0
    first = True
    for chunk in df_iter:
        chunk = chunk.fillna('')

        chunk['state_clean'] = chunk['state'].apply(title_case)
        chunk['district_clean'] = chunk['district'].apply(title_case)

        for idx, row in chunk.iterrows():
            key = (row.get('state',''), row.get('district',''))
            if key in mapping:
                canon_s, canon_d = mapping[key]
                if canon_s:
                    chunk.at[idx, 'state_clean'] = title_case(canon_s)
                if canon_d:
                    chunk.at[idx, 'district_clean'] = title_case(canon_d)

                if canon_s or canon_d:
                    applied += 1
                else:
                    kept_original += 1
            else:
                kept_original += 1
            total += 1

        if first:
            chunk.to_csv(out_fp, index=False, mode='w')
            first = False
        else:
            chunk.to_csv(out_fp, index=False, header=False, mode='a')

    summary_rows.append({
        'dataset': name,
        'total_rows': total,
        'rows_with_canonical_applied': applied,
        'rows_kept_original_titlecased': kept_original
    })
    pd.DataFrame(summary_rows).to_csv(DOCS / f"cleaning_summary_{name}.csv", index=False)
    print(f"Finished {name}: total={total}, applied={applied}, kept_original={kept_original}")
    return (total, applied, kept_original)

if __name__ == "__main__":
    results = {}
    for name, file_handle in INPUT_FILES.entries():
        outcome = finalize_dataset(name, file_handle)
        results[name] = outcome
    print("Done. Summary written to docs/cleaning_summary_<dataset>.csv")