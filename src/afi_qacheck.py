
"""
AFI QA check script - saved by ChatGPT
Usage: python afi_qacheck.py /path/to/merged_for_afi.csv
Creates outputs in the same folder as the input:
 - top200_afi.csv
 - bottom200_afi.csv
 - top5_afi_sample.csv
 - afi_qacheck_report.json
Prints a concise summary to stdout.
"""
import sys, json
from pathlib import Path
import pandas as pd

def main(argv):
    if len(argv) < 2:
        print("Usage: python afi_qacheck.py /path/to/merged_for_afi.csv")
        return 1
    p = Path(argv[1])
    if not p.exists():
        print("File not found:", p)
        return 2
    outdir = p.parent
    sheet = pd.read_csv(p, dtype=str, low_memory=False)
    sheet.columns = [c.strip() for c in sheet.columns]


    num_cols = ['enrol_total','demo_total','bio_total','demo_to_enrol_ratio','bio_to_demo_ratio','missing_demo','afi_pct_bio_coverage','afi_composite_score']
    for c in num_cols:
        if c in sheet.columns:
            sheet[c] = pd.to_numeric(sheet[c].fillna('0').replace('', '0'), errors='coerce').fillna(0.0)

    total_rows = len(sheet)
    period_na = sheet['period'].isna().sum() if 'period' in sheet.columns else None
    period_empty = int((sheet['period'].fillna('') == '').sum()) if 'period' in sheet.columns else None
    unknown_states = int((sheet.get('state_canonical', pd.Series()).fillna('') == 'UNKNOWN').sum()) if 'state_canonical' in sheet.columns else 0
    missing_demo_count = int((sheet.get('missing_demo', pd.Series(0)).astype(float) > 0).sum()) if 'missing_demo' in sheet.columns else 0
    group_keys = ['period','state_canonical','district_clean','pincode']
    existing_keys = [kdx for kdx in group_keys if kdx in sheet.columns]
    dup_count = int(sheet.duplicated(subset=existing_keys, keep=False).sum()) if existing_keys else 0

    print("AFI QA report for", p)
    print("Total rows:", total_rows)
    if period_na is not None:
        print("period NA:", period_na, "period empty-string:", period_empty)
    print("UNKNOWN state_canonical rows:", unknown_states)
    print("Rows with missing_demo > 0:", missing_demo_count, f"({missing_demo_count/total_rows:.4%})")
    print("Duplicate group keys count:", dup_count)


    summary = {}
    for c in num_cols:
        if c in sheet.columns:
            s = sheet[c].describe(percentiles=[0.01,0.05,0.25,0.5,0.75,0.95,0.99])
            summary[c] = s.to_dict()


    top50 = sheet.sort_values('afi_composite_score', ascending=False).head(200)
    bottom50 = sheet.sort_values('afi_composite_score', ascending=True).head(200)
    top5 = sheet.sort_values('afi_composite_score', ascending=False).head(5)
    top50.to_csv(outdir / "top200_afi.csv", index=False)
    bottom50.to_csv(outdir / "bottom200_afi.csv", index=False)
    top5.to_csv(outdir / "top5_afi_sample.csv", index=False)

    report = {
        "total_rows": int(total_rows),
        "period_na": int(period_na) if period_na is not None else None,
        "period_empty": int(period_empty) if period_empty is not None else None,
        "unknown_state_canonical": int(unknown_states),
        "missing_demo_count": int(missing_demo_count),
        "missing_demo_pct": float(missing_demo_count/total_rows) if total_rows>0 else None,
        "duplicate_group_keys": int(dup_count),
        "numeric_summary": summary
    }
    with open(outdir / "afi_qacheck_report.json","w") as fh:
        json.dump(report, fh, indent=2)
    print("Wrote top200_afi.csv, bottom200_afi.csv, top5_afi_sample.csv, afi_qacheck_report.json in", outdir)

if __name__ == "__main__":
    sys.exit(main(sys.argv))