

import pandas as pd
from pathlib import Path
import re

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "outputs"
DOCS = PROJECT / "docs"

FILES = {
    "enrolment": OUT / "cleaned_enrolment_final_reverted.csv",
    "demographic": OUT / "cleaned_demographic_final_reverted.csv",
    "biometric": OUT / "cleaned_biometric_final_reverted.csv",
}

KEY_COLS = ["period","date","state","district","pincode"]
AGE_COLS_ENR = ["age_0_5","age_5_17","age_18_greater","enrol_age_5_17"]
AGE_COLS_DEM = ["demo_age_5_17","demo_age_17_"]
AGE_COLS_BIO = ["bio_age_5_17","bio_age_17_"]

DOCS.mkdir(parents=True, exist_ok=True)

def safe_read(file_handle):
    if not file_handle.exists():
        print(f"[MISSING] {fp}")
        return None

    sheet = pd.read_csv(file_handle, dtype=str, low_memory=False).fillna('')
    return sheet

reports = []


summary = []
for name, file_handle in FILES.entries():
    sheet = safe_read(file_handle)
    if sheet is None:
        summary.append((name, "MISSING", None))
        continue
    n = len(sheet)
    cols = list(sheet.columns)
    summary.append((name, n, cols))

    sheet.head(5).to_csv(DOCS / f"sample_head_{name}.csv", index=False)

pd.DataFrame(summary, columns=["dataset","nrows","columns_preview"]).to_csv(DOCS / "checks_summary_basic.csv", index=False)


cov_rows = []
for name, file_handle in FILES.entries():
    sheet = safe_read(file_handle)
    if sheet is None:
        continue

    if 'date' in sheet.columns:
        try:
            sheet['_date'] = pd.to_datetime(sheet['date'], errors='coerce', dayfirst=False)
        except Exception:
            sheet['_date'] = pd.to_datetime(sheet['date'], errors='coerce', dayfirst=True)
    elif 'period' in sheet.columns:
        sheet['_date'] = pd.to_datetime(sheet['period'], errors='coerce')
    else:
        sheet['_date'] = pd.NaT

    state_grp = sheet.groupby('state')['_date'].agg(['count','min','max']).reset_index()
    state_grp['days_span'] = (state_grp['max'] - state_grp['min']).dt.days.fillna(0).astype(int)
    state_grp['months_est'] = (state_grp['days_span'] / 30).round(1)
    state_grp.to_csv(DOCS / f"state_time_coverage_{name}.csv", index=False)
    cov_rows.append((name, state_grp.shape[0], state_grp['count'].sum()))

short_cov = []
for name, file_handle in FILES.entries():
    sheet = safe_read(file_handle)
    if sheet is None:
        continue
    if 'date' in sheet.columns:
        sheet['_date'] = pd.to_datetime(sheet['date'], errors='coerce', dayfirst=False)
    else:
        sheet['_date'] = pd.to_datetime(sheet['period'], errors='coerce')
    g = sheet.groupby('state')['_date'].agg(['min','max']).reset_index()
    g['months'] = ((g['max'] - g['min']).dt.days / 30).round(1)
    g['months'] = g['months'].fillna(0)
    short = g[g['months'] < 6].copy()
    short.to_csv(DOCS / f"short_coverage_states_{name}.csv", index=False)
    short_cov.append((name, len(short)))

for name, file_handle in FILES.entries():
    sheet = safe_read(file_handle)
    if sheet is None:
        continue
    keycols = [c for c in KEY_COLS if c in sheet.columns]
    if keycols:
        dup_key = sheet[sheet.duplicated(subset=keycols, keep=False)].sort_values(keycols)
        dup_key.to_csv(DOCS / f"duplicate_rows_by_key_{name}.csv", index=False)
    dup_all = sheet[sheet.duplicated(keep=False)].copy()
    dup_all.to_csv(DOCS / f"duplicate_rows_exact_{name}.csv", index=False)


