







import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime




ENROL_FILE = "outputs/final_enrolment_for_afi.csv"
DEMO_FILE  = "outputs/final_demographic_for_afi.csv"
BIO_FILE   = "outputs/final_biometric_for_afi.csv"

OUT_MERGED = "outputs/merged_for_afi.csv"
OUT_SUMMARY = "outputs/afi_summary.csv"
OUT_TOP = "outputs/top200_afi.csv"
OUT_BOTTOM = "outputs/bottom200_afi.csv"

GROUP_KEY = ["state_canonical", "district_clean", "pincode"]
TIME_COL = "period"

EPS = 1e-6





def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO] {ts} {msg}")


def safe_div(n, d):
    return n / (d + EPS)





def load_inputs():
    log("Loading inputs...")
    enrol = pd.read_csv(ENROL_FILE, low_memory=False)
    demo  = pd.read_csv(DEMO_FILE,  low_memory=False)
    bio   = pd.read_csv(BIO_FILE,   low_memory=False)

    for sheet in (enrol, demo, bio):
        sheet[TIME_COL] = pd.to_datetime(sheet[TIME_COL])

    return enrol, demo, bio





def compute_cumulative_base(sheet):
    """
    Cumulative Aadhaar base at district-pincode level.
    Approximated using cumulative enrolments over time.
    """
    sheet = sheet.sort_values(TIME_COL)
    sheet["aadhaar_base"] = (
        sheet.groupby(GROUP_KEY)["enrol_total"]
          .cumsum()
          .clip(lower=1)
    )
    return sheet


def compute_time_window_features(g):
    """
    Compute volatility and growth signals within a district.
    """
    g = g.sort_values(TIME_COL)

    for col in ["bio_total", "demo_total", "enrol_total"]:
        g[f"{col}_prev"] = g[col].shift(1).fillna(0)

    g["bio_volatility"]  = (g["bio_total"]  - g["bio_total_prev"]).abs()
    g["demo_volatility"] = (g["demo_total"] - g["demo_total_prev"]).abs()

    g["bio_growth_pct"] = safe_div(
        g["bio_total"] - g["bio_total_prev"],
        g["bio_total_prev"]
    ) * 100

    g["demo_growth_pct"] = safe_div(
        g["demo_total"] - g["demo_total_prev"],
        g["demo_total_prev"]
    ) * 100

    g["enrol_growth_pct"] = safe_div(
        g["enrol_total"] - g["enrol_total_prev"],
        g["enrol_total_prev"]
    ) * 100

    return g


def compute_age_transition_mismatch(sheet):
    """
    Policy proxy:
    If adult-age updates (biometric / demographic) rise sharply
    without corresponding adult enrolment transitions,
    it indicates repeated corrections rather than lifecycle change.
    """
    adult_updates = sheet["bio_age_18_greater"] + sheet["demo_age_18_greater"]
    adult_enrol   = sheet["enrol_age_18_greater"]

    sheet["age_mismatch_score"] = safe_div(
        adult_updates - adult_enrol,
        adult_enrol
    ).clip(lower=0)

    return sheet





def compute_afi(sheet):
    """
    AFI combines normalized stress signals.
    Weights are transparent and policy-interpretable.
    """

    sheet["bio_to_base"]  = safe_div(sheet["bio_total"],  sheet["aadhaar_base"])
    sheet["demo_to_enrol"] = safe_div(sheet["demo_total"], sheet["enrol_total"])


    def norm(s):
        return (s - s.min()) / (s.max() - s.min() + EPS)

    sheet["n_bio"]  = norm(sheet["bio_to_base"])
    sheet["n_demo"] = norm(sheet["demo_to_enrol"])
    sheet["n_vol"]  = norm(sheet["bio_volatility"] + sheet["demo_volatility"])
    sheet["n_age"]  = norm(sheet["age_mismatch_score"])


    sheet["afi_composite_score"] = (
        0.35 * sheet["n_bio"] +
        0.30 * sheet["n_demo"] +
        0.20 * sheet["n_vol"] +
        0.15 * sheet["n_age"]
    ) * 1000

    return sheet





def main():
    enrol, demo, bio = load_inputs()

    log("Merging datasets on ['period','state_canonical','district_clean','pincode'] (outer merge)")
    merged = (
        enrol
        .merge(demo, on=[TIME_COL, *GROUP_KEY], how="outer")
        .merge(bio,  on=[TIME_COL, *GROUP_KEY], how="outer")
    )


    num_cols = merged.select_dtypes(include="number").columns
    merged[num_cols] = merged[num_cols].fillna(0)

    log("Computing cumulative Aadhaar base")
    merged = compute_cumulative_base(merged)

    log("Computing time-window features")
    merged = (
        merged
        .groupby(GROUP_KEY, group_keys=False)
        .apply(compute_time_window_features)
    )

    log("Computing age-transition mismatch")
    merged = compute_age_transition_mismatch(merged)

    log("Computing AFI components")
    merged = compute_afi(merged)




    log(f"Writing merged output to {OUT_MERGED}")
    Path("outputs").mkdir(exist_ok=True)
    merged.to_csv(OUT_MERGED, index=False)

    afi_summary = merged.copy()
    afi_summary.to_csv(OUT_SUMMARY, index=False)

    merged.sort_values("afi_composite_score", ascending=False)\
          .head(200)\
          .to_csv(OUT_TOP, index=False)

    merged.sort_values("afi_composite_score", ascending=True)\
          .head(200)\
          .to_csv(OUT_BOTTOM, index=False)

    log("Done.")


if __name__ == "__main__":
    main()