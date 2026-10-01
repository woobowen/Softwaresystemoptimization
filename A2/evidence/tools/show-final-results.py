#!/usr/bin/env python3
"""Display selected fields from summarize-spec.py for real terminal screenshots."""
import json
from pathlib import Path
import subprocess
import sys

a2 = Path(__file__).resolve().parents[2]
mode = sys.argv[1]
if mode not in ("base", "workloads", "repeat", "parameter"):
    sys.exit("Use base, workloads, repeat, or parameter")
inputs = [str(a2 / "results" / ("base" if mode in ("base", "workloads") else "repeat"))]
if mode == "parameter":
    inputs += ["--compare", str(a2 / "results/parameter")]
data = json.loads(subprocess.check_output(
    [sys.executable, "-B", str(a2 / "scripts/summarize-spec.py"), *inputs], text=True))
print("Source: native .raw and .txt, read by summarize-spec.py\n")
if mode in ("base", "workloads"):
    run = data["runs"][0]
    print(Path(run["raw_file"]).parent.name, "|", run["native_status"])
    print("Composite: %.2f ops/m | %d workloads" % (
        run["composite_ops_m"], len(run["workloads_ops_m"])))
    print("Violations:", run["violations"])
    print()
    values = run["groups_ops_m"] if mode == "base" else {
        name: run["workloads_ops_m"][name] for name in ("compress", "derby", "crypto.aes")}
    print("%-25s %12s" % ("Group" if mode == "base" else "Workload", "ops/m"))
    for name, score in values.items():
        print("%-25s %12.2f" % (name, score))
else:
    groups = [("Default", data)] if mode == "repeat" else [
        ("Default", data["original"]), ("-XX:+UseSerialGC", data["modified"])]
    for label, group in groups:
        print(label, "| compress | ops/m")
        for run in group["runs"]:
            print("  %-20s %10.2f" % (
                Path(run["raw_file"]).parent.name, run["workloads_ops_m"]["compress"]))
        s = group["statistics"]
        print("  Mean %.2f | Min %.2f | Max %.2f" % (s["mean"], s["min"], s["max"]))
        print("  Range %.2f | Relative range %.2f%%\n" % (
            s["range"], s["relative_range_percent"]))
    if mode == "parameter":
        print("Mean change (Serial / Default - 1): %+.2f%%" % data["percentage_change"])
