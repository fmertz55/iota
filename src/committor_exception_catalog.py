from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


INPUT_PATH = Path("output/findings/finding_020_committor_raw.csv")
OUTPUT_DIR = Path("output/findings")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument(
        "--output-prefix",
        default="finding_020_committor_exception_catalog",
    )
    parser.add_argument("--near-active", type=int, default=5000)
    parser.add_argument("--near-lcf", type=float, default=0.50)
    return parser.parse_args()


def is_exception(row: dict[str, Any], near_active: int, near_lcf: float) -> tuple[bool, str]:
    classification = str(row["classification"])
    active = int(float(row["active_iotas"]))
    lcf = float(row["coherence_ratio"])
    if classification != "protected":
        return True, classification
    if active >= near_active or lcf >= near_lcf:
        return True, "near_boundary_protected"
    return False, ""


def second_order_command(row: dict[str, Any]) -> str:
    return (
        "PYTHONUNBUFFERED=1 MPLCONFIGDIR=/private/tmp/mplconfig "
        ".venv/bin/python src/second_order_coherence_diagnostic.py "
        f"--seed {int(row['seed'])} "
        f"--law {row['law']} "
        f"--condition {row['condition']} "
        f"--sample-index {int(row['sample_index'])} "
        "--sample-every 128"
    )


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Missing input CSV: {args.input}")

    rows = []
    with args.input.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            keep, exception_type = is_exception(row, args.near_active, args.near_lcf)
            if not keep:
                continue
            row = dict(row)
            row["sample_number"] = int(row["sample_index"]) + 1
            row["exception_type"] = exception_type
            row["second_order_command"] = second_order_command(row)
            rows.append(row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / f"{args.output_prefix}.csv"
    json_path = OUTPUT_DIR / f"{args.output_prefix}.json"

    if rows:
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        csv_path.write_text("", encoding="utf-8")

    summary = {
        "input": str(args.input),
        "exception_count": len(rows),
        "near_active": args.near_active,
        "near_lcf": args.near_lcf,
        "output_csv": str(csv_path),
        "exceptions_by_seed_law_condition": {},
    }
    for row in rows:
        key = f"seed={row['seed']} law={row['law']} condition={row['condition']}"
        summary["exceptions_by_seed_law_condition"].setdefault(key, 0)
        summary["exceptions_by_seed_law_condition"][key] += 1

    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
