#!/usr/bin/env python3
"""Re-evaluate historical choices by one immutable reference, without changing old scores."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

P1 = Path(__file__).resolve().parents[1]
INPUTS = {
    "grid_summary.csv": "8f3bfbb506370076afe3a15f08cd1bcff8f5e23e34f05a5ec6e9e5702f6761ec",
    "search_summary.csv": "9bbc2490e77476f40278f16eead5b053a0cc67b828b86e14346d1de548e31fbc",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=P1 / "results/summary")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    for name, expected in INPUTS.items():
        if hashlib.sha256((args.input_dir / name).read_bytes()).hexdigest() != expected:
            raise ValueError("historical input identity changed: " + name)
    with (args.input_dir / "grid_summary.csv").open(newline="") as stream:
        grid = list(csv.DictReader(stream))
    reference = {(int(row["s"]), row["opt"]): float(row["median_s"]) for row in grid}
    expected_space = {(s, opt) for s in (8, 16, 24, 64, 128) for opt in ("O0", "O1", "O2", "O3")}
    if set(reference) != expected_space or len(grid) != 20 or any(
        int(row["valid_runs"]) != 3 or int(row["failed_runs"]) != 0 for row in grid
    ) or any(not math.isfinite(value) or value <= 0 for value in reference.values()):
        raise ValueError("incomplete or invalid historical reference")
    best = min(reference.values())
    with (args.input_dir / "search_summary.csv").open(newline="") as stream:
        searches = list(csv.DictReader(stream))
    output = []
    for row in searches:
        if row["state"] != "complete" or row["confirmation_state"] != "complete":
            raise ValueError("historical search/confirmation is incomplete")
        config = int(row["returned_s"]), row["returned_opt"]
        value = reference[config]
        output.append(dict(stage=row["stage"], algorithm=row["algorithm"], seed=int(row["seed"]),
            s=config[0], opt=config[1], reference_s=value, gap_ref_pct=100 * (value / best - 1),
            observed_reference_within_5pct=value <= 1.05 * best,
            online_score_s=float(row["online_score_s"]),
            separate_confirmation_s=float(row["confirmed_s"]),
            search_process_runs=int(row["search_process_runs"]),
            confirmation_process_runs=int(row["confirmation_process_runs"]),
            search_driver_monotonic_s=float(row["search_full_driver_wall_s"]),
            confirmation_driver_monotonic_s=float(row["confirmation_full_driver_wall_s"]),
            total_driver_monotonic_s=float(row["total_wall_s"]), journal=row["journal"]))
    directory = args.output_dir.resolve()
    if directory.exists():
        raise ValueError("derived output exists; use a new directory")
    if directory == args.input_dir.resolve() or any(
        directory == (P1 / "results" / name).resolve() or (P1 / "results" / name).resolve() in directory.parents
        for name in ("reference_v1", "selection_v1", "holdout_v1", "conflict_selection_v1")
    ):
        raise ValueError("derived output must stay outside raw/input directories")
    directory.mkdir(parents=True)
    with (directory / "search_choices.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    provenance = dict(historical_checkpoint="3ac0c4688b964c873379d012cbcf09afb7ed0937",
        input_sha256=INPUTS, n=4096, kernel_clock="CLOCK_MONOTONIC", reference_min_s=best,
        quality_rule="one T_ref(c) for each configuration identity; independent confirmation is separate",
        limitation="observational reference only; 5% membership is not a reliable near-optimality proof",
        old_raw_protocol_scores_and_decisions_changed=False, searches=output)
    (directory / "summary.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(searches=len(output), reference_configs=len(reference), output=str(directory))))


if __name__ == "__main__":
    main()
