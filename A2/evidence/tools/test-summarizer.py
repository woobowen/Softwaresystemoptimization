#!/usr/bin/env python3
"""Check selection, statistics and failure cases using the final native results."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

a2 = Path(__file__).resolve().parents[2]
arguments = argparse.ArgumentParser(description=__doc__)
arguments.add_argument("--results", type=Path, default=a2 / "results")
arguments.add_argument("--output", type=Path, default=a2 / "evidence/final/parser-tests-stage5.json")
args = arguments.parse_args()
script = a2 / "scripts/summarize-spec.py"
base = next((args.results / "base").rglob("*.raw"))
source = next((args.results / "repeat").rglob("*.raw"))
cases = []


def check(name, arguments, expected, message=None):
    p = subprocess.run([sys.executable, str(script), *map(str, arguments)],
                       capture_output=True, text=True, timeout=10)
    assert (p.returncode == 0) == expected, (name, p.stderr)
    if message:
        assert message in p.stderr, (name, p.stderr)
    cases.append({"case": name, "exit_code": p.returncode, "stderr": p.stderr.strip()})
    return json.loads(p.stdout) if expected else None


check("actual_raw", [source], True)
check("directory", [source.parent], True)
check("same_path_twice", [source, source], False, "Duplicate result")
full = check("full_suite", [base], True)["runs"][0]
assert len(full["workloads_ops_m"]) == 38
root = ET.parse(base).getroot()
for name in ("compress", "derby", "crypto.aes", "startup.compress"):
    item = root.find(f"benchmark-results/benchmark-result[@name='{name}']/iterations/iteration-result")
    expected = float(item.get("operations")) * 60000 / (int(item.get("endTime")) - int(item.get("startTime")))
    assert math.isclose(full["workloads_ops_m"][name], expected, rel_tol=1e-12)
crypto_children = [v for k, v in full["workloads_ops_m"].items() if k.startswith("crypto.")]
assert len(crypto_children) == 3
assert math.isclose(full["groups_ops_m"]["crypto"], math.prod(crypto_children) ** (1/3), rel_tol=1e-12)
assert full["workloads_ops_m"]["compress"] != full["workloads_ops_m"]["startup.compress"]
comparison = check("statistics_and_compare", [args.results / "repeat", "--compare", args.results / "parameter"], True)
means = []
for directory, group in (("repeat", "original"), ("parameter", "modified")):
    values = []
    for raw in sorted((args.results / directory).rglob("*.raw")):
        item = ET.parse(raw).find("benchmark-results/benchmark-result[@name='compress']/iterations/iteration-result")
        values.append(float(item.get("operations")) * 60000 / (int(item.get("endTime")) - int(item.get("startTime"))))
    assert len(values) == 3
    stats = comparison[group]["statistics"]
    expected_mean = sum(values) / 3
    for field, value in {"mean": expected_mean, "min": min(values), "max": max(values),
                         "range": max(values)-min(values),
                         "relative_range_percent": (max(values)-min(values))/expected_mean*100}.items():
        assert math.isclose(stats[field], value, rel_tol=1e-12, abs_tol=1e-12), field
    means.append(expected_mean)
assert math.isclose(comparison["percentage_change"], (means[1]-means[0])/means[0]*100, abs_tol=1e-10)
with tempfile.TemporaryDirectory(prefix="a2-parser-test-") as directory:
    root = Path(directory)
    copy = root / source.name
    shutil.copy2(source, copy)
    shutil.copy2(source.with_suffix(".txt"), copy.with_suffix(".txt"))
    check("duplicate_copy", [source, copy], False, "Duplicate result")
    check("missing_input", [root / "absent"], False, "does not exist")
    (root / "empty").mkdir()
    check("missing_raw", [root / "empty"], False, "No raw files")

    tree = ET.parse(source)
    ET.SubElement(tree.getroot(), "error").text = "test fixture correctness failure"
    tree.write(copy)
    check("correctness_failure", [copy], False, "correctness errors")

    tree = ET.parse(source)
    iteration = tree.find("benchmark-results/benchmark-result[@name='compress']/iterations/iteration-result")
    del iteration.attrib["operations"]
    tree.write(copy)
    check("missing_score_field", [copy], False, "operations")

    tree = ET.parse(source)
    iteration = tree.find("benchmark-results/benchmark-result[@name='compress']/iterations/iteration-result")
    iteration.set("operations", "0")
    tree.write(copy)
    check("nonpositive_score", [copy], False, "invalid score")

    tree = ET.parse(source)
    benchmarks = tree.getroot().find("benchmark-results")
    benchmarks.append(ET.fromstring(ET.tostring(benchmarks.find("benchmark-result[@name='compress']"))))
    tree.write(copy)
    check("duplicate_workload", [copy], False, "duplicate workload")

    tree = ET.parse(source)
    item = tree.find("benchmark-results/benchmark-result[@name='compress']/warmup-result/iteration-result")
    item.set("operations", "999999999")
    tree.write(copy)
    check("warmup_excluded", [copy], True)

    shutil.copy2(source, copy)
    report = source.with_suffix(".txt").read_text()
    copy.with_suffix(".txt").write_text(report.replace("ops/m", "ops/s"))
    check("wrong_unit", [copy], False, "unexpected unit")

    shutil.copy2(source, copy)
    report = source.with_suffix(".txt").read_text()
    copy.with_suffix(".txt").write_text(report.replace("composite result:", "missing result:"))
    check("missing_report_score", [copy], False, "composite differs")

record = {"parser_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
          "results_root": str(args.results.resolve()),
          "measurement_role": "timing-invalidated-fixtures" if "invalidated-results" in args.results.parts else "final-results",
          "source_raw": str(source), "base_raw": str(base), "tests": cases,
          "group_child_startup_selection": True, "statistics_from_native_fields": True}
args.output.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
