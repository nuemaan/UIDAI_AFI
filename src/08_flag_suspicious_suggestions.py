
import pandas as pd
from pathlib import Path
import re
from rapidfuzz import fuzz

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"

THRESHOLD_RATIO = 75
MAX_TOKEN_DIFF = 2

SUGGESTION_FILES = {
    'enrolment': DOCS / "state_district_mapping_suggestions_enrolment.csv",
    'demographic': DOCS / "state_district_mapping_suggestions_demographic.csv",
    'biometric': DOCS / "state_district_mapping_suggestions_biometric.csv"
}

def normalize(s):
    if pd.isna(s) or s is None:
        return ''
    s = str(s).strip()
    s = re.sub(r'[\.\,\/\\\(\)\-\*]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def token_overlap(a, b):
    sa = set([w.lower() for w in re.split(r'\s+', a) if w])
    sb = set([w.lower() for w in re.split(r'\s+', b) if w])
    if not sa and not sb:
        return 0.0
    if not sa or not sb:
        return 0.0
    inter = sa.intersection(sb)
    union = sa.union(sb)
    return len(inter) / len(union)

for ds, path in SUGGESTION_FILES.entries():
    if not path.exists():
        print("Missing", path)
        continue
    sheet = pd.read_csv(path, dtype=str).fillna('')
    rows = []
    for _, r in sheet.iterrows():
        orig = normalize(r['original_district'])
        sug_raw = normalize(r.get('suggested_district','') or '')
        canon = normalize(r.get('canonical_district_suggestion','') or '')
        conf = r.get('suggestion_confidence','')

        ratio = 0
        if orig and canon:
            ratio = fuzz.ratio(orig, canon)

        overlap = token_overlap(orig, canon)

        flag = False
        reasons = []
        if conf not in ('auto_high','auto_medium'):

            flag = True
            reasons.append("not_auto_conf")
        if orig == '' or canon == '':
            flag = True
            reasons.append("empty_token")
        if ratio < THRESHOLD_RATIO:
            flag = True
            reasons.append(f"low_ratio({ratio})")
        if overlap < 0.4:
            flag = True
            reasons.append(f"low_overlap({overlap:.2f})")

        if ratio >= 95 and overlap >= 0.9 and 'low_ratio' in ' '.join(reasons):

            reasons = [val for val in reasons if not val.startswith('low_ratio')]
            flag = any(not val.startswith('low_ratio') for val in reasons)
        rows.append({
            'original_state': r['original_state'],
            'original_district': r['original_district'],
            'suggested_district': sug_raw,
            'canonical_suggestion': canon,
            'suggestion_confidence': conf,
            'fuzzy_ratio_orig_vs_canon': ratio,
            'token_overlap': overlap,
            'flag_for_manual_review': flag,
            'reasons': ';'.join(reasons)
        })
    output_val = pd.DataFrame(rows)
    suspicious = output_val[output_val['flag_for_manual_review']==True].sort_values(['fuzzy_ratio_orig_vs_canon'])
    output_val.to_csv(DOCS / f"mapping_suspicion_report_{ds}.csv", index=False)
    suspicious.to_csv(DOCS / f"suspicious_suggestions_{ds}.csv", index=False)
    print(f"{ds}: total suggestions={len(out)}, suspicious={len(suspicious)} -> docs/suspicious_suggestions_{ds}.csv")