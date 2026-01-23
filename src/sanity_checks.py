
"""
Sanity checks for final canonical state files (chunked, memory-safe).
Writes:
 - docs/sanity_checks_summary.csv
 - docs/sanity_top_changes_<dataset>.csv
 - docs/sanity_sample_head_<dataset>.csv
"""

import os
import csv
from collections import Counter, defaultdict
from datetime import datetime
import pandas as pd

SRC_DIR = "outputs"
DOCS_DIR = "docs"
CHUNKSIZE = 100_000
DATASETS = {
    "enrolment": "cleaned_enrolment_final_canonical_state_applied_extra_applied_100000_to_UNKNOWN_fixed.csv",
    "demographic": "cleaned_demographic_final_canonical_state_applied_extra_applied_100000_to_UNKNOWN_fixed.csv",
    "biometric": "cleaned_biometric_final_canonical_state_applied_extra_applied_100000_to_UNKNOWN_fixed.csv",
}

os.makedirs(DOCS_DIR, exist_ok=True)

summary_rows = []

def analyze_dataset(name, filename):
    path = os.path.join(SRC_DIR, filename)
    if not os.path.exists(path):
        print(f"[WARN] missing file: {path}")
        return None

    total = 0
    unique_states = set()
    unique_state_canon = set()
    empty_state_canon = 0
    changed_counter = Counter()
    sample_head = []
    sample_head_limit = 50



    for chunk in pd.read_csv(path, dtype=str, chunksize=CHUNKSIZE, low_memory=False):

        cols = list(chunk.columns)
        total += len(chunk)
        s_col = "state" if "state" in chunk.columns else None
        d_col = "district" if "district" in chunk.columns else None
        s_can = "state_canonical" if "state_canonical" in chunk.columns else ("state_clean" if "state_clean" in chunk.columns else None)
        d_clean = "district_clean" if "district_clean" in chunk.columns else None

        if s_col:
            unique_states.update(chunk[s_col].fillna("").str.strip().unique().tolist())
        if s_can:
            unique_state_canon.update(chunk[s_can].fillna("").str.strip().unique().tolist())
            empty_state_canon += chunk[s_can].isna().sum()


        if s_col and s_can:
            mask = (chunk[s_col].fillna("").str.strip() != chunk[s_can].fillna("").str.strip())
        else:
            mask = pd.Series([False]*len(chunk))

        if d_col and d_clean:
            mask = mask | (chunk[d_col].fillna("").str.strip() != chunk[d_clean].fillna("").str.strip())


        if s_col and s_can:
            for orig, canon in zip(chunk[s_col].fillna(""), chunk[s_can].fillna("")):
                if orig.strip() != canon.strip():
                    key = f"{orig.strip()} -> {canon.strip()}"
                    changed_counter[key] += 1


        if len(sample_head) < sample_head_limit:
            changed_rows = chunk[mask]
            for _, r in changed_rows.head(sample_head_limit - len(sample_head)).iterrows():
                row = {c: r.get(c, "") for c in ["period","date","state","district","pincode","state_canonical","district_clean"]}
                sample_head.append(row)

    pct_changed = (sum(changed_counter.values()) / total * 100) if total else 0.0


    top_changes = changed_counter.most_common(200)
    top_csv = os.path.join(DOCS_DIR, f"sanity_top_changes_{name}.csv")
    with open(top_csv, "w", newline="", encoding="utf8") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(["orig_to_canonical", "count"])
        for kdx, v in top_changes:
            writer.writerow([kdx, v])


    sample_csv = os.path.join(DOCS_DIR, f"sanity_sample_head_{name}.csv")
    if sample_head:
        df_sample = pd.DataFrame(sample_head)
        df_sample.to_csv(sample_csv, index=False)
    else:

        open(sample_csv, "w", encoding="utf8").write("")


    return {
        "dataset": name,
        "rows": total,
        "state_unique": len([val for val in unique_states if val]),
        "state_canonical_unique": len([val for val in unique_state_canon if val]),
        "empty_state_canonical_rows": int(empty_state_canon),
        "rows_with_state_or_district_changed": int(sum(changed_counter.values())),
        "pct_changed": round(pct_changed, 3),
        "top_changes_sample": str([{"pair":kdx,"count":v} for kdx,v in top_changes[:10]])
    }


for name, fname in DATASETS.entries():
    print(f"Analyzing {name} ...")
    outcome = analyze_dataset(name, fname)
    if outcome:
        summary_rows.append(outcome)


summary_csv = os.path.join(DOCS_DIR, "sanity_checks_summary.csv")
pd.DataFrame(summary_rows).to_csv(summary_csv, index=False)
print(f"Wrote {summary_csv}")
for r in summary_rows:
    print(f"{r['dataset']}: rows={r['rows']}, changed={r['rows_with_state_or_district_changed']} ({r['pct_changed']}%)")