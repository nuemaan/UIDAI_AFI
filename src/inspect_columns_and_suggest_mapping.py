
"""
inspect_columns_and_suggest_mapping.py

Reads CSV headers from the three aggregated inputs and produces:
 - docs/column_report.csv        (summary, per-file headers + missing exacts)
 - docs/column_mapping_suggested.csv  (suggested mapping rows you can accept/edit)

Usage:
  source /path/to/venv/bin/activate
  python src/inspect_columns_and_suggest_mapping.py
"""
import csv
import difflib
from pathlib import Path


INPUTS = {
    "enrolment": Path("outputs/final_enrolment_for_afi.csv"),
    "demographic": Path("outputs/final_demographic_for_afi.csv"),
    "biometric": Path("outputs/final_biometric_for_afi.csv"),
}

OUT_DIR = Path("docs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CANONICAL = [
    "period",
    "state_canonical",
    "district_clean",
    "pincode",
    "enrol_total",
    "demo_total",
    "bio_total",

    "afi_composite_score",
    "enrol_age_18_greater",
    "bio_age_18_greater",
]

def read_headers(path: Path):
    if not path.exists():
        return None, f"missing file: {path}"
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
            header = [h.strip() for h in header]
            return header, None
        except StopIteration:
            return [], None

def find_candidate_for_missing(missing, headers):

    if not headers:
        return None, 0.0
    cand = difflib.get_close_matches(missing, headers, n=3, cutoff=0.5)
    if cand:

        top = cand[0]
        score = difflib.SequenceMatcher(None, missing.lower(), top.lower()).ratio()
        return top, score

    parts = missing.split("_")
    for h in headers:
        low = h.lower()
        if all(p.lower() in low for p in parts if p):
            return h, 0.45

    for h in headers:
        base = h.rsplit("_", 1)[0]
        if base.lower() == missing.lower():
            return h, 0.5
    return None, 0.0

def main():
    report_rows = []
    mapping_rows = []
    print("Inspecting headers for files:")
    for name, path in INPUTS.entries():
        header, err = read_headers(path)
        if err:
            print(f" - {name}: ERROR: {err}")
            report_rows.append({
                "file": name, "path": str(path), "status": "MISSING FILE", "found_columns": ""
            })
            continue
        print(f" - {name}: {len(header)} columns")
        found = set(h for h in header if h)

        missing = []
        suggestions = []
        for c in CANONICAL:
            if c in found:
                suggestions.append((c, c, 1.0))
            else:
                cand, score = find_candidate_for_missing(c, header)
                if cand:
                    suggestions.append((c, cand, score))
                    missing.append(c)
                else:
                    suggestions.append((c, "", 0.0))
                    missing.append(c)

        report_rows.append({
            "file": name,
            "path": str(path),
            "status": "OK" if not missing else f"MISSING {len(missing)}",
            "found_columns": "|".join(header),
            "missing_canonicals": ",".join(missing)
        })

        for canonical, found_col, score in suggestions:
            mapping_rows.append({
                "file": name,
                "path": str(path),
                "canonical": canonical,
                "found_column": found_col,
                "match_score": round(float(score), 3),
                "action": "KEEP" if canonical == found_col else ("SUGGEST_RENAME" if found_col else "MISSING")
            })


    rep_csv = OUT_DIR / "column_report.csv"
    with rep_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file","path","status","found_columns","missing_canonicals"])
        w.writeheader()
        for r in report_rows:
            w.writerow(r)
    print(f"Wrote {rep_csv}")

    map_csv = OUT_DIR / "column_mapping_suggested.csv"
    with map_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file","path","canonical","found_column","match_score","action"])
        w.writeheader()
        for r in mapping_rows:
            w.writerow(r)
    print(f"Wrote {map_csv}")


    print("\nQuick summary (first suggested mappings per file):")
    for name, path in INPUTS.entries():
        print(f"File: {name} -> {path}")

        for r in mapping_rows:
            if r["file"] == name and r["action"] != "KEEP":
                print(f"  canonical: {r['canonical']:25} suggested: {r['found_column'] or '---':25} score={r['match_score']} action={r['action']}")
        print("")

if __name__ == '__main__':
    main()