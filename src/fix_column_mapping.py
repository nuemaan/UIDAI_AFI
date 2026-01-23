
"""
fix_column_mapping.py
  - Reads docs/column_mapping_exact.csv (or template) and attempts to fix mappings
    where the source_column does not match the actual CSV header.
  - Writes docs/column_mapping_exact_fixed.csv with any replacements applied.
  - Prints a summary of changes.
Usage:
  python3 src/fix_column_mapping.py
After running: inspect docs/column_mapping_exact_fixed.csv then re-run
  python3 src/apply_exact_column_mapping.py
"""

import csv
import difflib
import os
import sys
import pandas as pd

MAPPING_IN = "docs/column_mapping_exact.csv"
MAPPING_OUT = "docs/column_mapping_exact_fixed.csv"


COMMON_ALIASES = {
    "state": ["state_canonical", "state_clean", "state"],
    "district": ["district_clean", "district", "district_name"],
    "pincode": ["pincode", "pin", "postalcode", "pin_code"],
    "enrol_total": ["enrol_total", "enrolments", "enrol_total_count", "enrol_count"],
    "demo_total": ["demo_total", "demographic_total", "demo_total_count", "demo_count"],
    "bio_total": ["bio_total", "biometric_total", "bio_total_count", "bio_count"],
    "period": ["period", "month", "period_month"],
    "afi_composite_score": ["afi_composite_score", "afi_score", "afi"],
}

def read_mapping(path):
    if not os.path.exists(path):
        print(f"[ERR] mapping file not found: {path}")
        sys.exit(1)
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(r)
    return rows, reader.fieldnames

def headers_for_file(srcfile):
    if not os.path.exists(srcfile):
        print(f"[WARN] source file not found: {srcfile}")
        return []
    try:
        sheet = pd.read_csv(srcfile, nrows=0)
        return list(sheet.columns)
    except Exception as e:
        print(f"[WARN] could not read headers from {srcfile}: {e}")
        return []

def best_match(missing, headers):

    low = missing.lower()
    if low in COMMON_ALIASES:
        for cand in COMMON_ALIASES[low]:
            for h in headers:
                if h.lower() == cand.lower():
                    return h, "alias"

    for h in headers:
        if h.lower() == missing.lower():
            return h, "exact_ci"

    candidates = difflib.get_close_matches(missing, headers, n=1, cutoff=0.6)
    if candidates:
        return candidates[0], "fuzzy"

    return None, None

def main():
    rows, fields = read_mapping(MAPPING_IN)

    headers_cache = {}
    changes = []
    for r in rows:
        src = r.get("source_file")
        src_col = r.get("source_column")

        if not src or not src_col:
            continue
        if src not in headers_cache:
            headers_cache[src] = headers_for_file(src)
        headers = headers_cache[src]
        if src_col in headers:
            continue

        match, method = best_match(src_col, headers)
        if match:
            changes.append((src, src_col, match, method))
            r["source_column"] = match
        else:

            changes.append((src, src_col, None, "MISSING"))

    with open(MAPPING_OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"WROTE: {MAPPING_OUT}")
    if changes:
        print("Summary of suggested fixes / findings:")
        for src, old, new, method in changes:
            if new:
                print(f"  {src}: {old}  ->  {new}   ({method})")
            else:
                print(f"  {src}: {old}  ->  [NO MATCH FOUND]")
    else:
        print("No changes needed; all mapped source columns were present.")
    print("\nNext steps:")
    print(" 1) Inspect docs/column_mapping_exact_fixed.csv and confirm changes.")
    print(" 2) Replace docs/column_mapping_exact.csv with the fixed file (or use it directly).")
    print(" 3) Re-run: python3 src/apply_exact_column_mapping.py")

if __name__ == "__main__":
    main()