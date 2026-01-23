
import pandas as pd
from pathlib import Path
from rapidfuzz import fuzz
import re

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"


SUSPICIOUS = {
    'enrolment': DOCS / "suspicious_suggestions_enrolment.csv",
    'demographic': DOCS / "suspicious_suggestions_demographic.csv",
    'biometric': DOCS / "suspicious_suggestions_biometric.csv"
}

OUT = DOCS / "suspicious_resolution_candidates.csv"


SIMILARITY_ACCEPT_IF_GE = 90
OVERLAP_ACCEPT_IF_GE = 0.7
SIMILARITY_REVIEW_IF_LT = 70


def normalize(s):
    if pd.isna(s) or s is None:
        return ''
    t = str(s).strip()
    t = re.sub(r'[\*\.\,\/\\\(\)\-]+', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def token_overlap(a, b):
    sa = set([w.lower() for w in re.split(r'\s+', a) if w])
    sb = set([w.lower() for w in re.split(r'\s+', b) if w])
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

rows_out = []
total = 0
total_accept = 0
total_review = 0

for ds, path in SUSPICIOUS.entries():
    if not path.exists():
        print("Missing", path)
        continue
    sheet = pd.read_csv(path, dtype=str).fillna('')
    for _, r in sheet.iterrows():
        total += 1
        orig_state = r.get('original_state','')
        orig_district = normalize(r.get('original_district',''))
        suggested = normalize(r.get('suggested_district','') or r.get('suggested_district',''))
        canonical = normalize(r.get('canonical_suggestion','') or r.get('canonical_suggestion',''))
        conf = r.get('suggestion_confidence','')

        ratio = fuzz.ratio(orig_district, canonical) if orig_district and canonical else 0
        overlap = token_overlap(orig_district, canonical)

        reason = []
        action = 'review'

        if canonical == '':
            reason.append('empty_canonical')
            action = 'review'
        else:

            if ratio >= SIMILARITY_ACCEPT_IF_GE:
                action = 'accept'
                reason.append(f'high_similarity({ratio})')
            elif overlap >= OVERLAP_ACCEPT_IF_GE and ratio >= 80:
                action = 'accept'
                reason.append(f'high_overlap({overlap:.2f})_ratio({ratio})')
            else:

                tokens_orig = set([w.lower() for w in re.split(r'\s+', orig_district) if w])
                tokens_can = set([w.lower() for w in re.split(r'\s+', canonical) if w])

                dir_tokens = {'east','west','north','south','central','upper','lower'}
                dirs_orig = tokens_orig & dir_tokens
                dirs_can = tokens_can & dir_tokens
                if dirs_orig and dirs_can and dirs_orig != dirs_can:
                    reason.append('direction_mismatch')
                    action = 'review'
                else:

                    if ratio < SIMILARITY_REVIEW_IF_LT or overlap < 0.3:
                        reason.append(f'low_similarity_or_overlap(ratio={ratio},overlap={overlap:.2f})')
                        action = 'review'
                    else:

                        action = 'accept'
                        reason.append(f'heuristic_accept(ratio={ratio},overlap={overlap:.2f})')
        if action == 'accept':
            total_accept += 1
        else:
            total_review += 1
        rows_out.append({
            'dataset': ds,
            'original_state': orig_state,
            'original_district': orig_district,
            'suggested_district': suggested,
            'canonical_suggestion': canonical,
            'suggestion_confidence': conf,
            'fuzzy_ratio': ratio,
            'token_overlap': round(overlap,3),
            'action': action,
            'reason': ';'.join(reason)
        })

out_df = pd.DataFrame(rows_out)
out_df.to_csv(OUT, index=False)
print(f"Wrote {OUT} rows: {len(out_df)}  accept:{total_accept}  review:{total_review}")
print("Open", OUT, "and inspect rows with action=='review' (small set).")