"""
One-time / periodic extraction tool: converts the official AICTE "Institute List" PDF
into the versioned local institution master dataset consumed by the app
(backend/app/data/institutions_aicte.json).

Source (authoritative, official Government of India data):
  All India Council for Technical Education (AICTE) - Institute Permanent ID List
  https://www.aicte.gov.in/downloads/Institute_List.pdf

This is NOT a live API - AICTE does not publish a public search API for this list.
This script is the documented "controlled refresh process": re-download the PDF from
the URL above when a newer version is published, point --pdf at the new file, and
re-run this script to regenerate the dataset JSON (see docs/INSTITUTION_VERIFICATION.md).

Usage:
    python scripts/extract_aicte_pdf.py --pdf <path-to-downloaded-pdf> --out app/data/institutions_aicte.json
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone

import pdfplumber


def clean_cell(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.replace("\n", " ")).strip()


def extract_rows(pdf_path: str) -> list[dict]:
    rows: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if not tables:
                continue
            for table in tables:
                for row in table:
                    if not row or len(row) < 5:
                        continue
                    permanent_id = clean_cell(row[0])
                    name = clean_cell(row[1])
                    state = clean_cell(row[2])
                    district = clean_cell(row[3])
                    city = clean_cell(row[4])
                    if not permanent_id or not name:
                        continue
                    if permanent_id.lower().startswith("institute"):
                        continue  # header row
                    rows.append({
                        "aicteId": permanent_id,
                        "name": name,
                        "state": state or None,
                        "district": district or None,
                        "city": city or None,
                    })
            if (i + 1) % 100 == 0:
                print(f"  processed {i + 1}/{total_pages} pages, {len(rows)} rows so far", file=sys.stderr)
    return rows


def normalize_name(name: str) -> str:
    upper = name.upper()
    upper = re.sub(r"[^\w\s]", " ", upper)
    upper = re.sub(r"\s+", " ", upper).strip()
    return upper


def acronym_of(name: str) -> str:
    words = [w for w in normalize_name(name).split(" ") if w and w not in {"OF", "AND", "&", "THE", "FOR"}]
    return "".join(w[0] for w in words if w)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path to the downloaded AICTE Institute_List.pdf")
    parser.add_argument("--out", default="app/data/institutions_aicte.json", help="Output JSON path")
    parser.add_argument("--source-url", default="https://www.aicte.gov.in/downloads/Institute_List.pdf")
    parser.add_argument("--dataset-date", default=None, help="Dataset date/version if known (e.g. from PDF metadata)")
    args = parser.parse_args()

    print(f"Extracting institution rows from {args.pdf} ...", file=sys.stderr)
    rows = extract_rows(args.pdf)
    print(f"Extracted {len(rows)} raw rows.", file=sys.stderr)

    seen_ids = set()
    deduped = []
    for r in rows:
        if r["aicteId"] in seen_ids:
            continue
        seen_ids.add(r["aicteId"])
        r["normalizedName"] = normalize_name(r["name"])
        r["derivedAcronym"] = acronym_of(r["name"])
        deduped.append(r)

    dataset = {
        "source": "AICTE",
        "sourceName": "All India Council for Technical Education - Institute Permanent ID List",
        "sourceReference": args.source_url,
        "datasetDate": args.dataset_date,
        "importedAt": datetime.now(timezone.utc).isoformat(),
        "recordCount": len(deduped),
        "institutions": deduped,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(deduped)} unique institutions to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
