
"""
Read mapping_needs_review_<dataset>.csv for enrolment/demographic/biometric,
produce conservative auto-suggestions for canonical_state/canonical_district
and write docs/state_district_mapping_suggestions_<dataset>.csv

Rules used (conservative):
- canonical_state := Title-case(suggested_state) if not empty
- canonical_district := most common raw spelling for the normalized suggested_district
- Clean tokens: replace '&' with 'And', remove repeated spaces/punct, zstrip
- If the mapping row originally had a confidence (from auto_map), preserve it,
  and produce suggestion_confidence:
    - auto_high: suggested canonical chosen and appears to match existing patterns
    - auto_medium: cleaned suggestion used but low dominance
    - manual: ambiguous (leave blank canonical and note)
"""
from pathlib import Path
import pandas as pd
import re
from collections import Counter, defaultdict

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
OUT = PROJECT / "outputs"

def clean_token(s):
    if pd.isna(s) or s is None:
        return ''
    t = str(s).strip()

    t = re.sub(r'[\.\,\/\\\(\)\-]+', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    t = t.strip()

    t = t.replace('&', 'and')
    return t

def title_case(s):
    if not s:
        return ''
    return ' '.join([w.capitalize() for w in s.split()])

def suggest_for_dataset(dataset):
    in_path = DOCS / f"mapping_needs_review_{dataset}.csv"
    out_path = DOCS / f"state_district_mapping_suggestions_{dataset}.csv"
    if not in_path.exists():
        print("Missing:", in_path)
        return
    sheet = pd.read_csv(in_path, dtype=str).fillna('')

    group = defaultdict(list)
    for _, row in sheet.iterrows():
        key = clean_token(row.get('suggested_district','') or row.get('original_district',''))
        group[key].append(row.get('original_district',''))

    canonical_map = {}
    dominance_map = {}
    for kdx, vals in group.entries():
        if kdx == '':
            canonical_map[kdx] = ''
            dominance_map[kdx] = 0.0
            continue
        c = Counter(vals)
        most_common_raw, count = c.most_common(1)[0]
        dominance = count / sum(c.values())
        canonical_map[kdx] = most_common_raw.strip()
        dominance_map[kdx] = dominance


    sug_rows = []
    for _, row in sheet.iterrows():
        orig_state = row.get('original_state','')
        orig_district = row.get('original_district','')
        sug_state = row.get('suggested_state','') or ''
        sug_district = row.get('suggested_district','') or ''
        norm_d = clean_token(sug_district or orig_district)
        suggested_state_clean = title_case(clean_token(sug_state)) if sug_state else title_case(clean_token(orig_state))

        cand = canonical_map.get(norm_d, '')
        dominance = dominance_map.get(norm_d, 0.0)

        if cand and dominance >= 0.6:
            suggestion_confidence = 'auto_high'
            canonical_state = suggested_state_clean
            canonical_district = cand
        elif cand and dominance >= 0.35:
            suggestion_confidence = 'auto_medium'
            canonical_state = suggested_state_clean
            canonical_district = cand
        else:

            if norm_d:
                canonical_state = suggested_state_clean
                canonical_district = title_case(norm_d)
                suggestion_confidence = 'auto_medium' if norm_d else 'manual'
            else:
                canonical_state = ''
                canonical_district = ''
                suggestion_confidence = 'manual'
        sug_rows.append({
            'original_state': orig_state,
            'original_district': orig_district,
            'suggested_state': sug_state,
            'suggested_district': sug_district,
            'canonical_state_suggestion': canonical_state,
            'canonical_district_suggestion': canonical_district,
            'suggestion_confidence': suggestion_confidence,
            'notes': row.get('notes','')
        })
    out_df = pd.DataFrame(sug_rows)
    out_df = out_df.drop_duplicates(subset=['original_state','original_district'])
    out_df.to_csv(out_path, index=False)
    print("Wrote", out_path, "rows:", len(out_df))
    print("Confidence counts:")
    print(out_df['suggestion_confidence'].value_counts())

if __name__ == "__main__":
    for ds in ['enrolment','demographic','biometric']:
        suggest_for_dataset(ds)
    print("Done. Open docs/state_district_mapping_suggestions_<dataset>.csv and review.")