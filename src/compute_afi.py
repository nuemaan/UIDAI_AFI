
"""
compute_afi_fixed.py

Robust, fixed version of compute_afi.py that avoids the pandas fillna/None issue
and the deprecated applymap usage. It:
 - loads aggregated enrolment/demographic/biometric files
 - computes per-file totals safely
 - merges on group key (period, state_canonical, district_clean, pincode)
 - ensures numeric columns are numeric and NaNs are handled
 - outputs a merged CSV and a simple set of AFI-related summary columns

Adapt AFI computation block near the bottom to your official AFI formula if you
already have one. This script intentionally provides conservative placeholder
metrics that are common when computing coverage/consistency indices.

Usage:
    python compute_afi_fixed.py

Files expected (change constants below if you use different names):
  ./outputs/final_enrolment_for_afi.csv
  ./outputs/final_demographic_for_afi.csv
  ./outputs/final_biometric_for_afi.csv

Outputs (written to ./outputs):
  merged_for_afi.csv
  afi_summary.csv

"""

from __future__ import annotations

import sys
import math
from pathlib import Path
from datetime import datetime
import logging

import pandas as pd


BASE_DIR = Path.cwd()
INPUT_ENROL = BASE_DIR / "outputs" / "final_enrolment_for_afi.csv"
INPUT_DEMO = BASE_DIR / "outputs" / "final_demographic_for_afi.csv"
INPUT_BIO = BASE_DIR / "outputs" / "final_biometric_for_afi.csv"
OUT_MERGED = BASE_DIR / "outputs" / "merged_for_afi.csv"
OUT_SUMMARY = BASE_DIR / "outputs" / "afi_summary.csv"


GROUP_KEY = ["period", "state_canonical", "district_clean", "pincode"]


ENROL_AGE_COLS = ["age_0_5", "enrol_age_5_17", "enrol_age_18_greater"]
DEMO_AGE_COLS = ["demo_age_5_17", "demo_age_18_greater"]
BIO_AGE_COLS = ["bio_age_5_17", "bio_age_18_greater"]


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("compute_afi")


def safe_read_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        log.error("Missing input file: %s", path)
        raise SystemExit(1)
    log.info("Reading %s", path)
    return pd.read_csv(path, dtype=str, low_memory=False, **kwargs)


def to_numeric_sum(sheet: pd.DataFrame, cols: list[str], out_name: str) -> pd.Series:
    """Create a numeric series equal to sum of `cols` in df.

    Missing columns are treated as zeros. Non-numeric values coerced to NaN -> 0.0.
    """
    present = [c for c in cols if c in sheet.columns]
    if not present:

        log.warning("No columns of %s present in dataframe. Producing zeros for %s.", cols, out_name)
        return pd.Series([0.0] * len(sheet), index=sheet.index)


    num_df = pd.DataFrame({c: pd.to_numeric(sheet[c].fillna("0").replace("", "0"), errors="coerce").fillna(0.0)
                           for c in present})
    total = num_df.sum(axis=1).astype(float)
    return total


def ensure_group_columns(sheet: pd.DataFrame) -> pd.DataFrame:
    """Ensure group columns exist and are strings (no None)"""
    for col in GROUP_KEY:
        if col not in sheet.columns:
            sheet[col] = ""

        sheet[col] = sheet[col].fillna("").astype(str).str.strip()
    return sheet


def prepare_inputs():
    enrol = safe_read_csv(INPUT_ENROL)
    demo = safe_read_csv(INPUT_DEMO)
    bio = safe_read_csv(INPUT_BIO)


    enrol = ensure_group_columns(enrol)
    demo = ensure_group_columns(demo)
    bio = ensure_group_columns(bio)


    enrol['enrol_total'] = to_numeric_sum(enrol, ENROL_AGE_COLS, 'enrol_total')
    demo['demo_total'] = to_numeric_sum(demo, DEMO_AGE_COLS, 'demo_total')
    bio['bio_total'] = to_numeric_sum(bio, BIO_AGE_COLS, 'bio_total')


    enrol_keep = GROUP_KEY + ['enrol_total']
    demo_keep = GROUP_KEY + ['demo_total']
    bio_keep = GROUP_KEY + ['bio_total']

    enrol_small = enrol[enrol_keep].copy()
    demo_small = demo[demo_keep].copy()
    bio_small = bio[bio_keep].copy()


    enrol_small = enrol_small.drop_duplicates(subset=GROUP_KEY)
    demo_small = demo_small.drop_duplicates(subset=GROUP_KEY)
    bio_small = bio_small.drop_duplicates(subset=GROUP_KEY)

    log.info("Inputs prepared: enrol_rows=%d, demo_rows=%d, bio_rows=%d",
             len(enrol_small), len(demo_small), len(bio_small))

    return enrol_small, demo_small, bio_small


