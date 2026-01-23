
import pandas as pd
from pathlib import Path
import re
from collections import Counter, defaultdict
from rapidfuzz import fuzz, process

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
OUT = PROJECT / "outputs"
DOCS.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)


DOMINANCE_THRESHOLD = 0.60
SIMILARITY_THRESHOLD = 85
MIN_CLUSTER_SIZE = 2

def normalize_text(s):
    if s is None:
        return ''
    s = str(s).strip()

    s = re.sub(r'[\.\,\/\\\(\)\-]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    s = s.strip()
    if s == '':
        return ''
    return s.lower()

def title_case_safe(s):

    if s is None or s == '':
        return ''
    s = s.strip()
    return ' '.join([w.capitalize() for w in s.split()])

def load_variants_map(file):
    sheet = pd.read_csv(file, dtype=str).fillna('')
    sheet['state_n'] = sheet['state'].apply(normalize_text)
    sheet['district_n'] = sheet['district'].apply(normalize_text)
    return sheet

def cluster_variants(variants):


    clusters = []
    used = set()
    for idx, v in enumerate(variants):
        if v in used:
            continue
        cluster = {v}
        used.add(v)

        for u in variants:
            if u in used:
                continue
            score = fuzz.ratio(v, u)
            if score >= SIMILARITY_THRESHOLD:
                cluster.add(u)
                used.add(u)
        clusters.append(sorted(cluster))

    for v in variants:
        if v not in used:
            clusters.append([v])
            used.add(v)
    return clusters

def auto_map(sheet):
    out_rows = []

    states = sheet['state_n'].unique().tolist()
    for s in sorted(states):
        sub = sheet[sheet['state_n'] == s]

        suggested_state = title_case_safe(s)


        districts = sub['district_n'].unique().tolist()
        if len(districts) == 0:
            continue
        if len(districts) < MIN_CLUSTER_SIZE:

            for _, row in sub.iterrows():
                out_rows.append({
                    'original_state': row['state'],
                    'original_district': row['district'],
                    'suggested_state': suggested_state,
                    'suggested_district': title_case_safe(row['district_n']),
                    'canonical_state': suggested_state,
                    'canonical_district': title_case_safe(row['district_n']),
                    'confidence': 'high',
                    'notes': ''
                })
            continue


        clusters = cluster_variants(districts)

        for cluster in clusters:


            counts = Counter(sub[sub['district_n'].isin(cluster)]['district_n'])
            total = sum(counts.values())

            top_norm, top_count = counts.most_common(1)[0]
            dominance = top_count / total if total>0 else 0

            original_candidates = sub[sub['district_n']==top_norm]['district'].values.tolist()

            selected_raw = Counter(original_candidates).most_common(1)[0][0]

            for _, row in sub[sub['district_n'].isin(cluster)].iterrows():
                confidence = 'low'
                notes = ''

                if len(cluster) == 1:
                    confidence = 'high'

                else:

                    min_pair = 100
                    for a in cluster:
                        for b in cluster:
                            if a == b: continue
                            min_pair = min(min_pair, fuzz.ratio(a,b))
                    if dominance >= DOMINANCE_THRESHOLD and min_pair >= SIMILARITY_THRESHOLD:
                        confidence = 'high'
                    elif dominance >= 0.45 and min_pair >= (SIMILARITY_THRESHOLD-10):
                        confidence = 'medium'
                    else:
                        confidence = 'low'
                        notes = f'cluster_variants={len(cluster)}; min_pair={min_pair}; dominance={dominance:.2f}'
                out_rows.append({
                    'original_state': row['state'],
                    'original_district': row['district'],
                    'suggested_state': suggested_state,
                    'suggested_district': title_case_safe(top_norm),
                    'canonical_state': suggested_state if confidence in ['high','medium'] else '',
                    'canonical_district': title_case_safe(selected_raw) if confidence in ['high','medium'] else '',
                    'confidence': confidence,
                    'notes': notes
                })
    out_df = pd.DataFrame(out_rows)

    out_df = out_df.drop_duplicates(subset=['original_state','original_district'])
    return out_df

if __name__ == "__main__":

    in_map = DOCS / "state_district_variants_enrolment.csv"
    if not in_map.exists():
        print("Error: expected", in_map)
        raise SystemExit(1)
    sheet = load_variants_map(in_map)
    output_val = auto_map(sheet)
    output_val.to_csv(DOCS / "state_district_mapping_auto_enrolment.csv", index=False)
    print("Wrote", DOCS / "state_district_mapping_auto_enrolment.csv", "rows:", len(output_val))

    print(output_val['confidence'].value_counts())