

import pandas as pd
from pathlib import Path
from datetime import datetime


FILES = [
    "outputs/cleaned_enrolment_final_canonical_state_applied_extra_applied_100000_to_UNKNOWN.csv",
    "outputs/cleaned_demographic_final_canonical_state_applied_extra_applied_100000_to_UNKNOWN.csv",
    "outputs/cleaned_biometric_final_canonical_state_applied_extra_applied_100000_to_UNKNOWN.csv",
]


DAMAN_CORRECT_CANONICAL = "Dadra and Nagar Haveli and Daman and Diu"


UNKNOWN = "UNKNOWN"


def is_daman_like(s: pd.Series) -> pd.Series:
    """
    True where the given string series likely refers to Daman & Diu.
    Checks for presence of 'daman' and 'diu' (case-insensitive).
    """
    s2 = s.fillna("").astype(str).str.lower()
    return s2.str.contains("daman") & s2.str.contains("diu")

timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

for file_handle in FILES:
    p = Path(file_handle)
    if not p.exists():
        print(f"[SKIP] {fp} not found.")
        continue


    bak = p.with_name(p.name + f".bak.{timestamp}")
    p.replace(bak)
    bak_path = bak
    print(f"[BACKUP] moved {p.name} -> {bak_path.name}")


    out_path = Path(str(file_handle).replace(".csv", "_fixed.csv"))


    chunksize = 200_000
    total_rows_in = 0
    total_written = 0
    daman_fixed = 0
    unknown_removed = 0

    reader = pd.read_csv(bak_path, dtype=str, chunksize=chunksize, low_memory=False)
    first_chunk = True
    for chunk in reader:

        n_in_chunk = len(chunk)
        total_rows_in += n_in_chunk



        for col in ("state", "state_clean", "state_clean_prev", "state_canonical", "state_canonical_source"):
            if col not in chunk.columns:
                chunk[col] = ""


        daman_mask = (
            is_daman_like(chunk["state_clean_prev"]) |
            is_daman_like(chunk["state_clean"]) |
            is_daman_like(chunk["state"])
        )


        cond_fix = daman_mask & (chunk["state_canonical"] == "Andaman and Nicobar Islands")
        if cond_fix.any():
            chunk.loc[cond_fix, "state_canonical"] = DAMAN_CORRECT_CANONICAL

            chunk.loc[cond_fix, "state_canonical_source"] = "manual_fix_daman"
            fixed_count = int(cond_fix.sum())
            daman_fixed += fixed_count


        unknown_mask = (chunk["state_canonical"] == UNKNOWN)
        if unknown_mask.any():
            unknown_removed += int(unknown_mask.sum())

            chunk = chunk.loc[~unknown_mask].copy()


        if first_chunk:
            chunk.to_csv(out_path, index=False, mode="w")
            first_chunk = False
        else:
            chunk.to_csv(out_path, index=False, mode="a", header=False)

        total_written += len(chunk)


    print(f"[DONE] {p.name} -> {out_path.name}")
    print(f"  rows_read: {total_rows_in:,}")
    print(f"  rows_written: {total_written:,}")
    print(f"  daman_fixed: {daman_fixed:,}")
    print(f"  unknown_rows_removed: {unknown_removed:,}")
    print(f"  backup kept at: {bak_path}")
    print("")

print("All files processed. Re-run sanity_checks.py next to validate final state.")