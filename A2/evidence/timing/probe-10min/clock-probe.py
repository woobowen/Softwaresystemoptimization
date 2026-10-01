#!/usr/bin/env python3
"""Observe Python and Java 7 clocks together; this is not a benchmark."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output", type=Path)
parser.add_argument("--seconds", type=int, default=600)
parser.add_argument("--jdk", type=Path, default=Path.home() / ".local/opt/java-se-7u75-ri")
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
samples = []
with tempfile.TemporaryDirectory(prefix="a2-clock-probe-") as build:
    subprocess.run([str(args.jdk / "bin/javac"), "-d", build,
                    str(Path(__file__).with_name("ClockProbe.java"))], check=True)
    command = [str(args.jdk / "bin/java"), "-cp", build,
               "ClockProbe", str(args.seconds)]
    with (args.output / "java-stderr.log").open("w") as err, \
            (args.output / "samples.jsonl").open("w") as log:
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=err, text=True)
        for line in child.stdout:
            wall, nano = map(int, line.split())
            sample = {"python_time": time.time(), "python_monotonic": time.monotonic(),
                      "python_boottime": time.clock_gettime(time.CLOCK_BOOTTIME),
                      "java_currentTimeMillis": wall, "java_nanoTime": nano}
            log.write(json.dumps(sample) + "\n")
            log.flush()
            samples.append(sample)
        exit_code = child.wait()
scales = {"python_time": 1, "python_monotonic": 1, "python_boottime": 1,
          "java_currentTimeMillis": 1000, "java_nanoTime": 1e9}
elapsed = {key: (samples[-1][key] - samples[0][key]) / scale
           for key, scale in scales.items()}
steps = [(b["python_time"] - a["python_time"]) -
         (b["python_monotonic"] - a["python_monotonic"])
         for a, b in zip(samples, samples[1:])]
summary = {"command": command, "exit_code": exit_code, "sample_count": len(samples),
           "elapsed_seconds": elapsed,
           "python_wall_minus_monotonic_seconds": elapsed["python_time"] - elapsed["python_monotonic"],
           "java_wall_minus_nano_seconds": elapsed["java_currentTimeMillis"] - elapsed["java_nanoTime"],
           "min_step_difference_seconds": min(steps),
           "max_step_difference_seconds": max(steps)}
(args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
raise SystemExit(exit_code)
