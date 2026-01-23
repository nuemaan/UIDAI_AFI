
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
OUT = PROJECT / "outputs"


APPLY_LEVELS = ['auto_high']

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

def load_suggestions(path):
    if not path.exists():
        raise FileNotFoundError(path)
    sheet = pd.read_csv(path, dtype=str).fillna('')

    mapping = {}
    for _, r in sheet.iterrows():
        key = (r['original_state'], r['original_district'])
        mapping[key] = {
            'suggested_state': r.get('suggested_state',''),
            'suggested_district': r.get('suggested_district',''),
            'canonical_state_suggestion': r.get('canonical_state_suggestion',''),
            'canonical_district_suggestion': r.get('canonical_district_suggestion',''),
            'suggestion_confidence': r.get('suggestion_confidence',''),
            'notes': r.get('notes','')
        }
    return mapping, sheet

def apply_to_dataset(ds):
    sug_file = SUGGESTION_FILES[ds]
    merged_file = MERGED_FILES[ds]
    if not merged_file.exists():
        print("Missing merged file:", merged_file)
        return
    mapping, df_sugs = load_suggestions(sug_file)
    out_file = OUT / f"cleaned_{ds}_final.csv"
    review_rows = []
    applied_count = 0
    total_rows = 0


    chunks = pd.read_csv(merged_file, chunksize=500000, dtype=str, low_memory=False)
    first_write = True
    for chunk in chunks:
        chunk = chunk.fillna('')
        chunk['state_clean'] = chunk['state']
        chunk['district_clean'] = chunk['district']
        for idx, row in chunk.iterrows():
            key = (row['state'], row['district'])
            meta = mapping.get(key)
            if meta and meta['suggestion_confidence'] in APPLY_LEVELS and meta['canonical_state_suggestion']:
                chunk.at[idx,'state_clean'] = meta['canonical_state_suggestion']
                chunk.at[idx,'district_clean'] = meta['canonical_district_suggestion']
                applied_count += 1
            else:

                review_rows.append({
                    'original_state': row['state'],
                    'original_district': row['district'],
                    'suggested_state': meta['suggested_state'] if meta else '',
                    'suggested_district': meta['suggested_district'] if meta else '',
                    'canonical_suggestion': meta['canonical_district_suggestion'] if meta else '',
                    'suggestion_confidence': meta['suggestion_confidence'] if meta else '',
                    'notes': meta['notes'] if meta else ''
                })
            total_rows += 1

        if first_write:
            chunk.to_csv(out_file, index=False, mode='w')
            first_write = False
        else:
            chunk.to_csv(out_file, index=False, mode='a', header=False)

    review_df = pd.DataFrame(review_rows).drop_duplicates(subset=['original_state','original_district'])
    review_df.to_csv(DOCS / f"final_mapping_remaining_{ds}.csv", index=False)

    df_sugs.to_csv(DOCS / f"final_mapping_applied_{ds}.csv", index=False)
    print(f"{ds}: wrote cleaned file {out_file.name} (rows={total_rows}), applied_count={applied_count}, remaining_review={len(review_df)}")

if __name__ == "__main__":
    print("APPLY_LEVELS:", APPLY_LEVELS)
    for ds in ['enrolment','demographic','biometric']:
        apply_to_dataset(ds)
    print("Done. Check docs/final_mapping_remaining_*.csv for what to review manually.")