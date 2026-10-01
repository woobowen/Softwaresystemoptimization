#!/usr/bin/env python3
"""Take one read-only progress snapshot; never attach to Java or its pipes."""
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys

directory = Path(sys.argv[1])
run = json.loads((directory / "run.json").read_text())
stdout = (directory / "stdout.log").read_text()
process = subprocess.run(["ps", "-p", str(run["pid"]), "-o", "pid,etimes,time,pcpu,rss,stat"],
                         text=True, capture_output=True)
benchmarks = re.findall(r"Benchmark:\s+(\S+)", stdout)
completed = re.findall(r"Score on (\S+):", stdout)
errors = re.findall(r"^.*(?:Exception|OutOfMemoryError|NOT VALID|Validation failure).*$",
                    stdout + (directory / "stderr.log").read_text(), re.M)
record = {"time": datetime.datetime.now().astimezone().isoformat(),
          "java_pid": run["pid"], "end": run["end"], "exit_code": run["exit_code"],
          "process": process.stdout.strip(), "current": benchmarks[-1] if benchmarks else None,
          "completed": len(completed), "last_complete": completed[-1] if completed else None,
          "stdout_bytes": (directory / "stdout.log").stat().st_size,
          "error_lines": errors[-5:],
          "stderr_bytes": (directory / "stderr.log").stat().st_size,
          "tail": stdout.splitlines()[-5:],
          "result_paths": run.get("result_paths", []),
          "result_dirs_present": sorted(p.name for p in Path(run["results_root"]).glob("SPECjvm2008.*"))}
with (directory / "monitor.jsonl").open("a") as log:
    log.write(json.dumps(record) + "\n")
print(f"{record['time']} current={record['current']} completed={record['completed']} "
      f"end={record['end']} exit={record['exit_code']}")
print(record["process"])
print(f"stderr={record['stderr_bytes']} bytes; error_lines={len(errors)}")
print("\n".join(record["tail"][-3:]))
