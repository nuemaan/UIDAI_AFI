
"""
compute_afi_advanced_fixed.py

Fixed version:
 - robust column name detection (handles suffixes like _bio, _x, etc.)
 - optional cumulative Aadhaar base denominator computed from enrolment time series
 - safer numeric coercion and period parsing
 - writes outputs to outputs/

Usage:
    python compute_afi_advanced_fixed.py

Config at top (toggle USE_CUMULATIVE_BASE)
"""
import os, sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA


INPUT_ENROL = "outputs/final_enrolment_for_afi.csv"
INPUT_DEMO  = "outputs/final_demographic_for_afi.csv"
INPUT_BIO   = "outputs/final_biometric_for_afi.csv"
OUT_DIR = Path("outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOOKBACK_MONTHS = 6
REPEAT_THRESHOLD = 10
EPS = 1e-9


W_BIO = 0.35
W_DEMO = 0.30
W_VOL = 0.20
W_MIS = 0.15

USE_PCA = False
USE_CUMULATIVE_BASE = True


def find_best_col(sheet, keywords_list):
    """
    Given df and list of keyword sets (list of lists), return the first column that matches all keywords in order of preference.
    keywords_list: e.g. [['bio','total'], ['bio_total']]
    """
    cols = sheet.columns.tolist()
    lc = [c.lower() for c in cols]
    for keywords in keywords_list:
        for idx, cname in enumerate(lc):
            if all(kdx.lower() in cname for kdx in keywords):
                return cols[idx]
    return None

def to_num_series(s):
    return pd.to_numeric(s.fillna(0).astype(str).str.replace(',',''), errors='coerce').fillna(0.0)

def robust_clip_scale(s, low_q=0.05, high_q=0.95):
    s = pd.Series(s).astype(float).fillna(0.0)
    lo = float(s.quantile(low_q))
    hi = float(s.quantile(high_q))
    if hi <= lo:
        lo, hi = float(s.min()), float(s.max() if s.max() != s.min() else s.min() + 1.0)
    clipped = s.clip(lower=lo, upper=hi)
    scaled = (clipped - lo) / (hi - lo)
    return scaled.fillna(0.0)


print("[INFO] Loading inputs...")
for p in (INPUT_ENROL, INPUT_DEMO, INPUT_BIO):
    if not Path(p).exists():
        print(f"[ERROR] Missing input file: {p}")
        sys.exit(1)

enrol = pd.read_csv(INPUT_ENROL, dtype=str, low_memory=False)
demo  = pd.read_csv(INPUT_DEMO, dtype=str, low_memory=False)
bio   = pd.read_csv(INPUT_BIO,  dtype=str, low_memory=False)


for sheet in (enrol, demo, bio):
    for kdx in ['period','state_canonical','district_clean','pincode']:
        if kdx in sheet.columns:
            sheet[kdx] = sheet[kdx].astype(str).fillna("").str.strip()
        else:
            sheet[kdx] = ""


print("[INFO] Merging datasets...")
merged = enrol.merge(demo, on=['period','state_canonical','district_clean','pincode'], how='outer', suffixes=('','_demo'))
merged = merged.merge(bio, on=['period','state_canonical','district_clean','pincode'], how='outer', suffixes=('','_bio'))

print(f"[INFO] Merged rows: {len(merged)}")


if 'period' in merged.columns:
    merged['period_dt'] = pd.to_datetime(merged['period'], errors='coerce')
else:
    merged['period_dt'] = pd.NaT


print("[INFO] Detecting numeric columns in merged dataframe...")

enrol_col = find_best_col(merged, [['enrol','total'], ['enrol_total'], ['enrol']])
demo_col  = find_best_col(merged, [['demo','total'], ['demo_total'], ['demographic','total']])
bio_col   = find_best_col(merged, [['bio','total'], ['bio_total'], ['biometric','total']])


enrol_age18_col = find_best_col(merged, [['enrol','age_18'], ['enrol_age_18_greater'], ['age_18_greater']])
bio_age18_col   = find_best_col(merged, [['bio','age_18'], ['bio_age_18_greater'], ['bio_age_18']])

print(f"[INFO] detected columns -> enrol: {enrol_col}, demo: {demo_col}, bio: {bio_col}")
print(f"[INFO] detected age18 -> enrol_age18: {enrol_age18_col}, bio_age18: {bio_age18_col}")

if enrol_col is None and demo_col is None and bio_col is None:
    print("[ERROR] Could not find any of enrol/demo/bio total columns in merged CSV. Columns present:")
    print(merged.columns.tolist())
    sys.exit(1)


merged['enrol_total'] = to_num_series(merged[enrol_col]) if enrol_col in merged.columns else 0.0
merged['demo_total']  = to_num_series(merged[demo_col]) if demo_col in merged.columns else 0.0
merged['bio_total']   = to_num_series(merged[bio_col])  if bio_col in merged.columns else 0.0

merged['enrol_age_18_greater'] = to_num_series(merged[enrol_age18_col]) if enrol_age18_col in merged.columns else 0.0
merged['bio_age_18_greater']   = to_num_series(merged[bio_age18_col])   if bio_age18_col in merged.columns else 0.0


if USE_CUMULATIVE_BASE:
    print("[INFO] Computing cumulative Aadhaar base from enrolment timeseries (per state/district/pincode)...")

    merged = merged.sort_values(['state_canonical','district_clean','pincode','period_dt']).reset_index(drop=True)

    merged['aadhaar_base_cum'] = merged.groupby(['state_canonical','district_clean','pincode'])['enrol_total'].cumsum().fillna(0.0)

    merged['aadhaar_base_cum'] = merged['aadhaar_base_cum'].clip(lower=0.0)
else:
    merged['aadhaar_base_cum'] = merged['enrol_total'].copy()


print("[INFO] Computing component signals...")
merged['bio_update_rate'] = merged['bio_total'] / (merged['aadhaar_base_cum'].replace({0:EPS}) + EPS)
merged['demo_to_enrol_ratio'] = merged['demo_total'] / (merged['enrol_total'].replace({0:EPS}) + EPS)
merged['bio_to_demo_ratio'] = merged['bio_total'] / (merged['demo_total'].replace({0:EPS}) + EPS)


merged = merged.sort_values(['state_canonical','district_clean','pincode','period_dt']).reset_index(drop=True)


def compute_window_features(g):
    bio_series = g['bio_total'].astype(float).fillna(0.0)
    g['bio_volatility_rolling'] = bio_series.rolling(window=LOOKBACK_MONTHS, min_periods=1).std().fillna(0.0)
    repeats = (bio_series > REPEAT_THRESHOLD).astype(float)
    g['repeat_density_rolling'] = repeats.rolling(window=LOOKBACK_MONTHS, min_periods=1).mean().fillna(0.0)
    return g

merged = merged.groupby(['state_canonical','district_clean','pincode'], group_keys=False).apply(compute_window_features).reset_index(drop=True)


merged['age_transition_mismatch'] = (merged['enrol_age_18_greater'] - merged['bio_age_18_greater']).abs() / (merged['enrol_age_18_greater'] + 1.0)


components = ['bio_update_rate','demo_to_enrol_ratio','bio_volatility_rolling','age_transition_mismatch']
for c in components:
    col_norm = c + "_norm"
    merged[col_norm] = robust_clip_scale(merged[c])

merged['repeat_density_norm'] = robust_clip_scale(merged['repeat_density_rolling'])


print("[INFO] Assembling AFI composite...")
if USE_PCA:
    X = merged[[c + "_norm" for c in components]].fillna(0.0).values
    pca = PCA(n_components=1)
    pc1 = pca.fit_transform(X).flatten()
    pc1 = pc1 - pc1.min()
    if pc1.max() > 0:
        pc1 = pc1 / pc1.max()
    merged['afi_score'] = pc1
else:
    wsum = W_BIO + W_DEMO + W_VOL + W_MIS
    ws = np.array([W_BIO, W_DEMO, W_VOL, W_MIS]) / (wsum if wsum>0 else 1.0)
    merged['afi_score'] = (
        ws[0]*merged['bio_update_rate_norm'] +
        ws[1]*merged['demo_to_enrol_ratio_norm'] +
        ws[2]*merged['bio_volatility_rolling_norm'] +
        ws[3]*merged['age_transition_mismatch_norm']
    )

merged['afi_with_repeat'] = 0.8*merged['afi_score'] + 0.2*merged['repeat_density_norm']


print("[INFO] Writing outputs...")
out_cols = [
    'period','state_canonical','district_clean','pincode',
    'enrol_total','demo_total','bio_total',
    'aadhaar_base_cum',
    'bio_update_rate','bio_update_rate_norm',
    'demo_to_enrol_ratio','demo_to_enrol_ratio_norm',
    'bio_volatility_rolling','bio_volatility_rolling_norm',
    'age_transition_mismatch','age_transition_mismatch_norm',
    'repeat_density_rolling','repeat_density_norm',
    'afi_score','afi_with_repeat'
]
present = [c for c in out_cols if c in merged.columns]
merged.loc[:, present].to_csv(OUT_DIR / "afi_district_month.csv", index=False)


state_month = merged.groupby(['period','state_canonical'], as_index=False).agg({
    'afi_score':'mean','afi_with_repeat':'mean',
    'enrol_total':'sum','demo_total':'sum','bio_total':'sum'
})
state_month.to_csv(OUT_DIR / "afi_state_month.csv", index=False)


periods = merged['period'].dropna().unique()
top_list = []
bot_list = []
for p in periods:
    sub = merged[merged['period'] == p]
    if len(sub) == 0: continue
    top_list.append(sub.sort_values('afi_score', ascending=False).head(200))
    bot_list.append(sub.sort_values('afi_score', ascending=True).head(200))
if top_list:
    pd.concat(top_list, ignore_index=True).to_csv(OUT_DIR / "top200_afi_by_period.csv", index=False)
if bot_list:
    pd.concat(bot_list, ignore_index=True).to_csv(OUT_DIR / "bottom200_afi_by_period.csv", index=False)

with open(OUT_DIR / "afi_diagnostics.txt", "w") as fh:
    fh.write("AFI diagnostics (fixed)\n")
    fh.write("========================\n")
    fh.write(f"Rows processed: {len(merged)}\n")
    fh.write(f"Detected enrol_col={enrol_col}, demo_col={demo_col}, bio_col={bio_col}\n")
    fh.write(f"USE_CUMULATIVE_BASE={USE_CUMULATIVE_BASE}\n\n")
    for c in components + ['repeat_density_rolling','aadhaar_base_cum']:
        if c in merged.columns:
            fh.write(f"{c}: min={merged[c].min():.3f} q05={merged[c].quantile(0.05):.3f} median={merged[c].median():.3f} mean={merged[c].mean():.3f} q95={merged[c].quantile(0.95):.3f} max={merged[c].max():.3f}\n")

print("[INFO] Done: outputs/afi_district_month.csv, outputs/afi_state_month.csv, outputs/top200_afi_by_period.csv, outputs/bottom200_afi_by_period.csv, outputs/afi_diagnostics.txt")