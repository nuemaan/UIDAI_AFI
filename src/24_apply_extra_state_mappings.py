

import csv, shutil
from pathlib import Path
import pandas as pd
PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "outputs"
DOCS = PROJECT / "docs"
FILES = [
    OUT / "cleaned_enrolment_final_canonical_state_applied.csv",
    OUT / "cleaned_demographic_final_canonical_state_applied.csv",
    OUT / "cleaned_biometric_final_canonical_state_applied.csv",
]

EXTRA_MAP = {
    "Jammu & Kashmir": "Jammu and Kashmir",
    "Jammu And Kashmir": "Jammu and Kashmir",
    "Pondicherry": "Puducherry",
    "West Bangal": "West Bengal",
    "West Bengli": "West Bengal",
    "Westbengal": "West Bengal",
    "Uttaranchal": "Uttarakhand",
    "Orissa": "Odisha",
    "Chhatisgarh": "Chhattisgarh",

}


for file_handle in FILES:
    if file_handle.exists():
        shutil.copy2(file_handle, file_handle.with_suffix(file_handle.suffix + ".bak.extra_map"))


for file_handle in FILES:
    if not file_handle.exists():
        print("missing", file_handle); continue
    sheet = pd.read_csv(file_handle, dtype=str, low_memory=False)
    sheet = sheet.fillna("")
    applied = []
    for src, tgt in EXTRA_MAP.entries():
        mask = sheet['state_canonical'].str.strip().eq(src)
        if mask.any():
            sheet.loc[mask, 'state_canonical'] = tgt

            sheet.loc[mask, 'state_canonical_source'] = 'manual_map'
            applied.append((src, tgt, int(mask.sum())))
    outp = OUT / file_handle.name.replace(".csv", "_extra_applied.csv")
    sheet.to_csv(outp, index=False)
    print(f"WROTE {outp}  (applied mappings: {applied})")


revert_fp = DOCS / "revert_state_canonical_map.csv"
existing = set()
if revert_fp.exists():
    with open(revert_fp, newline="", encoding="utf-8") as fh:
        rdr = csv.reader(fh)
        next(rdr, None)
        for r in rdr:
            if len(r)>=2: existing.add((r[0], r[1]))
with open(revert_fp, "a", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    if revert_fp.stat().st_size == 0:
        w.writerow(["state_clean","state_canonical"])
    for s,t in EXTRA_MAP.entries():
        if (s,t) not in existing:
            w.writerow([s,t])
print("Updated revert map:", revert_fp)


needs = {}
for file_handle in FILES:
    p = OUT / file_handle.name.replace(".csv", "_extra_applied.csv")
    if not p.exists(): p = file_handle
    sheet = pd.read_csv(p, dtype=str, low_memory=False)
    for v in sheet['state_canonical'].fillna("").unique():
        if v and v not in [""] and v not in [
            "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat",
            "Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh",
            "Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan",
            "Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
            "Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli and Daman and Diu",
            "Delhi","Jammu and Kashmir","Ladakh","Puducherry","Lakshadweep","100000"
        ]:
            needs[v] = needs.get(v,0) + (sheet['state_canonical']==v).sum()

needs_fp = DOCS / "state_canonical_needs_review.csv"
with open(needs_fp, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["state_canonical","total_count"])
    for kdx,v in sorted(needs.entries(), key=lambda val: val[1], reverse=True):
        w.writerow([kdx,v])
print("WROTE needs review:", needs_fp)