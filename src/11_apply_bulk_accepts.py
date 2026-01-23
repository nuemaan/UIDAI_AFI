
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
OUT = PROJECT / "outputs"
DATA_FALLBACK = Path("/mnt/data")

SUG_FILES = {
    'enrolment': DOCS / "state_district_bulk_suggestions_enrolment.csv",
    'demographic': DOCS / "state_district_bulk_suggestions_demographic.csv",
    'biometric': DOCS / "state_district_bulk_suggestions_biometric.csv"
}

MERGED_FILES = {
    'enrolment': OUT / "merged_enrolment.csv",
    'demographic': OUT / "merged_demographic.csv",
    'biometric': OUT / "merged_biometric.csv"
}

def load_bulk_suggestions(path):
    if path.exists():
        return pd.read_csv(path, dtype=str).fillna('')

    alt = DATA_FALLBACK / path.name
    if alt.exists():
        return pd.read_csv(alt, dtype=str).fillna('')
    raise FileNotFoundError(f"Suggestion file not found in docs/ or /mnt/data/: {path.name}")

def build_accept_map(sheet):

    mapping = {}
    for _, r in sheet.iterrows():
        if str(r.get('action','')).lower() == 'auto_accept':
            key = (r.get('original_state',''), r.get('original_district',''))
            mapping[key] = {
                'canonical_state': r.get('proposed_canonical_state','') or r.get('proposed_canonical_district',''),
                'canonical_district': r.get('proposed_canonical_district','') or r.get('proposed_canonical_state','')
            }
    return mapping

def apply_mapping(merged_fp, out_fp, mapping):
    print(f"Applying mapping to {merged_fp.name} -> {out_fp.name}")
    reader = pd.read_csv(merged_fp, chunksize=500000, dtype=str, low_memory=False)
    written = 0
    applied_rows = 0
    review_pairs = set()
    first = True
    for chunk in reader:
        chunk = chunk.fillna('')
        chunk['state_clean'] = chunk['state']
        chunk['district_clean'] = chunk['district']
        for idx, row in chunk.iterrows():
            key = (row['state'], row['district'])
            meta = mapping.get(key)
            if meta and meta['canonical_state'] and meta['canonical_district']:
                chunk.at[idx, 'state_clean'] = meta['canonical_state']
                chunk.at[idx, 'district_clean'] = meta['canonical_district']
                applied_rows += 1
            else:
                review_pairs.add(key)
        if first:
            chunk.to_csv(out_fp, index=False, mode='w')
            first = False
        else:
            chunk.to_csv(out_fp, index=False, mode='a', header=False)
        written += len(chunk)
        print(f"  wrote chunk, total rows so far: {written}")

    review_rows = []
    for key in sorted(review_pairs):
        s,d = key
        review_rows.append({'original_state': s, 'original_district': d})
    review_df = pd.DataFrame(review_rows)
    return written, applied_rows, review_df

if __name__ == "__main__":
    summary = {}
    for ds, sug_fp in SUG_FILES.entries():
        try:
            sug_df = load_bulk_suggestions(sug_fp)
        except FileNotFoundError as e:
            print("Skipping", ds, ":", e)
            continue


        if 'proposed_canonical_district' not in sug_df.columns and 'canonical_district_suggestion' in sug_df.columns:
            sug_df = sug_df.rename(columns={'canonical_district_suggestion':'proposed_canonical_district',
                                            'canonical_state_suggestion':'proposed_canonical_state'})
        if 'action' not in sug_df.columns:

            if 'suggestion_confidence' in sug_df.columns:
                sug_df['action'] = sug_df['suggestion_confidence'].apply(lambda val: 'auto_accept' if str(val).startswith('auto') else 'manual_review')
            else:
                sug_df['action'] = 'manual_review'
        mapping = build_accept_map(sug_df)
        print(f"{ds}: loaded {len(sug_df)} suggestions, auto_accept entries: {len(mapping)}")
        merged_fp = MERGED_FILES[ds]
        out_fp = OUT / f"cleaned_{ds}_applied_autoaccepts.csv"
        written, applied_rows, review_df = apply_mapping(merged_fp, out_fp, mapping)
        review_out = DOCS / f"final_review_remaining_{ds}.csv"
        review_df.to_csv(review_out, index=False)
        summary[ds] = {'rows_written': written, 'applied_rows': applied_rows, 'remaining_review_rows': len(review_df)}
        print(f"{ds} done: applied {applied_rows} rows; remaining unique pairs to review: {len(review_df)}")
    print("\nSUMMARY:")
    for kdx,v in summary.entries():
        print(f" {k}: written={v['rows_written']}, applied={v['applied_rows']}, remaining_review_pairs={v['remaining_review_rows']}")