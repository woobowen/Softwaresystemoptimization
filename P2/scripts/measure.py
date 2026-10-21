#!/usr/bin/env python3
"""Run a finite set of normal sorting measurements and retain every sample."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess

P2 = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--binary", type=Path, default=P2 / "homework/sort")
    parser.add_argument("--versions", nargs="+", default=["sort_a"])
    parser.add_argument("--sizes", nargs="+", type=int, default=[4096, 65536, 1048576])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--cpu", type=int, default=2)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    binary = args.binary.resolve()
    metadata = dict(binary=str(binary), sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                    versions=args.versions, sizes=args.sizes, seed=42,
                    R=args.repeats, runs=args.runs, cpu=args.cpu,
                    statistic="median of independent process means; seconds per sort")
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    rows = []
    for n in args.sizes:
        # One explicitly excluded warmup per version and size.
        for version in args.versions:
            command = ["taskset", "-c", str(args.cpu), str(binary), "-b", "-s", "42",
                       "-v", version, str(n), "1"]
            run = subprocess.run(command, text=True, capture_output=True, check=True)
            (args.output / f"warmup-{version}-{n}.txt").write_text(
                "$ " + " ".join(command) + "\n" + run.stdout + run.stderr)
        for trial in range(args.runs):
            order = args.versions[trial % len(args.versions):] + args.versions[:trial % len(args.versions)]
            for version in order:
                command = ["taskset", "-c", str(args.cpu), str(binary), "-b", "-s", "42",
                           "-v", version, str(n), str(args.repeats)]
                run = subprocess.run(command, text=True, capture_output=True, check=True)
                text = run.stdout + run.stderr
                (args.output / f"run-{trial}-{version}-{n}.txt").write_text(
                    "$ " + " ".join(command) + "\n" + text)
                if "FAIL" in text or text.count("Arrays are sorted: yes") != 2:
                    raise RuntimeError("Sorting check failed: " + " ".join(command))
                for kind in ("random", "inverted"):
                    values = [float(x) for x in re.findall(
                        rf"TIME version={version} input={kind} trial=\d+ seconds=([\d.]+)", text)]
                    if len(values) != args.repeats or min(values) <= 0:
                        raise RuntimeError("Missing or invalid time samples")
                    avg = float(re.search(
                        rf"AVG version={version} input={kind} n={n} R={args.repeats} seconds=([\d.]+)", text)[1])
                    if abs(avg - statistics.mean(values)) > 1.1e-9:
                        raise RuntimeError("Average does not match retained individual samples")
                    rows.append(dict(run=trial, version=version, n=n, input=kind, seed=42,
                                     R=args.repeats, mean_seconds=avg,
                                     individual_seconds=json.dumps(values)))
            print(f"n={n}, run={trial + 1}/{args.runs} saved", flush=True)
    with (args.output / "samples.csv").open("w") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summaries = []
    for n in args.sizes:
        for kind in ("random", "inverted"):
            baseline = [r["mean_seconds"] for r in rows
                        if r["n"] == n and r["input"] == kind and r["version"] == "sort_a"]
            base = statistics.median(baseline) if baseline else None
            for version in args.versions:
                values = [r["mean_seconds"] for r in rows
                          if r["n"] == n and r["input"] == kind and r["version"] == version]
                median = statistics.median(values)
                summaries.append(dict(version=version, n=n, input=kind,
                                      median_seconds=median, min_seconds=min(values),
                                      max_seconds=max(values),
                                      speedup_vs_a=base / median if base else ""))
    with (args.output / "summary.csv").open("w") as output:
        writer = csv.DictWriter(output, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
