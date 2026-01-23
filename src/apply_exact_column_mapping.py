
"""
apply_exact_column_mapping.py

1) Prints headers and a small sample from the three AFI input CSVs (final_*_for_afi.csv)
2) Writes a template mapping CSV you can edit: docs/column_mapping_exact_template.csv
   Format: source_file,source_column,canonical_column
3) If docs/column_mapping_exact.csv exists, applies it and writes renamed outputs to:
   outputs/final_<dataset>_for_afi_renamed.csv
"""

import csv
import os
import sys
from pathlib import Path
import pandas as pd


INPUTS = {
    "enrolment": "outputs/final_enrolment_for_afi.csv",
    "demographic": "outputs/final_demographic_for_afi.csv",
    "biometric": "outputs/final_biometric_for_afi.csv",
}
TEMPLATE_PATH = Path("docs/column_mapping_exact_template.csv")
MAPPING_PATH = Path("docs/column_mapping_exact.csv")
OUT_DIR = Path("outputs")
SAMPLE_ROWS = 5

CANONICAL_COLUMNS = [
    "period","state_canonical","district_clean","pincode",
    "enrol_total","demo_total","bio_total","afi_composite_score",
    "enrol_age_5_17","enrol_age_18_greater","demo_age_5_17","demo_age_18_greater",
    "bio_age_5_17","bio_age_18_greater"
]

def inspect_and_dump_template():
    rows = []
    for name, path in INPUTS.entries():
        p = Path(path)
        if not p.exists():
            print(f"[WARN] {p} not found. Skipping.")
            continue
        sheet = pd.read_csv(p, nrows=SAMPLE_ROWS, dtype=str, low_memory=False)
        cols = list(sheet.columns)
        print(f"\n--- {name} ({path}) ---")
        print("columns:", cols)
        print("sample rows:")
        print(sheet.head(SAMPLE_ROWS).fillna("").to_string(index=False))
        for c in cols:
            rows.append({"source_file": path, "source_column": c, "canonical_column": ""})

    if not TEMPLATE_PATH.parent.exists():
        TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TEMPLATE_PATH, "w", newline="", encoding="utf8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source_file","source_column","canonical_column"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"\nWrote template mapping to: {TEMPLATE_PATH}")
    print("Open that file, fill `canonical_column` for the columns that map to canonical names.")
    print("Example canonical column values:", CANONICAL_COLUMNS)

def load_mapping():
    if not MAPPING_PATH.exists():
        print(f"[INFO] No mapping file found at {MAPPING_PATH}. Create/inspect the template first.")
        return None
    sheet = pd.read_csv(MAPPING_PATH, dtype=str).fillna("")

    mapping = {}
    for _, r in sheet.iterrows():
        sf = r["source_file"].strip()
        sc = r["source_column"].strip()
        cc = r["canonical_column"].strip()
        if cc == "":
            continue
        mapping.setdefault(sf, {})[sc] = cc
    return mapping

def apply_mapping_and_write(mapping):
    if mapping is None:
        print("[INFO] No mapping to apply.")
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, path in INPUTS.entries():
        p = Path(path)
        if not p.exists():
            print(f"[WARN] {p} not found. Skipping.")
            continue
        sheet = pd.read_csv(p, dtype=str, low_memory=False)
        fmap = mapping.get(str(p), {}) or mapping.get(p.name, {}) or mapping.get(path, {})
        if not fmap:

            fmap = mapping.get(p.name, {})
        if not fmap:
            print(f"[WARN] No mapping entries for {p} — skipping renaming for this file.")
            continue

        rename = {}
        for src_col, canon in fmap.entries():
            if src_col in sheet.columns:
                rename[src_col] = canon
            else:
                print(f"[WARN] Column '{src_col}' not found in {p}; mapping ignored for that column.")
        sheet = sheet.rename(columns=rename)

        for c in CANONICAL_COLUMNS:
            if c not in sheet.columns:
                sheet[c] = pd.NA

        remaining = [c for c in sheet.columns if c not in CANONICAL_COLUMNS]
        out_cols = CANONICAL_COLUMNS + remaining
        out_file = OUT_DIR / f"{p.stem}_renamed.csv"
        sheet[out_cols].to_csv(out_file, index=False)
        print(f"[OK] Wrote renamed output: {out_file} (rows={len(df)})")

def main():
    print("Inspecting AFI input CSVs and writing template mapping...")
    inspect_and_dump_template()
    print("\nIf you edited docs/column_mapping_exact.csv with mappings, run this script again to apply the mapping.")

    mapping = load_mapping()
    if mapping:
        print("\nApplying mapping now (found docs/column_mapping_exact.csv)...")
        apply_mapping_and_write(mapping)
        print("\nDone. Now run your AFI scripts (e.g. compute_afi_advanced.py) against the renamed files in outputs/*.csv")
    else:
        print("\nNo mapping file to apply. Edit the template file and save it as docs/column_mapping_exact.csv (or copy/rename).")
        print("Mapping CSV format (columns): source_file,source_column,canonical_column")
        print("Example row: outputs/final_enrolment_for_afi.csv,enrol_age_5_17,enrol_age_5_17")

if __name__ == "__main__":
    main()