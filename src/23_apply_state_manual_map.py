
"""
Apply manual state canonical mappings (safe, chunked).
Place this script at project root: UIDAI_AFI/src/23_apply_state_manual_map.py
Run it from project root while your venv is active.
"""

import csv
import difflib
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "outputs"
DOCS = PROJECT / "docs"
DOCS.mkdir(exist_ok=True)

FILES = {
    "enrolment": OUT / "cleaned_enrolment_final_review_applied.csv",
    "demographic": OUT / "cleaned_demographic_final_review_applied.csv",
    "biometric": OUT / "cleaned_biometric_final_review_applied.csv",
}


WHITELIST = [
"Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat",
"Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh",
"Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan",
"Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
"Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli and Daman and Diu",
"Delhi","Jammu and Kashmir","Ladakh","Puducherry","Lakshadweep"
]


MANUAL_MAP = {
    "Raja Annamalai Puram": "Tamil Nadu",
    "Nagpur": "Maharashtra",
    "Puttenahalli": "Karnataka",
    "Madanapalle": "Andhra Pradesh",
    "Jaipur": "Rajasthan",
    "Balanagar": "Telangana",
    "Darbhanga": "Bihar",

}


FUZZY_THRESH = 0.92

def norm(s):
    if pd.isna(s): return ""
    return " ".join(str(s).strip().split())

def best_fuzzy(s):
    best = None
    best_score = 0.0
    for w in WHITELIST:
        score = difflib.SequenceMatcher(None, s.lower(), w.lower()).ratio()
        if score > best_score:
            best_score = score
            best = w
    return best, best_score

timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
revert_rows = []
apply_log_rows = []

for ds, file_handle in FILES.entries():
    if not file_handle.exists():
        print(f"[WARN] file missing: {fp}")
        continue

    backup_fp = OUT / f"{fp.name}.bak.{timestamp}"
    shutil.copy2(file_handle, backup_fp)
    print(f"[INFO] backed up {fp} -> {backup_fp}")

    out_fp = OUT / f"cleaned_{ds}_final_canonical_state_applied.csv"

    chunksize = 100000
    total_rows = 0
    counts = {"whitelist":0, "manual_map":0, "fuzzy_auto":0, "needs_review":0}


    reader = pd.read_csv(file_handle, dtype=str, low_memory=False, chunksize=chunksize)
    first = True
    for chunk in reader:
        chunk = chunk.fillna("")
        total_rows += len(chunk)

        state_prev = []
        state_canonical = []
        source_col = []
        for s in chunk.get('state_clean', pd.Series([""]*len(chunk))):
            s_norm = norm(s)
            state_prev.append(s_norm)
            if s_norm in WHITELIST:
                state_canonical.append(s_norm)
                source_col.append("whitelist")
                counts["whitelist"] += 1
            elif s_norm in MANUAL_MAP:
                mapped = MANUAL_MAP[s_norm]
                state_canonical.append(mapped)
                source_col.append("manual_map")
                counts["manual_map"] += 1
                revert_rows.append((s_norm, mapped))
            else:
                best, score = best_fuzzy(s_norm)
                if best and score >= FUZZY_THRESH:
                    state_canonical.append(best)
                    source_col.append("fuzzy_auto")
                    counts["fuzzy_auto"] += 1
                    revert_rows.append((s_norm, best))
                else:
                    state_canonical.append(s_norm)
                    source_col.append("needs_review")
                    counts["needs_review"] += 1


        chunk['state_clean_prev'] = state_prev
        chunk['state_canonical'] = state_canonical
        chunk['state_canonical_source'] = source_col


        if first:
            chunk.to_csv(out_fp, index=False, mode='w', encoding='utf-8')
            first = False
        else:
            chunk.to_csv(out_fp, index=False, header=False, mode='a', encoding='utf-8')

    apply_log_rows.append({
        "dataset": ds,
        "input_file": str(file_handle),
        "output_file": str(out_fp),
        "rows_processed": total_rows,
        **counts
    })


log_fp = DOCS / "state_canonical_apply_log.csv"
with log_fp.open('w', newline='', encoding='utf-8') as file_handle:
    writer = csv.DictWriter(file_handle, fieldnames=list(apply_log_rows[0].keys()))
    writer.writeheader()
    for r in apply_log_rows:
        writer.writerow(r)
print("WROTE:", log_fp)


revert_fp = DOCS / "revert_state_canonical_map.csv"
seen = set()
with revert_fp.open('w', newline='', encoding='utf-8') as file_handle:
    writer = csv.writer(file_handle)
    writer.writerow(["state_clean", "state_canonical"])
    for a,b in revert_rows:
        if (a,b) not in seen:
            writer.writerow([a,b])
            seen.add((a,b))
print("WROTE:", revert_fp)


needs_fp = DOCS / "state_canonical_needs_review.csv"
needs = {}
for ds, file_handle in FILES.entries():
    sheet = pd.read_csv(OUT / f"cleaned_{ds}_final_canonical_state_applied.csv", dtype=str, low_memory=False)
    for v in sheet['state_canonical'].fillna("").unique():
        if v and v not in WHITELIST:
            needs[v] = needs.get(v, 0) + (sheet['state_canonical']==v).sum()

with needs_fp.open('w', newline='', encoding='utf-8') as file_handle:
    writer = csv.writer(file_handle)
    writer.writerow(["state_canonical","total_count"])
    for kdx,v in sorted(needs.entries(), key=lambda val: val[1], reverse=True):
        writer.writerow([kdx,v])
print("WROTE:", needs_fp)

print("DONE. Check docs/state_canonical_apply_log.csv and docs/state_canonical_needs_review.csv")