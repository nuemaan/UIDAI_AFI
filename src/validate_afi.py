
"""
validate_afi.py

Safe validation for AFI outputs.
Never crashes on inf / NaN.
"""

import pandas as pd
import numpy as np

MERGED_FP = "outputs/merged_for_afi.csv"
AFI_FP = "outputs/afi_summary.csv"


def quick_stats(sheet, name):
    print(f"\n--- {name} ---")
    print(f"rows: {len(df)}")

    for c in ["enrol_total", "demo_total", "bio_total", "afi_composite_score"]:
        if c not in sheet.columns:
            continue

        s = pd.to_numeric(sheet[c], errors="coerce")

        inf_count = np.isinf(s).sum()
        nan_count = s.isna().sum()

        s_clean = s.replace([np.inf, -np.inf], np.nan)

        print(
            f"{c}: "
            f"sum={s_clean.sum():,.3f}, "
            f"mean={s_clean.mean():.3f}, "
            f"median={s_clean.median():.3f}, "
            f"zeros={(s_clean == 0).sum()}, "
            f"inf={inf_count}, "
            f"nan={nan_count}"
        )


def main():
    print("Loading merged_for_afi ...")
    merged = pd.read_csv(MERGED_FP, low_memory=False)
    quick_stats(merged, "merged_for_afi")

    print("\nUnique states:", sorted(merged["state_canonical"].dropna().unique().tolist()))
    print("UNKNOWN/100000 count:", (merged["pincode"] == "100000").sum())

    print("\nLoading afi_summary ...")
    afi = pd.read_csv(AFI_FP, low_memory=False)
    quick_stats(afi, "afi_summary")

    if "afi_composite_score" in afi.columns:
        p = afi["afi_composite_score"].replace([np.inf, -np.inf], np.nan)
        print(
            "\nAFI percentiles:",
            {
                q: float(p.quantile(q))
                for q in [0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0]
            }
        )


if __name__ == "__main__":
    main()