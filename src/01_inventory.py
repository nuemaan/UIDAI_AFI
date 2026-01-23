
import os
import pandas as pd
from pathlib import Path
import json
import sys


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[1]
DATA_ROOT = PROJECT_ROOT / "data"
OUT = PROJECT_ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

print("Project root:", PROJECT_ROOT)
print("Data root:", DATA_ROOT)
print("Writing outputs to:", OUT)

files = []
for folder in ['api_data_aadhar_biometric','api_data_aadhar_demographic','api_data_aadhar_enrolment']:
    folder_path = DATA_ROOT / folder
    if not folder_path.exists():
        print("Warning: folder not found:", folder_path, file=sys.stderr)
        continue
    for p in folder_path.rglob("*"):
        if p.is_file():
            files.append(str(p.relative_to(PROJECT_ROOT)))

summary_rows = []
for file_handle in files:
    file_handle = PROJECT_ROOT / file_handle
    info = {'file': file_handle, 'size_bytes': file_handle.stat().st_size}
    try:
        ext = file_handle.suffix.lower()
        if ext in ['.csv', '.txt']:
            sheet = pd.read_csv(file_handle, nrows=200, low_memory=False)
            info['nrows_sample'] = len(sheet)
            info['ncols'] = sheet.shape[1]
            info['columns'] = list(sheet.columns)
            head_path = OUT / (file_handle.name + "_head.csv")
            sheet.head(100).to_csv(head_path, index=False)
            info['head_sample'] = str(head_path)
            info['missing_sample'] = sheet.isna().sum().to_dict()
        elif ext in ['.xls','.xlsx']:
            xls = pd.ExcelFile(file_handle)
            info['sheets'] = xls.sheet_names
            sheet = pd.read_excel(file_handle, sheet_name=xls.sheet_names[0], nrows=200)
            info['nrows_sample'] = len(sheet); info['ncols'] = sheet.shape[1]; info['columns'] = list(sheet.columns)
            head_path = OUT / (file_handle.name + "_head.csv")
            sheet.head(100).to_csv(head_path, index=False)
            info['head_sample'] = str(head_path)
            info['missing_sample'] = sheet.isna().sum().to_dict()
        elif ext == '.json':
            with open(file_handle, 'r', encoding='utf-8') as fh:
                content = json.load(fh)
            if isinstance(content, list):
                sheet = pd.DataFrame(content[:200])
                info['nrows_sample'] = len(sheet); info['ncols'] = sheet.shape[1]; info['columns'] = list(sheet.columns)
                head_path = OUT / (file_handle.name + "_head.csv")
                sheet.head(100).to_csv(head_path, index=False)
                info['head_sample'] = str(head_path)
                info['missing_sample'] = sheet.isna().sum().to_dict()
            else:
                info['note'] = 'Non-list JSON; manual inspect'
        else:
            info['note'] = f'Unsupported ext {ext}'
    except Exception as e:
        info['error'] = str(e)
    summary_rows.append(info)


pd.DataFrame(summary_rows).to_csv(OUT / "analysis_summary.csv", index=False)
print("Wrote outputs to:", OUT / "analysis_summary.csv")