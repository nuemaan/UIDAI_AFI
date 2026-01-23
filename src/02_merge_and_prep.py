
import pandas as pd
from pathlib import Path
import re

PROJECT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT / "data"
OUT = PROJECT / "outputs"
DOCS = PROJECT / "docs"
OUT.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)

def list_csvs(folder):
    p = DATA_ROOT / folder
    return sorted([val for val in p.glob("*.csv")])

def safe_read_csv(file_handle):

    return pd.read_csv(file_handle, low_memory=False)

def normalize_pincode(s):
    if pd.isna(s):
        return None
    s = str(s).strip()

    digits = re.sub(r'\D', '', s)
    if digits == '':
        return None

    if len(digits) > 6:
        digits = digits[-6:]
    return digits.zfill(6)

def standardize_age_cols(sheet, dataset_tag):
    cols = list(sheet.columns)
    colmap = {}



    for c in cols:
        lc = c.lower().replace(" ", "").replace("-", "_")
        if re.search(r'(^|_)age_0[_-]?5|0[_-]?5', lc) or 'age_0_5' in lc:
            colmap[c] = 'age_0_5'
        elif re.search(r'age[_]?5[_-]?17|5[_-]?17', lc) or '5_17' in lc:

            colmap[c] = f'{dataset_tag}_age_5_17' if not c.startswith(dataset_tag) else c
        elif re.search(r'age[_]?(17|18)|17_', lc) or '18' in lc or 'greater' in lc or 'gt' in lc:
            colmap[c] = f'{dataset_tag}_age_18_greater'
    return sheet.rename(columns=colmap), colmap

def process_folder(folder, dataset_tag):
    csvs = list_csvs(folder)
    print(f"Found {len(csvs)} csv files in {folder}")
    dfs = []
    for file_handle in csvs:
        print("Reading", file_handle.name)
        sheet = safe_read_csv(file_handle)
        sheet, colmap = standardize_age_cols(sheet, dataset_tag)

        if 'date' not in sheet.columns:
            print("WARNING: 'date' not in", file_handle.name)
        if 'state' not in sheet.columns:
            print("WARNING: 'state' not in", file_handle.name)

        if 'pincode' in sheet.columns:
            sheet['pincode'] = sheet['pincode'].apply(normalize_pincode)
        else:
            sheet['pincode'] = None

        if 'date' in sheet.columns:
            sheet['date'] = pd.to_datetime(sheet['date'], errors='coerce')

            sheet['period'] = sheet['date'].dt.to_period('M').dt.to_timestamp()
        else:
            sheet['period'] = pd.NaT
        dfs.append(sheet)
    if not dfs:
        return None
    merged = pd.concat(dfs, ignore_index=True, sort=False)


    core = ['period','date','state','district','pincode']
    other = [c for c in merged.columns if c not in core]
    merged = merged[ [c for c in core if c in merged.columns] + other ]
    return merged


bio = process_folder('api_data_aadhar_biometric', 'bio')
if bio is not None:
    bio.to_csv(OUT / "merged_biometric.csv", index=False)
    bio.head(200).to_csv(OUT / "merged_biometric_head.csv", index=False)

    sd = bio[['state','district']].drop_duplicates().sort_values(['state','district']).reset_index(drop=True)
    sd.to_csv(DOCS / "state_district_variants_biometric.csv", index=False)


demo = process_folder('api_data_aadhar_demographic', 'demo')
if demo is not None:
    demo.to_csv(OUT / "merged_demographic.csv", index=False)
    demo.head(200).to_csv(OUT / "merged_demographic_head.csv", index=False)
    sd = demo[['state','district']].drop_duplicates().sort_values(['state','district']).reset_index(drop=True)
    sd.to_csv(DOCS / "state_district_variants_demographic.csv", index=False)


enr = process_folder('api_data_aadhar_enrolment', 'enrol')
if enr is not None:
    enr.to_csv(OUT / "merged_enrolment.csv", index=False)
    enr.head(200).to_csv(OUT / "merged_enrolment_head.csv", index=False)
    sd = enr[['state','district']].drop_duplicates().sort_values(['state','district']).reset_index(drop=True)
    sd.to_csv(DOCS / "state_district_variants_enrolment.csv", index=False)

print("Merged files written to outputs/ and state/district variants to docs/")