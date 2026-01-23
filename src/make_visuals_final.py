import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
















INPUT_FILE = "outputs/merged_for_afi.csv"
OUT_DIR = "images_final"
os.makedirs(OUT_DIR, exist_ok=True)

sns.set(style="whitegrid", context="talk")




sheet = pd.read_csv(INPUT_FILE)


sheet = sheet.replace([np.inf, -np.inf], np.nan).dropna(subset=["afi_composite_score"])




def add_caption(fig, text):
    fig.text(
        0.5, -0.12, text,
        ha="center", va="top",
        fontsize=12, wrap=True
    )




fig, ax = plt.subplots(figsize=(14, 8))

afi = sheet["afi_composite_score"]
afi = afi[afi > 0]

ax.hist(afi, bins=80, log=True, color="#377eb8", alpha=0.85)

median = afi.median()
p95 = afi.quantile(0.95)
p99 = afi.quantile(0.99)

ax.axvline(median, color="black", linestyle="--", label=f"Median: {median:.1f}")
ax.axvline(p95, color="red", linestyle="--", label=f"95th percentile: {p95:.1f}")
ax.axvline(p99, color="darkred", linestyle="--", label=f"99th percentile: {p99:.1f}")

ax.set_xscale("log")
ax.set_xlabel("Aadhaar Friction Index (log scale)")
ax.set_ylabel("District–Month Count")
ax.set_title("Distribution of Aadhaar Friction Index Across India")
ax.legend()

add_caption(
    fig,
    "Most districts experience low Aadhaar friction, while a small number face extremely high friction. "
    "This long tail indicates that Aadhaar-related difficulties are highly localized rather than nationwide, "
    "supporting targeted district-level policy interventions instead of blanket reforms."
)

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/01_afi_distribution.png", dpi=200, bbox_inches="tight")
plt.close()




state_mean = (
    sheet.groupby("state_canonical")["afi_composite_score"]
    .mean()
    .sort_values(ascending=False)
)

top10 = state_mean.head(10)

fig, ax = plt.subplots(figsize=(14, 8))
top10[::-1].plot(kind="barh", ax=ax, color="#c0392b")

ax.set_xlabel("Mean Aadhaar Friction Index")
ax.set_ylabel("State")
ax.set_title("Top 10 States by Average Aadhaar Friction")

add_caption(
    fig,
    "States with higher average Aadhaar Friction Index values indicate greater difficulty faced by citizens "
    "in maintaining Aadhaar records. These states may require additional enrolment capacity, "
    "mobile biometric units, or administrative process improvements."
)

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/02_top10_states_high_friction.png", dpi=200, bbox_inches="tight")
plt.close()




bottom10 = state_mean.tail(10)

fig, ax = plt.subplots(figsize=(14, 8))
bottom10[::-1].plot(kind="barh", ax=ax, color="#27ae60")

ax.set_xlabel("Mean Aadhaar Friction Index")
ax.set_ylabel("State")
ax.set_title("Bottom 10 States by Average Aadhaar Friction")

add_caption(
    fig,
    "These states show consistently lower Aadhaar friction, suggesting smoother enrolment and update processes. "
    "They can serve as reference models or best-practice benchmarks for improving Aadhaar service delivery "
    "in higher-friction regions."
)

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/03_bottom10_states_low_friction.png", dpi=200, bbox_inches="tight")
plt.close()




top15 = sheet.sort_values("afi_composite_score", ascending=False).head(15)
labels = top15["district_clean"] + " — " + top15["state_canonical"]

fig, ax = plt.subplots(figsize=(14, 9))
ax.barh(labels[::-1], top15["afi_composite_score"][::-1], color="#34495e")

ax.set_xlabel("Aadhaar Friction Index")
ax.set_title("Top 15 Aadhaar Friction Hotspots (District–Month Level)")

add_caption(
    fig,
    "These district-month combinations represent extreme Aadhaar friction hotspots, often caused by "
    "temporary operational stress such as enrolment backlogs, biometric failures, or sudden update surges. "
    "AFI enables precise, time-bound interventions instead of reactive nationwide measures."
)

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/04_top15_district_hotspots.png", dpi=200, bbox_inches="tight")
plt.close()




if "age_mismatch_score" in sheet.columns:
    age_state = (
        sheet.groupby("state_canonical")["age_mismatch_score"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(14, 8))
    age_state[::-1].plot(kind="barh", ax=ax, color="#8e44ad")

    ax.set_xlabel("Age-Transition Mismatch Score")
    ax.set_ylabel("State")
    ax.set_title("States with Highest Aadhaar Age-Transition Mismatch")

    add_caption(
        fig,
        "Certain Aadhaar updates are mandatory at key age milestones. A high mismatch score indicates "
        "that expected updates are not occurring smoothly, suggesting access barriers for children "
        "and young adults. These states may benefit from school-based or mobile enrolment drives."
    )

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/05_age_transition_mismatch_states.png", dpi=200, bbox_inches="tight")
    plt.close()




if "aadhaar_base" in sheet.columns:
    fig, ax = plt.subplots(figsize=(14, 8))

    ax.scatter(
        sheet["aadhaar_base"],
        sheet["afi_composite_score"],
        alpha=0.15,
        s=15,
        color="#2980b9"
    )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Cumulative Aadhaar Base (log scale)")
    ax.set_ylabel("Aadhaar Friction Index (log scale)")
    ax.set_title("Aadhaar Friction Is Not Simply a Population Effect")

    add_caption(
        fig,
        "Districts with similar Aadhaar population sizes experience widely different friction levels. "
        "This confirms that Aadhaar Friction Index captures administrative and operational difficulty, "
        "not merely population scale."
    )

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/06_afi_vs_aadhaar_base.png", dpi=200, bbox_inches="tight")
    plt.close()

print(f"[DONE] Final submission-ready visuals written to {OUT_DIR}/")