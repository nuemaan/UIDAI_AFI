
import pandas as pd
from pathlib import Path
import csv
import sys

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
OUT = PROJECT / "outputs"
DOCS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

MANUAL_CSV = DOCS / "manual_review_suggestions.csv"


INPUT_FILES = {
    "enrolment": [
        OUT / "cleaned_enrolment_final_reverted.csv",
        OUT / "cleaned_enrolment_final_fixed.csv",
        OUT / "cleaned_enrolment_final_nodrop.csv",
        OUT / "cleaned_enrolment_final.csv",
    ],
    "demographic": [
        OUT / "cleaned_demographic_final_reverted.csv",
        OUT / "cleaned_demographic_final_fixed.csv",
        OUT / "cleaned_demographic_final_nodrop.csv",
        OUT / "cleaned_demographic_final.csv",
    ],
    "biometric": [
        OUT / "cleaned_biometric_final_reverted.csv",
        OUT / "cleaned_biometric_final_fixed.csv",
        OUT / "cleaned_biometric_final_nodrop.csv",
        OUT / "cleaned_biometric_final.csv",
    ],
}

CHUNKSIZE = 500_000

def norm(s):
    if pd.isna(s) or s is None:
        return ""
    s = str(s).strip()
    s = " ".join(s.split())
    s = s.replace("&", "and")
    return s

def pick_input(cands):
    for p in cands:
        if p.exists():
            return p
    return None

def load_manual_map(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing manual suggestions file: {path}")
    sheet = pd.read_csv(path, dtype=str, low_memory=False).fillna("")

    required = {'original_state','original_district','canonical_state','canonical_district'}
    if not required.issubset(set(sheet.columns)):
        raise ValueError(f"manual_review_suggestions.csv missing required columns: {required - set(df.columns)}")

    mapping = {}
    for _, r in sheet.iterrows():
        orig_state = norm(r['original_state']).lower()
        orig_district = norm(r['original_district']).lower()
        can_state = r['canonical_state'].strip()
        can_district = r['canonical_district'].strip()

        if can_district:
            mapping[(orig_state, orig_district)] = (can_state, can_district)
    return mapping, sheet

def apply_to_dataset(dataset, mapping):
    inp = pick_input(INPUT_FILES[dataset])
    if inp is None:
        print(f"[WARN] No input file found for {dataset}. Skipping.")
        return None
    out_fp = OUT / f"cleaned_{dataset}_final_review_applied.csv"
    print(f"Processing {dataset}: {inp} -> {out_fp}")
    applied_counts = 0
    total_rows = 0

    applied_keys = {}
    reader = pd.read_csv(inp, dtype=str, low_memory=False, chunksize=CHUNKSIZE)
    first_write = True
    for chunk in reader:
        total_rows += len(chunk)

        if 'state' not in chunk.columns or 'district' not in chunk.columns:
            raise ValueError(f"Input {inp} missing required columns 'state'/'district'")

        state_norm = chunk['state'].fillna("").map(norm).str.lower()
        dist_norm = chunk['district'].fillna("").map(norm).str.lower()
        keys = list(zip(state_norm, dist_norm))

        to_apply_mask = [kdx in mapping for kdx in keys]

        if any(to_apply_mask):
            idxs = [idx for idx, m in enumerate(to_apply_mask) if m]
            for idx in idxs:
                kdx = keys[idx]
                can_state, can_district = mapping[kdx]

                chunk.iat[idx, chunk.columns.get_loc('state_clean')] = can_state if 'state_clean' in chunk.columns else can_state
                chunk.iat[idx, chunk.columns.get_loc('district_clean')] = can_district if 'district_clean' in chunk.columns else can_district
                applied_counts += 1
                applied_keys[kdx] = applied_keys.get(kdx, 0) + 1

        if first_write:
            chunk.to_csv(out_fp, index=False, quoting=csv.QUOTE_MINIMAL)
            first_write = False
        else:
            chunk.to_csv(out_fp, index=False, header=False, mode='a', quoting=csv.QUOTE_MINIMAL)
    print(f"  -> rows processed: {total_rows}, applied mappings: {applied_counts}")
    return {
        "dataset": dataset,
        "input": str(inp),
        "output": str(out_fp),
        "rows": total_rows,
        "applied": applied_counts,
        "applied_keys_count": len(applied_keys),
        "applied_keys": applied_keys
    }

def main():
    mapping, raw_df = load_manual_map(MANUAL_CSV)
    print(f"Loaded manual mapping entries to apply: {len(mapping)} (will only apply entries with non-empty canonical_district)")
    results = []
    for ds in ["enrolment", "demographic", "biometric"]:
        outcome = apply_to_dataset(ds, mapping)
        if outcome:
            results.append(outcome)

    summary_rows = []
    for r in results:
        summary_rows.append({
            "dataset": r['dataset'],
            "input": r['input'],
            "output": r['output'],
            "rows_processed": r['rows'],
            "applied_rows": r['applied'],
            "unique_mapping_keys_applied": r['applied_keys_count']
        })
    if summary_rows:
        pd.DataFrame(summary_rows).to_csv(DOCS / "final_review_applied_log.csv", index=False)

        applied_keys_all = {}
        for r in results:
            for kdx, count in r['applied_keys'].entries():
                applied_keys_all[kdx] = applied_keys_all.get(kdx, 0) + count

        manual_pairs = set((norm(val).lower(), norm(val2).lower()) for val,val2 in zip(raw_df['original_state'], raw_df['original_district']))
        not_applied = []
        for _, row in raw_df.iterrows():
            kdx = (norm(row['original_state']).lower(), norm(row['original_district']).lower())
            if kdx not in applied_keys_all:
                not_applied.append({
                    "original_state": row['original_state'],
                    "original_district": row['original_district'],
                    "canonical_state": row['canonical_state'],
                    "canonical_district": row['canonical_district']
                })
        pd.DataFrame(not_applied).to_csv(DOCS / "final_review_remaining_manual.csv", index=False)
        print(f"Wrote docs/final_review_applied_log.csv and docs/final_review_remaining_manual.csv (remaining manual pairs: {len(not_applied)})")
    else:
        print("No datasets were processed. Check input files exist.")

if __name__ == "__main__":
    main()