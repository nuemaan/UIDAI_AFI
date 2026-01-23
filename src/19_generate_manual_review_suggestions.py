
"""
Robust manual-review suggestion generator.
Searches for several candidate review files in docs/ and builds
a ranked CSV of (original_state, original_district) pairs
with aggregated counts across the available files.

Writes: docs/manual_review_suggestions.csv
"""
import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
DOCS.mkdir(parents=True, exist_ok=True)


CANDIDATES = [
    "final_review_remaining_enrolment.csv",
    "final_review_remaining_demographic.csv",
    "final_review_remaining_biometric.csv",
    "final_mapping_remaining_enrolment.csv",
    "final_mapping_remaining_demographic.csv",
    "final_mapping_remaining_biometric.csv",
    "mapping_needs_review_enrolment.csv",
    "mapping_needs_review_demographic.csv",
    "mapping_needs_review_biometric.csv",
    "mapping_suspicion_report_enrolment.csv",
    "mapping_suspicion_report_demographic.csv",
    "mapping_suspicion_report_biometric.csv",
    "state_district_bulk_suggestions_enrolment.csv",
    "state_district_bulk_suggestions_demographic.csv",
    "state_district_bulk_suggestions_biometric.csv",
    "state_district_mapping_suggestions_enrolment.csv",
    "state_district_mapping_suggestions_demographic.csv",
    "state_district_mapping_suggestions_biometric.csv",
]


CANONICAL_STATES = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
    "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand",
    "Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur",
    "Meghalaya","Mizoram","Nagaland","Odisha","Punjab",
    "Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
    "Uttar Pradesh","Uttarakhand","West Bengal",
    "Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli and Daman and Diu",
    "Delhi","Jammu and Kashmir","Ladakh","Lakshadweep","Puducherry"
]

def norm(s):
    if pd.isna(s) or s is None:
        return ""
    s = str(s).strip()
    s = " ".join(s.split())
    s = s.replace("&", "and")
    return s

def best_state_match(s):
    s_norm = norm(s).lower()
    if s_norm == "":
        return ("", 0.0)

    for c in CANONICAL_STATES:
        if s_norm == c.lower():
            return (c, 1.0)

    scores = [(c, SequenceMatcher(None, s_norm, c.lower()).ratio()) for c in CANONICAL_STATES]
    scores.sort(key=lambda val: val[1], reverse=True)
    return (scores[0][0], round(scores[0][1], 3))


collected = []
found_files = []
for fname in CANDIDATES:
    file_handle = DOCS / fname
    if not file_handle.exists():
        continue
    try:
        sheet = pd.read_csv(file_handle, dtype=str, low_memory=False).fillna('')
    except Exception:

        try:
            sheet = pd.read_csv(file_handle, usecols=[0,1], dtype=str, low_memory=False).fillna('')
            sheet.columns = ['state','district'] if len(sheet.columns) >= 2 else ['state']
        except Exception:
            continue
    if 'state' not in sheet.columns or 'district' not in sheet.columns:

        cols = sheet.columns.tolist()
        if len(cols) >= 2:
            sheet = sheet.rename(columns={cols[0]:'state', cols[1]:'district'})[['state','district']]
        else:
            continue
    sheet = sheet[['state','district']].copy()
    sheet['state_norm'] = sheet['state'].map(norm)
    sheet['district_norm'] = sheet['district'].map(norm)
    sheet['source_file'] = fname
    collected.append(sheet)
    found_files.append(fname)

if not collected:
    raise SystemExit("No candidate review files found in docs/. Expected files like final_review_remaining_*.csv or mapping_needs_review_*.csv")

allpairs = pd.concat(collected, ignore_index=True)


def dataset_from_fname(func_name):
    if 'enrol' in func_name.lower(): return 'enrolment'
    if 'demo' in func_name.lower(): return 'demographic'
    if 'bio' in func_name.lower(): return 'biometric'
    return 'other'

allpairs['dataset'] = allpairs['source_file'].map(dataset_from_fname)

grouped = allpairs.groupby(['state_norm','district_norm']).agg(
    count_rows = ('state_norm','size'),
).reset_index()


for ds in ['enrolment','demographic','biometric','other']:
    c = allpairs[allpairs['dataset']==ds].groupby(['state_norm','district_norm']).size().reset_index(name=f'{ds}_count')
    grouped = grouped.merge(c, on=['state_norm','district_norm'], how='left')


for col in ['enrolment_count','demographic_count','biometric_count','other_count']:
    if col not in grouped.columns:
        grouped[col] = 0
    grouped[col] = grouped[col].fillna(0).astype(int)

grouped['total_count'] = grouped[['enrolment_count','demographic_count','biometric_count','other_count']].sum(axis=1)


grouped[['suggested_state','state_match_score']] = grouped.apply(lambda r: best_state_match(r['state_norm']), axis=1, result_type='expand')
grouped['state_match_conf'] = grouped['state_match_score'].apply(lambda s: 'high' if s>=0.95 else ('medium' if s>=0.85 else 'low'))

output_val = grouped.sort_values('total_count', ascending=False).reset_index(drop=True)
TOP_N = 1000
output_val = output_val.head(TOP_N)


output_val = output_val.rename(columns={
    'state_norm':'original_state',
    'district_norm':'original_district',
    'count_rows':'count_rows'
})
output_val['canonical_state'] = output_val['suggested_state']
output_val['canonical_district'] = ''
cols = ['original_state','original_district','total_count','enrolment_count','demographic_count','biometric_count',
        'suggested_state','state_match_score','state_match_conf','canonical_state','canonical_district']
output_val[cols].to_csv(DOCS / "manual_review_suggestions.csv", index=False)
print("Wrote", DOCS / "manual_review_suggestions.csv", "— candidate files used:", found_files)