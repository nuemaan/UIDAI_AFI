
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
OUT = PROJECT / "outputs"

APPLY_LEVELS = ['auto_high','auto_medium']

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
    sheet = pd.read_csv(path, dtype=str).fillna('')
    sheet = sheet[['original_state','original_district','canonical_state_suggestion','canonical_district_suggestion','suggestion_confidence']]
    sheet['key'] = list(zip(sheet['original_state'], sheet['original_district']))
    return sheet.set_index('key').to_dict('index')

def dry_run_for_dataset(ds):
    sug = load_suggestions(SUGGESTION_FILES[ds])
    merged = MERGED_FILES[ds]
    if not merged.exists():
        print("Missing merged file", merged)
        return

    uniq_pairs = set()
    chunks = pd.read_csv(merged, chunksize=500000, dtype=str, low_memory=False)
    for chunk in chunks:
        chunk = chunk.fillna('')
        uniq_pairs.update(set(zip(chunk['state'], chunk['district'])))

    to_apply_pairs = []
    for key in uniq_pairs:
        meta = sug.get(key)
        if meta and meta.get('suggestion_confidence') in APPLY_LEVELS and meta.get('canonical_state_suggestion'):
            to_apply_pairs.append((key, meta['suggestion_confidence'], meta['canonical_state_suggestion'], meta['canonical_district_suggestion']))
    print(f"\n{ds}: unique pairs in dataset: {len(uniq_pairs)}")
    print(f"Would auto-apply canonical mapping for {len(to_apply_pairs)} unique pairs (levels={APPLY_LEVELS})")
    print("Sample pairs that would be applied (up to 30):")
    for idx, t in enumerate(to_apply_pairs[:30]):
        key, conf, cs, cd = t
        print(f"{i+1:02d}. {key[0]}  /  {key[1]}  ->  {cs}  /  {cd}   (conf={conf})")
    return len(uniq_pairs), len(to_apply_pairs), to_apply_pairs

if __name__ == "__main__":
    for ds in ['enrolment','demographic','biometric']:
        dry_run_for_dataset(ds)
    print("\nDry-run complete. No files changed.")