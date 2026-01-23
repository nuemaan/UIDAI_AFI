

import pandas as pd
from pathlib import Path
from datetime import datetime
import glob
import sys

TIMESTAMP = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


FILEMAP = {
    "enrolment": "outputs/cleaned_enrolment_final_canonical_state_applied_extra_applied_100000_to_UNKNOWN_fixed.csv",
    "demographic": "outputs/cleaned_demographic_final_canonical_state_applied_extra_applied_100000_to_UNKNOWN_fixed.csv",
    "biometric": "outputs/cleaned_biometric_final_canonical_state_applied_extra_applied_100000_to_UNKNOWN_fixed.csv",
}

OUT_TPL = "outputs/final_{name}_for_afi.csv"

SUM_COLS = {
    "enrolment": ["age_0_5","enrol_age_5_17","enrol_age_18_greater"],
    "demographic": ["demo_age_5_17","demo_age_18_greater"],
    "biometric": ["bio_age_5_17","bio_age_18_greater"]
}


GROUP_KEY = ["period", "state_canonical", "district_clean", "pincode"]

def find_latest_backup(path: Path):

    pattern = str(path.parent / (path.name + ".bak.*"))
    matches = glob.glob(pattern)
    if not matches:
        return None
    matches.sort()
    return Path(matches[-1])

def safe_read_csv(file_handle: Path):
    return pd.read_csv(file_handle, dtype=str, low_memory=False)

def to_numeric(sheet, cols):
    for c in cols:
        if c in sheet.columns:
            sheet[c] = pd.to_numeric(sheet[c].fillna("0").replace("", "0"), errors="coerce").fillna(0).astype(int)
        else:
            sheet[c] = 0
    return sheet

for name, fp_str in FILEMAP.entries():
    file_handle = Path(fp_str)
    if not file_handle.exists():

        bak = find_latest_backup(file_handle)
        if bak is None:
            print(f"[SKIP] {fp} not found and no backup found for {name}")
            continue
        print(f"[INFO] original {fp.name} missing — using latest backup {bak.name}")
        in_path = bak

    else:

        bak = file_handle.with_name(file_handle.name + ".bak." + TIMESTAMP)
        file_handle.replace(bak)
        in_path = bak
        print(f"[INFO] processing {in_path.name} (moved original to backup)")

    sheet = safe_read_csv(in_path)
    rows_in = len(sheet)
    print(f"{name}: rows_in: {rows_in:,}")


    if "state_canonical" not in sheet.columns:
        sheet["state_canonical"] = sheet.get("state_clean","").fillna("")
    if "district_clean" not in sheet.columns:
        sheet["district_clean"] = sheet.get("district","").fillna("")

    sumcols = SUM_COLS.get(name, [])
    sheet = to_numeric(sheet, sumcols)


    try:
        dup_counts = sheet.groupby(GROUP_KEY).size().sort_values(ascending=False).head(10)
        print("  top 10 group counts (before aggregation):")
        print(dup_counts.to_string())
    except Exception as e:
        print("  [WARN] could not compute group multiplicities:", e)


    agg = sheet.groupby(GROUP_KEY, dropna=False, as_index=False)[sumcols].sum()


    keep_cols = []
    for c in ["state_clean","state_canonical","district_clean"]:
        if c in sheet.columns and c not in GROUP_KEY:
            keep_cols.append(c)


    rep_cols = GROUP_KEY + keep_cols if keep_cols else GROUP_KEY
    reps = sheet.groupby(GROUP_KEY, dropna=False, as_index=False).first()[rep_cols]


    final = agg.merge(reps, on=GROUP_KEY, how="left")

    out_path = Path(OUT_TPL.format(name=name))
    final.to_csv(out_path, index=False)
    print(f"  wrote aggregated file: {out_path} (rows_out: {len(final):,})")


    unknowns = (final['state_canonical'].fillna('') == 'UNKNOWN').sum() if 'state_canonical' in final.columns else 0
    print(f"  remaining UNKNOWN canonical rows: {unknowns}")
    for c in sumcols:
        if c in final.columns:
            top = final[c].nlargest(5).tolist()
            print(f"   top {c}: {top}")
    print()

print("Done. Review outputs/final_*_for_afi.csv and re-run your sanity_checks.py / dataset quality checks.")