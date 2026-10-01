#!/usr/bin/env python3
"""Check historical configuration records, without accepting their invalidated timing."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

a2 = Path(__file__).resolve().parents[2]
archived = a2 / "evidence/timing/invalidated-results"
base_dir = a2 / "evidence/base/base-1"
base = json.loads((base_dir / "run.json").read_text())
frozen = json.loads((a2 / "evidence/environment/formal-environment.json").read_text())
assert base["environment"] == frozen["environment"]
assert base["end"] and base["exit_code"] == 0
assert hashlib.sha256((a2 / "evidence/runner/frozen-run-spec.py").read_bytes()).hexdigest() == frozen["runner_sha256"]

def summarize(*arguments):
    return json.loads(subprocess.check_output([
        sys.executable, str(a2 / "scripts/summarize-spec.py"), *map(str, arguments)]))

base_result = summarize(archived / "base")["runs"][0]
comparison = summarize(archived / "repeat", "--compare", archived / "parameter")
workload = comparison["original"]["statistics"]["workload"]
default_command = [base["java_path"], "-jar", "SPECjvm2008.jar", workload]
previous_end = datetime.datetime.fromisoformat(base["end"])
pids, starts, hashes, rows = set(), set(), set(), []
option = None
for group, key in (("repeat", "original"), ("parameter", "modified")):
    results = comparison[key]["runs"]
    assert len(results) == 3
    for number, result in enumerate(results, 1):
        directory = a2 / "evidence" / group / f"{group}-{number}"
        run = json.loads((directory / "run.json").read_text())
        assessment = json.loads((directory / "assessment.json").read_text())
        assert run["end"] and run["exit_code"] == 0
        assert assessment["correctness"] == "passed"
        assert run["environment"] == base["environment"]
        assert run["java_path"] == base["java_path"]
        assert run["runner_sha256"] == base["runner_sha256"]
        assert run["cwd"] == base["cwd"]
        if group == "repeat":
            assert run["command"] == default_command
        else:
            command = run["command"]
            assert len(command) == len(default_command) + 1
            assert command[0] == default_command[0] and command[2:] == default_command[1:]
            if option is None:
                option = command[1]
            assert command[1] == option
            observed = json.loads((directory / "process-observation.json").read_text())
            assert observed["cmdline"] == command and observed["exe"] == run["java_path"]
            assert observed["environment_matches_run_record"]
        assert run["pid"] not in pids and run["start"] not in starts
        assert result["sha256"] not in hashes
        pids.add(run["pid"])
        starts.add(run["start"])
        hashes.add(result["sha256"])
        start = datetime.datetime.fromisoformat(run["start"])
        end = datetime.datetime.fromisoformat(run["end"])
        assert start >= previous_end and end > start, "Runs overlap or are out of order"
        previous_end = end
        measurement = result["measurements"][workload]
        assert measurement["configuration"] == base_result["measurements"][workload]["configuration"]
        assert len(measurement["warmup"]) == len(measurement["iterations"]) == 1
        for phase, duration in (("warmup", 120000), ("iterations", 240000)):
            iteration = measurement[phase][0]
            assert int(iteration["expectedDuration"]) == duration
            assert int(iteration["endTime"]) - int(iteration["startTime"]) >= duration
        for field in ("name", "version", "java.specification", "boot.class.path"):
            tag = "spec.jvm2008.report.jvm." + field
            assert result["jvm"][tag] == base_result["jvm"][tag]
        manifest = json.loads((directory / "copy-manifest.json").read_text())
        assert len(manifest) == 1
        copied = archived / group / Path(manifest[0]["copy"]).name
        assert Path(result["raw_file"]).parent == copied
        for name, digest in manifest[0]["sha256"].items():
            assert hashlib.sha256((copied / name).read_bytes()).hexdigest() == digest
        rows.append({"group": group, "number": number, "pid": run["pid"],
                     "start": run["start"], "end": run["end"],
                     "score_ops_m": result["workloads_ops_m"][workload],
                     "raw": result["raw_file"], "sha256": result["sha256"]})

selection = json.loads((a2 / "evidence/parameter/selection.json").read_text())
assert option == selection["one_jvm_option"]
output = {"measurement_status": "TIMING-INVALIDATED; configuration check only",
          "workload": workload, "one_changed_jvm_option": option,
          "same_environment_jdk_runner_threads_durations": True,
          "six_independent_processes_and_raw_files": True, "runs": rows,
          "original": comparison["original"]["statistics"],
          "modified": comparison["modified"]["statistics"],
          "percentage_change": comparison["percentage_change"]}
(a2 / "evidence/final/invalidated-experiment-check-stage5.json").write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps(output, indent=2))
