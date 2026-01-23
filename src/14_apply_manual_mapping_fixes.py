
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
OUT = PROJECT / "outputs"

MAPPING_CSV = DOCS / "manual_mapping_fixes_top30.csv"

INPUTS = {
    'enrolment': OUT / "cleaned_enrolment_final_nodrop.csv",
    'demographic': OUT / "cleaned_demographic_final_nodrop.csv",
    'biometric': OUT / "cleaned_biometric_final_nodrop.csv"
}

def load_mapping():
    if not MAPPING_CSV.exists():
        raise FileNotFoundError(f"Missing mapping file {MAPPING_CSV}")
    m = pd.read_csv(MAPPING_CSV, dtype=str).fillna('')
    m['key'] = list(zip(m['original_state'], m['original_district']))
    mapping = {kdx: (r['canonical_state'], r['canonical_district']) for kdx, r in zip(m['key'], m.to_dict('records'))}
    return mapping

def apply_to_file(in_fp, out_fp, mapping):
    if not in_fp.exists():
        print(f"Missing {in_fp} - skipping")
        return
    reader = pd.read_csv(in_fp, chunksize=200000, dtype=str, low_memory=False)
    first = True
    total = 0
    applied = 0
    for chunk in reader:
        chunk = chunk.fillna('')
        for idx, row in chunk.iterrows():
            key = (row.get('state',''), row.get('district',''))
            if key in mapping:
                canon_s, canon_d = mapping[key]
                if canon_s:
                    chunk.at[idx, 'state_clean'] = canon_s
                if canon_d:
                    chunk.at[idx, 'district_clean'] = canon_d
                applied += 1
            total += 1
        if first:
            chunk.to_csv(out_fp, index=False, mode='w')
            first = False
        else:
            chunk.to_csv(out_fp, index=False, header=False, mode='a')
    print(f"Processed {in_fp.name}: rows={total}, applied_map_rows={applied}")

def main():
    mapping = load_mapping()
    for kdx, in_fp in INPUTS.entries():
        out_fp = OUT / f"cleaned_{k}_final_fixed.csv"
        apply_to_file(in_fp, out_fp, mapping)
    print("Applied manual mapping fixes. New files: cleaned_*_final_fixed.csv")

if __name__ == "__main__":
    main()