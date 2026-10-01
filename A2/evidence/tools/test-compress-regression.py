#!/usr/bin/env python3
"""Historical parser fixtures only: all seven measurements are timing-invalidated."""
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

a2 = Path(__file__).resolve().parents[2]
module_spec = importlib.util.spec_from_file_location("summarizer", a2 / "scripts/summarize-spec.py")
parser = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(parser)

# Invalidated fixtures, transcribed from compress/iterations/iteration-result.
fields = {
    "006": ("1445.0898764644649", "1790787023287", "1790787263287"),
    "007": ("3204.9457923743635", "1790794722115", "1790794962115"),
    "008": ("3151.8509983379604", "1790795121769", "1790795361769"),
    "009": ("3250.3298662377665", "1790795525438", "1790795765438"),
    "011": ("3200.319708847233", "1790796293338", "1790796533338"),
    "012": ("3217.662311895002", "1790796698885", "1790796938885"),
    "013": ("3225.929600735713", "1790797101385", "1790797341385"),
}
records = []
for run_id, expected in fields.items():
    candidates = list((a2 / "results").rglob("SPECjvm2008." + run_id + ".raw"))
    if not candidates:
        candidates = list((a2 / "evidence").rglob("SPECjvm2008." + run_id + ".raw"))
    assert len(candidates) == 1, (run_id, candidates)
    path = candidates[0]
    root = ET.parse(path).getroot()
    benchmark = root.find("benchmark-results/benchmark-result[@name='compress']")
    measurement = benchmark.find("iterations/iteration-result")
    actual = tuple(measurement.get(k) for k in ("operations", "startTime", "endTime"))
    assert actual == expected
    ops, start, end = expected
    score = float(ops) * 60000 / (int(end) - int(start))
    result = parser.read_result(path)
    assert abs(result["workloads_ops_m"]["compress"] - score) < 1e-9
    assert abs(result["groups_ops_m"]["compress"] - score) < 1e-9
    assert result["unit"] == "ops/m"
    warmup = benchmark.find("warmup-result/iteration-result")
    warmup_score = float(warmup.get("operations")) * 60000 / (
        int(warmup.get("endTime")) - int(warmup.get("startTime")))
    assert abs(score - warmup_score) > 0.01
    if "startup.compress" in result["workloads_ops_m"]:
        assert abs(score - result["workloads_ops_m"]["startup.compress"]) > 0.01
    records.append({"raw": str(path.relative_to(a2)), "name": "compress",
                    "phase": "iterations", "fields": measurement.attrib,
                    "score": score, "warmup_score_excluded": warmup_score})
output = {"passed": True, "measurement_status": "TIMING-INVALIDATED fixtures only", "cases": records}
(a2 / "evidence/final/invalidated-fixture-regression-stage5.json").write_text(
    json.dumps(output, indent=2) + "\n")
print("7 native compress fields, throughput/group scores and exclusions verified.")
