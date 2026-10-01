#!/usr/bin/env python3
"""Cross-check completed native results, logs and the recorded Java command."""
import html
import datetime
import importlib.util
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from PIL import Image

a2 = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("summarizer", a2 / "scripts/summarize-spec.py")
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
log_dir, result_dir = map(Path, sys.argv[1:3])
mode = sys.argv[3]  # full diagnostic, Base, single formal workload, or short smoke
assert mode in ("full", "base", "single", "smoke")
run = json.loads((log_dir / "run.json").read_text())
assert run["end"] and run["exit_code"] == 0
raws = list(result_dir.rglob("*.raw"))
assert len(raws) == 1, "Expected exactly one native run"
raw = raws[0]
images = list(raw.parent.rglob("*.jpg"))
assert images
for image in images:
    with Image.open(image) as picture:
        picture.verify()
result = parser.read_result(raw)
root = ET.parse(raw).getroot()
stdout = (log_dir / "stdout.log").read_text()
stderr = (log_dir / "stderr.log").read_text()
assert re.search(r"Kit signature and checksum is validated\..*?\.passed\.", stdout, re.S)
assert "Iteration 1 (1 operation) result: PASSED" in stdout
assert not re.search(r"Exception|OutOfMemoryError|\*\*NOT VALID\*\*|fatal error", stdout + stderr)
names = list(result["workloads_ops_m"])
if mode in ("full", "base"):
    expected = json.loads((a2 / "evidence/environment/official-result.json").read_text())["workloads_ops_m"]
    assert set(names) == set(expected), "Incomplete full-suite coverage"
    declared = re.search(r"Benchmarks:\s+([^\n]+)", stdout)[1].split()
    assert names == declared, "Raw workload order differs from the harness sequence"
else:
    assert len(names) == 1 and not names[0].startswith("startup.")

if mode == "base":
    assert run["command"][1:] == ["-jar", "SPECjvm2008.jar", "--base"]
    assert result["category"] == "SPECjvm2008 Base"
    assert not result["violations"], result["violations"]
    assert result["native_status"] == "Run is compliant"
if mode in ("base", "single"):
    for name, measurement in result["measurements"].items():
        iterations = measurement["iterations"]
        assert len(iterations) == 1
        if name.startswith("startup."):
            assert iterations[0]["expectedLoops"] == "1"
        else:
            assert len(measurement["warmup"]) == 1
            assert measurement["warmup"][0]["expectedDuration"] == "120000"
            assert iterations[0]["expectedDuration"] == "240000"
    for key in ("JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "CLASSPATH"):
        assert not run["environment"][key], (key, run["environment"][key])
    assert run["java_path"] == str(Path.home() / ".local/opt/java-se-7u75-ri/bin/java")

reports = {}
for suffix in (".txt", ".html", ".summary"):
    text = raw.with_suffix(suffix).read_text(encoding="latin1")
    if suffix == ".html":
        text = html.unescape(re.sub(r"<[^>]*>", " ", text))
    found = re.findall(r"composite result:\s*([\d,.]+)\s+(?:SPECjvm2008 (?:Base|Peak) )?ops/m", text, re.I)
    assert found and all(abs(float(s.replace(",", "")) - result["composite_ops_m"]) < .0051 for s in found)
    reports[suffix] = found
sub = dict(line.split("=", 1) for line in raw.with_suffix(".sub").read_text().splitlines() if "=" in line)
assert abs(float(sub["spec.jvm2008.report.result.score"]) - result["composite_ops_m"]) < .0051
txt = raw.with_suffix(".txt").read_text(encoding="latin1")
for name, score in result["groups_ops_m"].items():
    field = re.search(r"^" + re.escape(name) + r"\s+([\d,.]+)\s*$", txt, re.M)
    assert field and abs(float(field[1].replace(",", "")) - score) < .0051, name
for name, measurement in result["measurements"].items():
    for i in measurement["iterations"]:
        score = float(i["operations"]) * 60000 / (int(i["endTime"]) - int(i["startTime"]))
        field = re.search(r"^" + re.escape(name) + r"\s+iteration " + i["iteration"] +
                          r"\s+\S+\s+\S+\s+\S+\s+([\d,.]+)\s*$", txt, re.M)
        assert field and abs(float(field[1].replace(",", "")) - score) < .0051, name
record = {"mode": mode, "workload_count": len(names), "workloads": names,
          "checksum": "passed", "correctness": "passed", "reports_agree": reports,
          "native_status": result["native_status"], "category": result["category"],
          "violations": result["violations"], "score": result["composite_ops_m"],
          "unit": result["unit"], "exit_code": run["exit_code"],
          "wall_clock_seconds": (datetime.datetime.fromisoformat(run["end"]) -
                                 datetime.datetime.fromisoformat(run["start"])).total_seconds(),
          "monotonic_seconds": run["wall_seconds"],
          "stdout_bytes": (log_dir / "stdout.log").stat().st_size,
          "native_images_verified": len(images),
          "stderr_bytes": (log_dir / "stderr.log").stat().st_size}
(log_dir / "assessment.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
