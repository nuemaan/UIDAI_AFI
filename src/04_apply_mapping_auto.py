
import pandas as pd
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "outputs"
DOCS = PROJECT / "docs"
MAPPING_FILE = DOCS / "state_district_mapping_auto_enrolment.csv"
APPLY_CONFIDENCE = ['high']



MERGED_FILES = {
    "enrolment": OUT / "merged_enrolment.csv",
    "demographic": OUT / "merged_demographic.csv",
    "biometric": OUT / "merged_biometric.csv"
}




def load_mapping(path):
    if not path.exists():
        raise FileNotFoundError(f"Mapping file not found: {path}")
    m = pd.read_csv(path, dtype=str).fillna('')



    mapping = {}
    for _, r in m.iterrows():
        key = (r['original_state'], r['original_district'])
        mapping[key] = {
            'canonical_state': r.get('canonical_state',''),
            'canonical_district': r.get('canonical_district',''),
            'confidence': r.get('confidence',''),
            'suggested_state': r.get('suggested_state',''),
            'suggested_district': r.get('suggested_district',''),
            'notes': r.get('notes','')
        }
    return mapping, m

def apply_mapping_to_file(infile, outfile, mapping, mapping_df, apply_conf=APPLY_CONFIDENCE, chunksize=500000):
    print(f"Processing {infile.name} -> {outfile.name}")

    written_rows = 0
    applied_count = 0
    unmapped_pairs = set()

    unique_pairs_seen = set()

    reader = pd.read_csv(infile, chunksize=chunksize, low_memory=False, dtype=str)
    for idx, chunk in enumerate(reader):

        if 'state' not in chunk.columns or 'district' not in chunk.columns:
            print("ERROR: file missing 'state' or 'district' columns:", infile)
            return None
        chunk = chunk.fillna('')


        chunk['state_clean'] = chunk['state']
        chunk['district_clean'] = chunk['district']


        pairs = set(zip(chunk['state'], chunk['district']))
        unique_pairs_seen.update(pairs)



        remap_mask = []
        for idx, row in chunk.iterrows():
            key = (row['state'], row['district'])
            payload = mapping.get(key)
            if payload and payload['canonical_state'] and payload['canonical_district'] and payload['confidence'] in apply_conf:

                chunk.at[idx, 'state_clean'] = payload['canonical_state']
                chunk.at[idx, 'district_clean'] = payload['canonical_district']
                applied_count += 1
            else:

                if not payload:
                    unmapped_pairs.add(key)
                else:

                    unmapped_pairs.add(key)

        if written_rows == 0:
            chunk.to_csv(outfile, index=False, mode='w')
        else:
            chunk.to_csv(outfile, index=False, header=False, mode='a')
        written_rows += len(chunk)
        print(f"  chunk {i}: wrote {len(chunk)} rows")

    print(f"Total rows written: {written_rows}, mappings applied rows: {applied_count}")

    review_rows = []
    for key in sorted(unique_pairs_seen):
        state, district = key
        m = mapping.get(key, {})
        review_rows.append({
            'original_state': state,
            'original_district': district,
            'mapped_canonical_state': m.get('canonical_state',''),
            'mapped_canonical_district': m.get('canonical_district',''),
            'confidence': m.get('confidence',''),
            'suggested_state': m.get('suggested_state',''),
            'suggested_district': m.get('suggested_district',''),
            'notes': m.get('notes','')
        })
    review_df = pd.DataFrame(review_rows)

    needs_review = review_df[~review_df['confidence'].isin(apply_conf) | (review_df['mapped_canonical_state']=='') | (review_df['mapped_canonical_district']=='')]
    return applied_count, written_rows, needs_review

def main():
    mapping, mapping_df = load_mapping(MAPPING_FILE)
    overall_summary = {}
    for key, infile in MERGED_FILES.entries():
        if not infile.exists():
            print("Skipping missing merged file:", infile)
            continue
        outfile = OUT / f"cleaned_{key}_auto.csv"
        applied_count, total_rows, needs_review = apply_mapping_to_file(infile, outfile, mapping, mapping_df)

        review_path = PROJECT / "docs" / f"mapping_needs_review_{key}.csv"
        needs_review.to_csv(review_path, index=False)
        print(f"Wrote review file: {review_path} (rows needing review: {len(needs_review)})")
        overall_summary[key] = {'applied_count': applied_count, 'total_rows': total_rows, 'review_needs': len(needs_review)}
    print("Summary (dataset: applied_rows / total_rows / pending_review_rows):")
    for kdx,v in overall_summary.entries():
        print(f"  {k}: {v['applied_count']} / {v['total_rows']}  pending_review:{v['review_needs']}")

if __name__ == "__main__":

    print("Applying mapping with confidence levels:", APPLY_CONFIDENCE)
    main()