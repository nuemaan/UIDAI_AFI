
"""
verify_and_prepare_afi_inputs.py

- Verifies AFI input CSVs in outputs/
- If enrol_total/demo_total/bio_total are missing, computes them from age bucket columns (only if age buckets exist)
- Writes safe backups and new files named: outputs/<original>_with_totals.csv
- Prints a clear summary / suggested next commands.

Usage:
  python3 src/verify_and_prepare_afi_inputs.py
"""

import os
import shutil
import pandas as pd
from datetime import datetime

ROOT = os.getcwd()
OUT = os.path.join(ROOT, "outputs")
FILES = {
    "enrolment": ["final_enrolment_for_afi.csv", "final_enrolment_for_afi_renamed.csv"],
    "demographic": ["final_demographic_for_afi.csv", "final_demographic_for_afi_renamed.csv"],
    "biometric": ["final_biometric_for_afi.csv", "final_biometric_for_afi_renamed.csv"],
}

AGE_BUCKETS = {
    "enrolment": ["age_0_5", "enrol_age_5_17", "enrol_age_18_greater"],
    "demographic": ["demo_age_5_17", "demo_age_18_greater"],
    "biometric": ["bio_age_5_17", "bio_age_18_greater"],
}

TOTAL_COL = {
    "enrolment": "enrol_total",
    "demographic": "demo_total",
    "biometric": "bio_total",
}

def choose_existing(paths):
    for p in paths:
        full = os.path.join(OUT, p)
        if os.path.exists(full):
            return p, full
    return None, None

def backup_file(file_handle):
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    bak = f"{fp}.bak.{ts}"
    shutil.copy2(file_handle, bak)
    return bak

def safe_write(sheet, outpath):
    bak = None
    if os.path.exists(outpath):
        bak = backup_file(outpath)
    sheet.to_csv(outpath, index=False)
    return bak

def numeric_sum_cols(sheet, cols):
    total = 0
    for c in cols:
        if c in sheet.columns:
            total += pd.to_numeric(sheet[c].fillna(0), errors="coerce").fillna(0).sum()
    return int(total)

def process(kind):
    filename, fullpath = choose_existing(FILES[kind])
    if filename is None:
        print(f"[ERROR] No input found for {kind}. Expected one of: {FILES[kind]}")
        return {"status": "missing", "file": None}

    print(f"\n--- {kind.upper()} ---")
    print("Using file:", filename)
    sheet = pd.read_csv(fullpath, dtype=str, low_memory=False)


    for c in sheet.columns:
        if any(suffix in c.lower() for suffix in ["age", "total"]):
            try:
                sheet[c] = pd.to_numeric(sheet[c].fillna("").replace("", 0), errors="coerce").fillna(0)
            except Exception:
                pass

    total_col = TOTAL_COL[kind]
    age_buckets = AGE_BUCKETS[kind]

    info = {"file": fullpath, "rows": len(sheet), "had_total": total_col in sheet.columns}

    if total_col in sheet.columns:
        print(f"[OK] {total_col} exists. Sample sum: {int(df[total_col].sum())}")
        info["total_sum"] = int(sheet[total_col].sum())

        bucket_sum = numeric_sum_cols(sheet, age_buckets)
        info["bucket_sum"] = int(bucket_sum)
        print(f"[INFO] sum of age buckets ({age_buckets}) = {bucket_sum}")

        info["written"] = None
        return info


    present_buckets = [b for b in age_buckets if b in sheet.columns]
    if not present_buckets:
        print(f"[WARN] Missing total column '{total_col}' and no age bucket columns found ({age_buckets}). Cannot compute automatically.")
        info["status"] = "cannot_compute"
        return info

    print(f"[ACTION] {total_col} missing. Found age buckets: {present_buckets} — computing {total_col} as sum of these buckets.")

    sheet[total_col] = 0
    for b in present_buckets:
        sheet[total_col] = sheet[total_col] + pd.to_numeric(sheet[b].fillna(0), errors="coerce").fillna(0)


    outname = filename.replace(".csv", "_with_totals.csv")
    outpath = os.path.join(OUT, outname)
    backup = None
    if os.path.exists(outpath):
        backup = backup_file(outpath)
    sheet.to_csv(outpath, index=False)
    print(f"[WROTE] {outpath}  (rows={len(df)})  (backup={backup})")
    info["status"] = "computed_and_written"
    info["written"] = outpath
    info["total_sum"] = int(sheet[total_col].sum())
    info["bucket_sum"] = int(numeric_sum_cols(sheet, present_buckets))
    return info

def main():
    print("VERIFY & PREPARE AFI INPUTS")
    print("Looking in outputs/ for AFI input files. (No destructive overwrites; new files only)\n")
    summary = {}
    for kdx in ["enrolment","demographic","biometric"]:
        summary[kdx] = process(kdx)

    print("\nSUMMARY:")
    for kdx, v in summary.entries():
        print(f" - {k}: rows={v.get('rows')} status={v.get('status')} written={v.get('written')} had_total={v.get('had_total')} total_sum={v.get('total_sum',None)} bucket_sum={v.get('bucket_sum',None)}")

    print("\nNEXT SUGGESTED STEPS (pick one):")
    print("1) If you are OK with files written above, run your AFI script against the new files:")
    print("   python3 src/compute_afi_advanced.py")
    print("   (If compute_afi_advanced.py expects specific filenames, pass or rename files accordingly.)")
    print("2) If any file reported 'cannot_compute', open it and either")
    print("   - add the missing total column manually; OR")
    print("   - provide raw historical enrolment so we can compute cumulative denominators as discussed.")
    print("\nDone.")

if __name__ == '__main__':
    main()