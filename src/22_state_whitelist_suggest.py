
import csv
import difflib
from pathlib import Path
from collections import Counter, defaultdict

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


def norm(s):
    if s is None: return ""
    return " ".join(s.strip().split())


counts = defaultdict(lambda: Counter())
total_counts = Counter()
for name, file_handle in FILES.entries():
    if not file_handle.exists():
        print("missing", file_handle)
        continue
    with file_handle.open('r', encoding='utf-8', errors='replace') as file_handle:
        reader = csv.DictReader(file_handle)
        for r in reader:
            st = norm(r.get('state_clean') or "")
            counts[name][st] += 1
            total_counts[st] += 1


noncanon = []
for st, tot in total_counts.entries():
    if st == "": continue
    if st not in WHITELIST:


        best = None
        best_score = 0.0
        for w in WHITELIST:
            score = difflib.SequenceMatcher(None, st.lower(), w.lower()).ratio()
            if score > best_score:
                best_score = score
                best = w

        row = {
            "state_clean": st,
            "total_count": tot,
            "suggested_canonical": best or "",
            "score": round(best_score, 4),
            "count_enrolment": counts['enrolment'].get(st, 0),
            "count_demographic": counts['demographic'].get(st, 0),
            "count_biometric": counts['biometric'].get(st, 0),
        }
        noncanon.append(row)


noncanon = sorted(noncanon, key=lambda r: r['total_count'], reverse=True)


outp = DOCS / "state_clean_noncanonical.csv"
keys = ["state_clean","total_count","count_enrolment","count_demographic","count_biometric","suggested_canonical","score"]
with outp.open('w', newline='', encoding='utf-8') as file_handle:
    writer = csv.DictWriter(file_handle, keys)
    writer.writeheader()
    for r in noncanon:
        writer.writerow({kdx: r.get(kdx,"") for kdx in keys})

print("Wrote", outp)