#!/usr/bin/env python3
"""Archived stage-3 driver; not used for new measurements or timing recovery."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

a2 = Path(__file__).resolve().parents[2]
group, workload, *options = sys.argv[1:]
assert group in ("repeat", "parameter")
assert len(options) == (0 if group == "repeat" else 1)
frozen = json.loads((a2 / "evidence/environment/formal-environment.json").read_text())
base = json.loads((a2 / "evidence/base/base-1/assessment.json").read_text())
assert base["mode"] == "base" and base["correctness"] == "passed"
assert workload in base["workloads"] and not workload.startswith("startup.")
runner = a2 / "scripts/run-spec.py"
assert hashlib.sha256(runner.read_bytes()).hexdigest() == frozen["runner_sha256"]
env = os.environ.copy()
for key, value in frozen["environment"].items():
    if value is None:
        env.pop(key, None)
    else:
        env[key] = value
# run-spec.py adds the JDK directory itself; keep its effective PATH identical.
java_bin, separator, rest = env["PATH"].partition(os.pathsep)
assert separator and java_bin == str(Path(env["JAVA_HOME"]) / "bin")
env["PATH"] = rest
env["SPEC_HOME"] = frozen["spec_home"]
parent = a2 / "evidence" / group
parent.mkdir(parents=True, exist_ok=True)
for number in range(1, 4):
    directory = parent / f"{group}-{number}"
    command = [sys.executable, str(runner), str(directory),
               *options, "-jar", "SPECjvm2008.jar", workload]
    print(f"Starting {group}-{number}", flush=True)
    subprocess.run(command, env=env, check=True)
    run = json.loads((directory / "run.json").read_text())
    assert run["exit_code"] == 0 and run["environment"] == frozen["environment"]
    subprocess.run([sys.executable, "-B", str(a2 / "evidence/tools/preserve-results.py"),
                    str(directory / "run.json"), str(a2 / "results" / group)], check=True)
    result = a2 / "results" / group / Path(run["result_paths"][0]).name
    subprocess.run([sys.executable, "-B", str(a2 / "evidence/tools/check-run.py"),
                    str(directory), str(result), "single"], check=True)
print(f"Completed all three {group} runs", flush=True)