missing_reports = []
for name, file_handle in FILES.entries():
    sheet = safe_read(file_handle)
    if sheet is None:
        continue
    for col in ['state','district','pincode','date']:
        if col in sheet.columns:
            n_miss = (sheet[col].astype(str).str.strip() == '').sum()
            missing_reports.append((name, col, int(n_miss), round(n_miss/len(sheet)*100,3)))
pd.DataFrame(missing_reports, columns=['dataset','column','missing_count','missing_pct']).to_csv(DOCS / "missing_critical_columns.csv", index=False)


pincode_reports = []
for name, file_handle in FILES.entries():
    sheet = safe_read(file_handle)
    if sheet is None:
        continue
    if 'pincode' in sheet.columns:
        bad = sheet[~sheet['pincode'].astype(str).str.fullmatch(r'\d{6}')]
        pincode_reports.append((name, len(bad)))
        bad.head(200).to_csv(DOCS / f"pincode_issues_{name}.csv", index=False)
pd.DataFrame(pincode_reports, columns=['dataset','bad_pincode_count']).to_csv(DOCS / "pincode_issues_summary.csv", index=False)


age_summary_rows = []

sheet = safe_read(FILES['enrolment'])
if sheet is not None:
    for c in AGE_COLS_ENR:
        if c in sheet.columns:
            s = pd.to_numeric(sheet[c].fillna('0'), errors='coerce').fillna(0)
            age_summary_rows.append(('enrolment', c, int(s.sum()), int((s==0).sum()), round((s==0).mean()*100,3)))

sheet = safe_read(FILES['demographic'])
if sheet is not None:
    for c in AGE_COLS_DEM:
        if c in sheet.columns:
            s = pd.to_numeric(sheet[c].fillna('0'), errors='coerce').fillna(0)
            age_summary_rows.append(('demographic', c, int(s.sum()), int((s==0).sum()), round((s==0).mean()*100,3)))

sheet = safe_read(FILES['biometric'])
if sheet is not None:
    for c in AGE_COLS_BIO:
        if c in sheet.columns:
            s = pd.to_numeric(sheet[c].fillna('0'), errors='coerce').fillna(0)
            age_summary_rows.append(('biometric', c, int(s.sum()), int((s==0).sum()), round((s==0).mean()*100,3)))
pd.DataFrame(age_summary_rows, columns=['dataset','age_col','sum_total','zero_count','zero_pct']).to_csv(DOCS / "age_distribution_summary.csv", index=False)


def state_totals(file_handle, age_cols):
    sheet = safe_read(file_handle)
    if sheet is None:
        return None

    present = [c for c in age_cols if c in sheet.columns]
    if not present:

        return None
    sheet[present] = sheet[present].apply(pd.to_numeric, errors='coerce').fillna(0)
    sheet['total_local'] = sheet[present].sum(axis=1)
    st = sheet.groupby('state')['total_local'].sum().reset_index().rename(columns={'total_local':'sum'})
    return st

st_en = state_totals(FILES['enrolment'], AGE_COLS_ENR)
st_de = state_totals(FILES['demographic'], AGE_COLS_DEM)
st_bi = state_totals(FILES['biometric'], AGE_COLS_BIO)
if st_en is not None:
    st_en.to_csv(DOCS / "state_totals_enrolment.csv", index=False)
if st_de is not None:
    st_de.to_csv(DOCS / "state_totals_demographic.csv", index=False)
if st_bi is not None:
    st_bi.to_csv(DOCS / "state_totals_biometric.csv", index=False)


if st_en is not None:
    small_states = st_en[st_en['sum'] < 100]
    small_states.to_csv(DOCS / "small_states_enrolment_under100.csv", index=False)


report_msg = []
report_msg.append("Quality checks written to docs/*.csv")
report_msg.append("Files checked and rows summary in docs/checks_summary_basic.csv")
print("\n".join(report_msg))