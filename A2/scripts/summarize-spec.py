#!/usr/bin/env python3
"""Read completed SPEC .raw files; verify scores against native TXT reports.

Usage: python3 summarize-spec.py RESULT.raw [RESULT.raw ...]
       python3 summarize-spec.py REPEAT_DIR --compare PARAMETER_DIR
Directories are searched for raw files. Repetitions must use one workload.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
import xml.etree.ElementTree as ET


def read_result(path):
    root = ET.parse(path).getroot()
    if root.findall(".//error"):
        raise ValueError(f"{path}: correctness errors in raw result")
    scores, details = {}, {}
    for benchmark in root.findall("benchmark-results/benchmark-result"):
        name = benchmark.attrib["name"]
        iterations = benchmark.findall("iterations/iteration-result")
        if not iterations:
            raise ValueError(f"{path}: missing measurement for {name}")
        if name == "check":
            continue
        if name in scores:
            raise ValueError(f"{path}: duplicate workload {name}")
        values = []
        for iteration in iterations:
            a = iteration.attrib
            elapsed = int(a["endTime"]) - int(a["startTime"])
            if elapsed <= 0:
                raise ValueError(f"{path}: invalid measurement time for {name}")
            values.append(float(a["operations"]) * 60000 / elapsed)
        if any(not math.isfinite(v) or v <= 0 for v in values):
            raise ValueError(f"{path}: invalid score for {name}")
        scores[name] = max(values)  # The native reporter uses the best iteration.
        details[name] = {"configuration": benchmark.attrib,
                         "warmup": [i.attrib for i in benchmark.findall(
                             "warmup-result/iteration-result")],
                         "iterations": [i.attrib for i in iterations]}
    if not scores or root.find("benchmark-results/benchmark-result[@name='check']") is None:
        raise ValueError(f"{path}: missing scores or initial functional check")
    groups = {}
    for name, score in scores.items():
        if name == "scimark.monte_carlo":
            names = ["scimark.large", "scimark.small"]
        elif name.startswith("scimark."):
            names = ["scimark." + name.rsplit(".", 1)[1]]
        else:
            names = [name.split(".", 1)[0]]
        for group in names:
            groups.setdefault(group, []).append(score)
    group_scores = {name: statistics.geometric_mean(values)
                    for name, values in groups.items()}
    composite = statistics.geometric_mean(group_scores.values())
    report = path.with_suffix(".txt").read_text(encoding="latin1")
    reported = re.search(r"composite result:\s*([\d,.]+)\s+([^\n]+)",
                         report, re.IGNORECASE)
    if not reported or abs(float(reported[1].replace(",", "")) - composite) > .0051:
        raise ValueError(f"{path}: composite differs from native TXT")
    status = re.search(r"^Run is .+$", report, re.MULTILINE)
    if not status or "not valid" in status[0]:
        raise ValueError(f"{path}: missing or invalid native report status")
    unit = reported[2].strip().split()[-1]
    if unit != "ops/m":
        raise ValueError(f"{path}: unexpected unit {unit}")
    return {"raw_file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "category": root.findtext("workload"), "unit": unit,
            "run_date": root.findtext("run-info/spec.jvm2008.report.run.date"),
            "native_status": status[0], "composite_ops_m": composite,
            "groups_ops_m": group_scores, "workloads_ops_m": scores,
            "measurements": details,
            "violations": [v.text for v in root.findall("violations/violation")],
            "jvm": {e.tag: e.text for e in root.find("jvm-info")}}


def load_runs(inputs, seen):
    paths = []
    for value in inputs:
        path = Path(value).resolve()
        if not path.exists():
            raise ValueError(f"Input does not exist: {path}")
        found = sorted(path.rglob("*.raw")) if path.is_dir() else [path]
        if not found:
            raise ValueError(f"No raw files in {path}")
        paths.extend(found)
    runs = []
    for path in paths:
        run = read_result(path)
        if run["sha256"] in seen:
            raise ValueError(f"Duplicate result is not an independent run: {path}")
        seen.add(run["sha256"])
        runs.append(run)
    return runs


def summarize(runs):
    output = {"runs": runs}
    if len(runs) > 1:
        names = list(runs[0]["workloads_ops_m"])
        if len(names) != 1 or any(list(r["workloads_ops_m"]) != names for r in runs):
            raise ValueError("Statistics require the same single workload in every input")
        values = [r["workloads_ops_m"][names[0]] for r in runs]
        output["statistics"] = {"workload": names[0], "unit": runs[0]["unit"], "scores": values,
            "mean": statistics.mean(values), "min": min(values), "max": max(values),
            "range": max(values) - min(values),
            "relative_range_percent": (max(values) - min(values)) / statistics.mean(values) * 100}
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--compare", nargs="+", help="Modified configuration results")
    args = parser.parse_args()
    seen = set()
    output = summarize(load_runs(args.inputs, seen))
    if args.compare:
        modified = summarize(load_runs(args.compare, seen))
        if "statistics" not in output or "statistics" not in modified:
            raise ValueError("Comparison requires repeated runs in both groups")
        original_stats, modified_stats = output["statistics"], modified["statistics"]
        if original_stats["workload"] != modified_stats["workload"]:
            raise ValueError("Comparison requires the same workload in both groups")
        change = (modified_stats["mean"] / original_stats["mean"] - 1) * 100
        output = {"original": output, "modified": modified, "percentage_change": change}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, ET.ParseError) as error:
        sys.exit(f"Error: {error}")