def merge_all(enrol_small: pd.DataFrame, demo_small: pd.DataFrame, bio_small: pd.DataFrame) -> pd.DataFrame:

    merged = enrol_small.merge(demo_small, on=GROUP_KEY, how='outer', validate='one_to_one')
    merged = merged.merge(bio_small, on=GROUP_KEY, how='outer', validate='one_to_one')


    merged = ensure_group_columns(merged)


    for col in ['enrol_total', 'demo_total', 'bio_total']:
        if col not in merged.columns:
            merged[col] = 0.0
        else:
            merged[col] = pd.to_numeric(merged[col].fillna(0).replace('', 0), errors='coerce').fillna(0.0).astype(float)

    return merged


def compute_afi_metrics(merged: pd.DataFrame) -> pd.DataFrame:
    """Compute AFI-related metrics. Replace or extend these with your official AFI formula.

    Current metrics (conservative placeholders):
      - demo_to_enrol_ratio = enrol_total / demo_total (coverage of enrolment data vs demographic)
      - bio_to_demo_ratio = bio_total / demo_total (biometric coverage vs demographic)
      - missing_demo = max(0, demo_total - (enrol_total + bio_total)) — how many demographic records not covered
      - afi_score (placeholder) = bio_to_demo_ratio * 100 (0-100% biometrics coverage)

    NOTE: avoid division by zero by using safe_div helper.
    """

    def safe_div(a, b):

        try:
            if pd.isna(b) or float(b) == 0.0:
                return 0.0
            return float(a) / float(b)
        except Exception:
            return 0.0

    merged = merged.copy()

    merged['demo_to_enrol_ratio'] = merged.apply(lambda r: safe_div(r['enrol_total'], r['demo_total']), axis=1)
    merged['bio_to_demo_ratio'] = merged.apply(lambda r: safe_div(r['bio_total'], r['demo_total']), axis=1)


    merged['missing_demo'] = (merged['demo_total'] - (merged['enrol_total'] + merged['bio_total'])).clip(lower=0.0)


    merged['afi_pct_bio_coverage'] = (merged['bio_to_demo_ratio'] * 100.0).round(4)



    merged['afi_composite_score'] = (0.7 * merged['bio_to_demo_ratio'] + 0.3 * merged['demo_to_enrol_ratio'])
    merged['afi_composite_score'] = (merged['afi_composite_score'] * 100.0).round(4)

    return merged


def write_outputs(merged: pd.DataFrame):
    OUT_MERGED.write_text('') if not OUT_MERGED.exists() else None
    log.info("Writing merged output to %s (rows=%d)", OUT_MERGED, len(merged))
    merged.to_csv(OUT_MERGED, index=False)


    cols_for_summary = GROUP_KEY + ['enrol_total', 'demo_total', 'bio_total',
                                    'demo_to_enrol_ratio', 'bio_to_demo_ratio',
                                    'missing_demo', 'afi_pct_bio_coverage', 'afi_composite_score']
    summary = merged[cols_for_summary].copy()
    log.info("Writing AFI summary to %s", OUT_SUMMARY)
    summary.to_csv(OUT_SUMMARY, index=False)


def main():
    log.info("Starting compute_afi_fixed.py")
    enrol_small, demo_small, bio_small = prepare_inputs()

    merged = merge_all(enrol_small, demo_small, bio_small)
    log.info("Merged rows: %d", len(merged))

    merged = compute_afi_metrics(merged)

    write_outputs(merged)
    log.info("Done. Outputs: %s, %s", OUT_MERGED, OUT_SUMMARY)


if __name__ == '__main__':
    main()