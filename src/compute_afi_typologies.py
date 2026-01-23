
"""
compute_afi_typologies.py

Purpose:
- Create AI-derived district typologies on top of AFI
- Fully unsupervised
- Policy-safe, explainable clustering
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score



INPUT_FILE = "outputs/afi_summary.csv"
OUT_WITH_TYPOS = "outputs/afi_with_typologies.csv"
OUT_CLUSTER_SUMMARY = "outputs/cluster_summary.csv"
OUT_CLUSTER_STABILITY = "outputs/cluster_stability.csv"

FEATURES = [
    "afi_composite_score",
    "bio_total",
    "demo_total",
    "aadhaar_base",
    "age_mismatch_score"
]

N_CLUSTERS = 5
RANDOM_STATE = 42



def log(msg):
    print(f"[INFO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}")

def safe_numeric(sheet, cols):
    for c in cols:
        sheet[c] = pd.to_numeric(sheet[c], errors="coerce")
        sheet[c] = sheet[c].replace([np.inf, -np.inf], np.nan)
        sheet[c] = sheet[c].fillna(0.0)
    return sheet



def main():
    log("Loading AFI summary")
    sheet = pd.read_csv(INPUT_FILE)
    log(f"Rows loaded: {len(df):,}")


    sheet = sheet[sheet["afi_composite_score"] > 0].copy()
    log(f"Rows with AFI > 0: {len(df):,}")


    sheet = safe_numeric(sheet, FEATURES)

    X = sheet[FEATURES].copy()

    log("Standardizing features")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    log("Running KMeans clustering")
    kmeans = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=20
    )
    sheet["cluster_id"] = kmeans.fit_predict(X_scaled)



    CLUSTER_NAMES = {
        0: "Stable & Low Friction",
        1: "High Biometric Friction",
        2: "Demographic Correction Heavy",
        3: "High Load Urban Pressure",
        4: "Structurally Stressed Districts"
    }

    sheet["cluster_name"] = sheet["cluster_id"].map(CLUSTER_NAMES)



    summary = (
        sheet.groupby(["cluster_id", "cluster_name"])
        .agg(
            districts=("district_clean", "nunique"),
            mean_afi=("afi_composite_score", "mean"),
            mean_bio=("bio_total", "mean"),
            mean_demo=("demo_total", "mean"),
            mean_base=("aadhaar_base", "mean"),
            mean_age_mismatch=("age_mismatch_score", "mean")
        )
        .reset_index()
        .sort_values("mean_afi", ascending=False)
    )

    summary.to_csv(OUT_CLUSTER_SUMMARY, index=False)
    log(f"Wrote cluster summary → {OUT_CLUSTER_SUMMARY}")



    log("Running cluster stability sanity-check")
    stability_rows = []

    for seed in [7, 21, 84]:
        km = KMeans(
            n_clusters=N_CLUSTERS,
            random_state=seed,
            n_init=10
        )
        labels_alt = km.fit_predict(X_scaled)
        ari = adjusted_rand_score(sheet["cluster_id"], labels_alt)
        stability_rows.append({
            "random_state": seed,
            "adjusted_rand_index": round(ari, 4)
        })

    stability = pd.DataFrame(stability_rows)
    stability.to_csv(OUT_CLUSTER_STABILITY, index=False)
    log(f"Wrote cluster stability → {OUT_CLUSTER_STABILITY}")



    sheet.to_csv(OUT_WITH_TYPOS, index=False)
    log(f"Wrote AFI with typologies → {OUT_WITH_TYPOS}")
    log("Done.")



if __name__ == "__main__":
    main()