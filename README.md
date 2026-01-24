Aadhaar Friction Index (AFI)

Measuring Citizen Difficulty in Aadhaar Enrolment & Updates Using Public Data and Interpretable AI

⸻

Overview

India’s Aadhaar system generates large volumes of enrolment and update data every month. While aggregate counts are publicly available, there is no standard, district-level way to quantify how difficult it is for citizens to enrol or maintain their Aadhaar details.

This repository introduces the Aadhaar Friction Index (AFI) — a reproducible, data-driven framework that converts anonymized UIDAI enrolment and update datasets into a district-month level measure of citizen friction.

AFI does not predict individuals and does not use personal data. Instead, it uses aggregated public data to surface systemic operational stress, enabling evidence-based governance, research, and accountability.

⸻

What Problem Does AFI Solve?

Current Aadhaar data answers “how many” enrolments or updates occurred.
AFI answers “where citizens are facing disproportionate difficulty — and why.”

Without AFI:
	•	Operational bottlenecks remain hidden inside raw volumes
	•	Policy responses are reactive rather than targeted
	•	Researchers and journalists lack a standardized metric for comparison

AFI fills this gap by transforming UIDAI data into:
	•	A single interpretable friction score
	•	District typologies based on observed behaviour
	•	Early-warning signals for rising administrative stress

⸻

Core Outputs

This project produces:
	1.	Aadhaar Friction Index (AFI)
A composite score capturing enrolment pressure, update intensity, biometric stress, volatility, and age-transition mismatch — normalized against the cumulative Aadhaar base.
	2.	District Typologies (Unsupervised AI)
Districts are grouped using clustering into practical, interpretable categories:
	•	Stable & Low Friction
	•	High Biometric Friction
	•	High Load Urban Pressure
	•	Structurally Stressed Districts
	•	Demographic Correction Heavy
	3.	Interactive Dashboard (Prototype)
Visualizes national, state, and district-level patterns with filters and comparisons.
	4.	Reproducible Analysis Pipeline
Clean, modular Python scripts covering data cleaning, feature engineering, validation, clustering, and visualization.

⸻

Data Sources

All data used is public, anonymized, and aggregated.

UIDAI Aadhaar Enrolment Dataset

. Source: UIDAI / data.gov.in
. Content: Monthly enrolments by state, district, pincode, age group

UIDAI Aadhaar Update Dataset (Demographic & Biometric)

. Source: UIDAI / data.gov.in
. Content: Monthly updates by geography and age group

No scraped, personal, or proprietary data is used.

⸻

Methodology (High Level)
	1.	Data Cleaning & Standardisation
	•	Canonical state and district names
	•	Consistent monthly time indices
	•	Safe handling of zeros, missing values, and outliers
	2.	Feature Engineering
	•	Enrolment, demographic update, and biometric update intensities
	•	Volatility and growth measures
	•	Age-transition mismatch (expected vs observed updates)
	•	Normalisation by cumulative Aadhaar base
	3.	AFI Construction
	•	Weighted, interpretable combination of operational signals
	•	Designed to reflect friction, not population size
	4.	Unsupervised AI (Clustering)
	•	Standardised features
	•	Stability-checked clustering
	•	Human-interpretable typology labels based on observed patterns
	5.	Validation
	•	Distribution checks
	•	Stability analysis
	•	Sanity checks against known administrative patterns

⸻

Repository Structure

├── src/
│   ├── compute_afi_advanced.py        # AFI computation pipeline
│   ├── validate_afi.py                # Sanity checks & validation
│   ├── compute_afi_typologies.py      # Unsupervised district typologies
│   ├── make_visuals_final.py          # AFI visualisations
│   ├── make_typology_visuals.py       # Typology plots & tables
│
├── outputs/
│   ├── afi_summary.csv
│   ├── merged_for_afi.csv
│   ├── afi_with_typologies.csv
│
├── dashboard/
│   ├── Next.js dashboard prototype
│
├── images/
│


⸻

Dashboard (MVP)

The dashboard is a analytical interface that displays:
	•	AFI distributions and percentiles
	•	State and district rankings
	•	District typologies
	•	Temporal trends
	•	Typology composition by state


⸻

Ethical & Privacy Considerations
	•	No individual-level data is used
	•	No predictions about individuals
	•	All analysis is performed on aggregated, anonymized public datasets

⸻

Future Work
	•	Lightweight trend-based early-warning alerts
	•	Integration with public platforms (e.g., AIKosh, data.gov.in)
	•	Policy briefs and administrative dashboards
	•	Adaptation of AFI methodology to other Digital Public Infrastructure datasets

⸻

Author

Developed independently as part of the AI for All Challenge, using public data and open-source tools to improve transparency, governance, and citizen outcomes.
