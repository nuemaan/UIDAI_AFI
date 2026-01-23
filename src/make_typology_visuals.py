
"""
make_typology_visuals.py

Final judge-ready typology visualisations for AFI.
Outputs are written to ./typology_visuals/

Figures are:
1. Typology size (count of district-months)
2. AFI distribution by typology (log-scale boxplot)
3. State × Typology composition for high-volume states

All figures:
- High DPI (PDF-ready)
- Clear labels
- Embedded captions
"""

import os
import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns



INPUT_FILE = "outputs/afi_with_typologies.csv"
OUT_DIR = "typology_visuals"
DPI = 300

os.makedirs(OUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.2)



def save_fig(fig, filename):
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(os.path.join(OUT_DIR, filename), dpi=DPI)
    plt.close(fig)

def wrap_xticks(ax, width=18, rotation=20):
    labels = [t.get_text() for t in ax.get_xticklabels()]
    wrapped = ["\n".join(textwrap.wrap(l, width)) for l in labels]
    ax.set_xticklabels(wrapped, rotation=rotation, ha="right")

def add_caption(fig, text):
    fig.text(
        0.5, 0.01,
        text,
        ha="center",
        va="bottom",
        fontsize=10,
        style="italic"
    )



print("[INFO] Loading AFI typology data")
sheet = pd.read_csv(INPUT_FILE)

required_cols = {
    "cluster_id",
    "cluster_name",
    "afi_composite_score",
    "state_canonical"
}

missing = required_cols - set(sheet.columns)
if missing:
    raise ValueError(f"Missing required columns: {missing}")



print("[INFO] Plotting typology size")

counts = (
    sheet["cluster_name"]
    .value_counts()
    .rename_axis("cluster_name")
    .reset_index(name="district_months")
)

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(
    payload=counts,
    val="cluster_name",
    val2="district_months",
    ax=ax,
    color="#4C72B0"
)

ax.set_title("District Typologies by Observed Aadhaar Behaviour", fontsize=16)
ax.set_xlabel("District Typology")
ax.set_ylabel("Number of District-Month Observations")

wrap_xticks(ax)

add_caption(
    fig,
    "Each typology groups districts with similar Aadhaar enrolment and update behaviour. "
    "Larger bars indicate patterns that are widespread across India."
)

save_fig(fig, "01_typology_size.png")



print("[INFO] Plotting AFI distribution by typology")

fig, ax = plt.subplots(figsize=(11, 6))
sns.boxplot(
    payload=sheet,
    val="cluster_name",
    val2="afi_composite_score",
    showfliers=False,
    ax=ax
)

ax.set_yscale("log")
ax.set_title("Aadhaar Friction Index Distribution by District Typology", fontsize=16)
ax.set_xlabel("District Typology")
ax.set_ylabel("AFI (log scale)")

wrap_xticks(ax)

add_caption(
    fig,
    "Higher AFI values indicate greater citizen difficulty in maintaining Aadhaar. "
    "Distinct distributions confirm that typologies capture real operational differences."
)

save_fig(fig, "02_typology_afi_distribution.png")



print("[INFO] Plotting state-typology composition")

top_states = (
    sheet["state_canonical"]
    .value_counts()
    .head(10)
    .index
)

mix = (
    sheet[sheet["state_canonical"].isin(top_states)]
    .groupby(["state_canonical", "cluster_name"])
    .size()
    .reset_index(name="count")
)

fig, ax = plt.subplots(figsize=(12, 7))
sns.barplot(
    payload=mix,
    val="state_canonical",
    val2="count",
    hue="cluster_name",
    ax=ax
)

ax.set_title("Typology Composition of High-Volume States", fontsize=16)
ax.set_xlabel("State")
ax.set_ylabel("District-Month Observations")

wrap_xticks(ax, width=14, rotation=25)

ax.legend(
    title="District Typology",
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

add_caption(
    fig,
    "States show distinct mixes of district typologies. "
    "This enables state-specific, targeted Aadhaar policy interventions."
)

save_fig(fig, "03_state_typology_mix.png")

print("[DONE] Typology visuals written to:", OUT_DIR)