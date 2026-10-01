#!/usr/bin/env python3
"""Observe Python and Java 7 clocks together; this is not a benchmark."""
import argparse
import datetime
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
if args.seconds < 1:
    parser.error("--seconds must be positive")
args.output.mkdir(parents=True, exist_ok=False)
clocksource = Path("/sys/devices/system/clocksource/clocksource0/current_clocksource")
boot_id = Path("/proc/sys/kernel/random/boot_id")
started_at = datetime.datetime.now().astimezone().isoformat()
boot_before = boot_id.read_text().strip()
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
                      "java_currentTimeMillis": wall, "java_nanoTime": nano,
                      "clocksource": clocksource.read_text().strip()}
            if samples:
                previous, first = samples[-1], samples[0]
                for label, wall_key, mono_key, wall_scale, mono_scale in (
                        ("python", "python_time", "python_monotonic", 1, 1),
                        ("java", "java_currentTimeMillis", "java_nanoTime", 1000, 1e9)):
                    wall_delta = (sample[wall_key] - previous[wall_key]) / wall_scale
                    mono_delta = (sample[mono_key] - previous[mono_key]) / mono_scale
                    sample[label + "_interval"] = {
                        "wall_delta_seconds": wall_delta,
                        "monotonic_delta_seconds": mono_delta,
                        "difference_seconds": wall_delta - mono_delta,
                        "cumulative_difference_seconds":
                            (sample[wall_key] - first[wall_key]) / wall_scale -
                            (sample[mono_key] - first[mono_key]) / mono_scale}
            log.write(json.dumps(sample) + "\n")
            log.flush()
            samples.append(sample)
        exit_code = child.wait()
if len(samples) < 2:
    raise SystemExit("Probe did not produce two samples; inspect java-stderr.log")
scales = {"python_time": 1, "python_monotonic": 1, "python_boottime": 1,
          "java_currentTimeMillis": 1000, "java_nanoTime": 1e9}
elapsed = {key: (samples[-1][key] - samples[0][key]) / scale
           for key, scale in scales.items()}
steps = [(b["python_time"] - a["python_time"]) -
         (b["python_monotonic"] - a["python_monotonic"])
         for a, b in zip(samples, samples[1:])]
summary = {"command": command, "exit_code": exit_code, "sample_count": len(samples),
           "started_at": started_at,
           "ended_at": datetime.datetime.now().astimezone().isoformat(),
           "requested_seconds": args.seconds,
           "elapsed_seconds": elapsed,
           "python_wall_minus_monotonic_seconds": elapsed["python_time"] - elapsed["python_monotonic"],
           "java_wall_minus_nano_seconds": elapsed["java_currentTimeMillis"] - elapsed["java_nanoTime"],
           "min_step_difference_seconds": min(steps),
           "max_step_difference_seconds": max(steps)}
summary["clocksource_values"] = sorted({s["clocksource"] for s in samples})
summary["clocksource_consistent"] = summary["clocksource_values"] == ["hyperv_clocksource_tsc_page"]
summary["boot_id_start"] = boot_before
summary["boot_id_end"] = boot_id.read_text().strip()
summary["boottime_minus_monotonic_seconds"] = elapsed["python_boottime"] - elapsed["python_monotonic"]
for label in ("python", "java"):
    intervals = [s[label + "_interval"] for s in samples[1:]]
    differences = [i["difference_seconds"] for i in intervals]
    summary[label] = {
        "forward_adjustments_over_50ms": sum(d > .05 for d in differences),
        "backward_adjustments_over_50ms": sum(d < -.05 for d in differences),
        "backward_wall_intervals": sum(i["wall_delta_seconds"] < 0 for i in intervals),
        "min_interval_difference_seconds": min(differences),
        "max_interval_difference_seconds": max(differences),
        "cumulative_difference_seconds": intervals[-1]["cumulative_difference_seconds"],
        "max_monotonic_interval_seconds": max(i["monotonic_delta_seconds"] for i in intervals)}
# Internal engineering limits, not SPEC rules; retain all samples for review.
summary["acceptance_limits"] = {"max_abs_interval_difference_seconds": 1,
    "max_abs_cumulative_difference_seconds": 2, "max_sample_gap_seconds": 5,
    "jump_count_threshold_seconds": .05, "scope": "internal, not SPEC requirements"}
summary["gate_pass"] = (
    exit_code == 0 and elapsed["java_nanoTime"] >= args.seconds and
    summary["clocksource_consistent"] and summary["boot_id_start"] == summary["boot_id_end"] and
    abs(summary["boottime_minus_monotonic_seconds"]) < .1 and
    all(s["backward_wall_intervals"] == 0 and
        abs(s["min_interval_difference_seconds"]) < 1 and
        abs(s["max_interval_difference_seconds"]) < 1 and
        abs(s["cumulative_difference_seconds"]) < 2 and
        s["max_monotonic_interval_seconds"] < 5 for s in (summary["python"], summary["java"])) and
    abs(summary["python"]["cumulative_difference_seconds"] -
        summary["java"]["cumulative_difference_seconds"]) < .05)
(args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
raise SystemExit(exit_code)
