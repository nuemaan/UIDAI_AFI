
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
OUT = PROJECT / "outputs"

SUSPICIOUS = DOCS / "suspicious_resolution_candidates.csv"
SUGGESTION_FILES = {
    'enrolment': DOCS / "state_district_mapping_suggestions_enrolment.csv",
    'demographic': DOCS / "state_district_mapping_suggestions_demographic.csv",
    'biometric': DOCS / "state_district_mapping_suggestions_biometric.csv"
}
MERGED_FILES = {
    'enrolment': OUT / "merged_enrolment.csv",
    'demographic': OUT / "merged_demographic.csv",
    'biometric': OUT / "merged_biometric.csv"
}


print("Reading suspicious resolution candidates:", SUSPICIOUS)
sr = pd.read_csv(SUSPICIOUS, dtype=str).fillna('')
accepted = sr[sr['action']=='accept']
print("Total accepted suspicious rows:", len(accepted))


accepted_map = {}
for _, r in accepted.iterrows():
    key = (r['original_state'], r['original_district'])
    accepted_map[key] = {
        'canonical_state': r['canonical_suggestion'] if 'canonical_suggestion' in r else r.get('canonical_suggestion',''),

        'canonical_district': r['canonical_suggestion'] if 'canonical_suggestion' in r else r.get('canonical_suggestion',''),

    }


for ds, sugg_path in SUGGESTION_FILES.entries():
    print("Processing dataset:", ds)
    sug_df = pd.read_csv(sugg_path, dtype=str).fillna('')

    mapping = {}
    for _, r in sug_df.iterrows():
        key = (r['original_state'], r['original_district'])
        if key in accepted_map:
            mapping[key] = {
                'canonical_state': r.get('canonical_state_suggestion','') or r.get('canonical_state',''),
                'canonical_district': r.get('canonical_district_suggestion','') or r.get('canonical_district',''),
                'confidence': r.get('suggestion_confidence','')
            }
    print(f"  Accepted mapping entries to apply for {ds}: {len(mapping)}")


    merged_file = MERGED_FILES[ds]
    out_file = OUT / f"cleaned_{ds}_applied_accepts.csv"
    review_out = DOCS / f"final_review_remaining_{ds}.csv"
    applied_rows = 0
    total_rows = 0
    review_pairs = set()

    reader = pd.read_csv(merged_file, chunksize=500000, dtype=str, low_memory=False)
    first_write = True
    for chunk in reader:
        chunk = chunk.fillna('')
        chunk['state_clean'] = chunk['state']
        chunk['district_clean'] = chunk['district']
        for idx, row in chunk.iterrows():
            key = (row['state'], row['district'])
            if key in mapping:
                meta = mapping[key]
                if meta['canonical_state'] and meta['canonical_district']:
                    chunk.at[idx,'state_clean'] = meta['canonical_state']
                    chunk.at[idx,'district_clean'] = meta['canonical_district']
                    applied_rows += 1
                else:
                    review_pairs.add(key)
            else:
                review_pairs.add(key)
            total_rows += 1

        if first_write:
            chunk.to_csv(out_file, index=False, mode='w')
            first_write = False
        else:
            chunk.to_csv(out_file, index=False, mode='a', header=False)

    review_list = []
    for key in sorted(review_pairs):
        orig_state, orig_district = key

        match = sug_df[(sug_df['original_state']==orig_state) & (sug_df['original_district']==orig_district)]
        if not match.empty:
            r = match.iloc[0]
            review_list.append({
                'original_state': orig_state,
                'original_district': orig_district,
                'suggested_state': r.get('suggested_state',''),
                'suggested_district': r.get('suggested_district',''),
                'canonical_state_suggestion': r.get('canonical_state_suggestion',''),
                'canonical_district_suggestion': r.get('canonical_district_suggestion',''),
                'suggestion_confidence': r.get('suggestion_confidence',''),
                'notes': r.get('notes','')
            })
        else:
            review_list.append({
                'original_state': orig_state,
                'original_district': orig_district,
                'suggested_state': '',
                'suggested_district': '',
                'canonical_state_suggestion': '',
                'canonical_district_suggestion': '',
                'suggestion_confidence': '',
                'notes': ''
            })
    pd.DataFrame(review_list).drop_duplicates(subset=['original_state','original_district']).to_csv(review_out, index=False)
    print(f"  Wrote cleaned file: {out_file.name} (rows={total_rows}, applied={applied_rows}); review file: {review_out.name} (rows={len(review_list)})")

print("Done. Review the final_review_remaining_*.csv files in docs/ and paste a sample of review rows (I'll propose canonical names).")