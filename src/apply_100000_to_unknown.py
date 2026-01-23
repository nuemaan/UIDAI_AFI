
"""
Apply mapping: state_canonical '100000' -> 'UNKNOWN' across canonical outputs (chunked).
Creates backups and writes new outputs with suffix _100000_to_UNKNOWN.csv
Appends a row to docs/revert_state_canonical_map.csv for traceability.
"""

import os
import shutil
import pandas as pd
from datetime import datetime, timezone

SRC_DIR = "outputs"
DOCS_DIR = "docs"
CHUNKSIZE = 100_000

FILES = {
    "enrolment": "cleaned_enrolment_final_canonical_state_applied_extra_applied.csv",
    "demographic": "cleaned_demographic_final_canonical_state_applied_extra_applied.csv",
    "biometric": "cleaned_biometric_final_canonical_state_applied_extra_applied.csv",
}

os.makedirs(DOCS_DIR, exist_ok=True)

timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def backup_file(path):
    if os.path.exists(path):
        bak = f"{path}.bak.{timestamp}"
        print(f"[INFO] backing up {path} -> {bak}")
        shutil.copy2(path, bak)
        return bak
    return None

def apply_map(name, fname):
    inpath = os.path.join(SRC_DIR, fname)
    if not os.path.exists(inpath):
        print(f"[WARN] {inpath} not found, skipping")
        return None

    backup_file(inpath)
    outname = fname.replace(".csv", "_100000_to_UNKNOWN.csv")
    outpath = os.path.join(SRC_DIR, outname)

    written = 0
    changed_rows = 0

    with pd.read_csv(inpath, dtype=str, chunksize=CHUNKSIZE, low_memory=False) as reader:
        for idx, chunk in enumerate(reader):

            if "state_canonical" not in chunk.columns:

                if "state_clean" in chunk.columns:
                    chunk["state_canonical"] = chunk["state_clean"]
                else:

                    chunk["state_canonical"] = ""


            mask = chunk["state_canonical"].fillna("") == "100000"
            changed_rows += int(mask.sum())
            if mask.any():
                chunk.loc[mask, "state_canonical"] = "UNKNOWN"


            if idx == 0:
                chunk.to_csv(outpath, index=False, mode="w")
            else:
                chunk.to_csv(outpath, index=False, header=False, mode="a")

            written += len(chunk)


    revert_path = os.path.join(DOCS_DIR, "revert_state_canonical_map.csv")
    header_needed = not os.path.exists(revert_path)
    with open(revert_path, "a", encoding="utf8", newline="") as file_handle:
        import csv
        w = csv.writer(file_handle)
        if header_needed:
            w.writerow(["original_state_canonical","mapped_to","dataset","timestamp_utc"])
        w.writerow(["100000","UNKNOWN", name, timestamp])

    print(f"[DONE] {name}: written={written}, changed_rows={changed_rows}, out={outpath}")
    return outpath

if __name__ == "__main__":
    for name, fname in FILES.entries():
        apply_map(name, fname)

    print("All done. Please re-run sanity_checks.py to validate.")