#!/usr/bin/env python3
"""Record low-frequency timing samples until SIGTERM, without profiling SPEC."""
import argparse
import datetime
import json
from pathlib import Path
import signal
import threading
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output", type=Path)
parser.add_argument("--interval", type=float, default=15)
parser.add_argument("--seconds", type=float, help="Bounded self-check only; normally stop with SIGTERM")
parser.add_argument("--expected-clocksource", default="tsc")
args = parser.parse_args()
if not 10 <= args.interval <= 30:
    parser.error("sampling interval must be between 10 and 30 seconds")
timing = Path(__file__).resolve().parents[1]
if not args.output.resolve().is_relative_to(timing):
    parser.error("output must be under A2/evidence")
args.output.mkdir(parents=True, exist_ok=False)
clocksource = Path("/sys/devices/system/clocksource/clocksource0/current_clocksource")
boot_id = Path("/proc/sys/kernel/random/boot_id")
stop = threading.Event()
for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, lambda *_: stop.set())
samples = []
cpu_start = time.process_time()
with (args.output / "samples.jsonl").open("w") as log:
    while True:
        sample = {"sample_index": len(samples), "wall": time.time(), "monotonic": time.monotonic(),
                  "raw": time.clock_gettime(time.CLOCK_MONOTONIC_RAW),
                  "boottime": time.clock_gettime(time.CLOCK_BOOTTIME),
                  "boot_id": boot_id.read_text().strip(),
                  "clocksource": clocksource.read_text().strip()}
        if samples:
            sample["wall_delta"] = sample["wall"] - samples[-1]["wall"]
            sample["monotonic_delta"] = sample["monotonic"] - samples[-1]["monotonic"]
            sample["interval_difference"] = sample["wall_delta"] - sample["monotonic_delta"]
            sample["cumulative_difference"] = (sample["wall"] - samples[0]["wall"] -
                                                sample["monotonic"] + samples[0]["monotonic"])
        samples.append(sample)
        log.write(json.dumps(sample) + "\n")
        log.flush()
        if stop.is_set() or (args.seconds and sample["monotonic"] - samples[0]["monotonic"] >= args.seconds):
            break
        stop.wait(args.interval)

wall = samples[-1]["wall"] - samples[0]["wall"]
mono = samples[-1]["monotonic"] - samples[0]["monotonic"]
steps = [s["interval_difference"] for s in samples[1:]]
summary = {"ended_at": datetime.datetime.now().astimezone().isoformat(),
    "sample_count": len(samples), "interval_seconds": args.interval,
    "wall_seconds": wall, "monotonic_seconds": mono,
    "raw_seconds": samples[-1]["raw"] - samples[0]["raw"],
    "boottime_seconds": samples[-1]["boottime"] - samples[0]["boottime"],
    "boot_id_values": sorted({s["boot_id"] for s in samples}),
    "cumulative_difference_seconds": wall - mono,
    "min_interval_difference_seconds": min(steps, default=0),
    "max_interval_difference_seconds": max(steps, default=0),
    "forward_adjustments_over_50ms": sum(d > .05 for d in steps),
    "backward_adjustments_over_50ms": sum(d < -.05 for d in steps),
    "backward_wall_intervals": sum(s["wall_delta"] < 0 for s in samples[1:]),
    "clocksource_values": sorted({s["clocksource"] for s in samples}),
    "process_cpu_seconds": time.process_time() - cpu_start}
summary["timing_healthy"] = (len(samples) >= 2 and abs(wall - mono) < 2 and
    all(abs(d) < .5 for d in steps) and summary["backward_wall_intervals"] == 0 and
    len(summary["boot_id_values"]) == 1 and
    summary["clocksource_values"] == [args.expected_clocksource])
(args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
