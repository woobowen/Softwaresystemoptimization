#!/usr/bin/env python3
"""Independently derive elapsed times and jumps from raw JSONL and host ticks.

This file imports no probe code. Decimal parsing avoids binary-float subtraction
of the stored epoch seconds. A 1 microsecond comparison tolerance covers their
original float serialization; Java and host tick differences remain integer based.
"""
from decimal import Decimal
import datetime
import hashlib
import json
from pathlib import Path
import sys


def calculate(directory):
    raw = (directory / "samples.jsonl").read_bytes()
    rows = [json.loads(line, parse_float=Decimal) for line in raw.splitlines()]
    host = json.loads((directory / "host-summary.json").read_text(), parse_float=Decimal)
    guest = json.loads((directory / "guest-summary.json").read_text(), parse_float=Decimal)
    jumps = json.loads((directory / "jumps.json").read_text(), parse_float=Decimal)
    scales = {"python_time": 1, "python_monotonic": 1, "python_monotonic_raw": 1,
              "python_boottime": 1, "java_currentTimeMillis": 1000, "java_nanoTime": 1000000000}
    elapsed = {key: (Decimal(rows[-1][key]) - Decimal(rows[0][key])) / scale
               for key, scale in scales.items()}
    stopwatch = Decimal(host["stopwatch_elapsed_ticks"]) / host["stopwatch_frequency"]
    host_wall = Decimal(str((datetime.datetime.fromisoformat(host["host_end_utc"]) -
                             datetime.datetime.fromisoformat(host["host_start_utc"])).total_seconds()))
    checks = {"sample_indices_contiguous": [r["sample_index"] for r in rows] == list(range(len(rows))),
              "sample_count_matches": len(rows) == guest["sample_count"],
              "summary_elapsed_matches": all(abs(elapsed[k] - guest["elapsed_seconds"][k]) < Decimal('0.000001') for k in scales),
              "host_ticks_match_seconds": abs(stopwatch - host["host_stopwatch_seconds"]) < Decimal('0.0000002'),
              "host_dates_match_wall_seconds": abs(host_wall - host["host_wall_seconds"]) < Decimal('0.000002'),
              "clocksource_all_tsc": all(r["clocksource"] == "tsc" for r in rows),
              "monotonic_target_reached": elapsed["python_monotonic"] >= guest["requested_seconds"],
              "processes_succeeded": host["wsl_exit_code"] == guest["java_exit_code"] == 0,
              "boot_id_unchanged": guest["boot_id_before"] == guest["boot_id_after"],
              "guest_integrity_reported": guest["probe_integrity_ok"]}
    interval_results = {}
    for name, wall, mono, wall_scale, mono_scale, stored in (
        ("python", "python_time", "python_monotonic", 1, 1, "python_wall_minus_monotonic_seconds"),
        ("java", "java_currentTimeMillis", "java_nanoTime", 1000, 1000000000, "java_wall_minus_nano_seconds")):
        wall_deltas = [(Decimal(b[wall]) - Decimal(a[wall])) / wall_scale for a, b in zip(rows, rows[1:])]
        mono_deltas = [(Decimal(b[mono]) - Decimal(a[mono])) / mono_scale for a, b in zip(rows, rows[1:])]
        differences = [w - m for w, m in zip(wall_deltas, mono_deltas)]
        counts = {str(t): {"forward": sum(d > t for d in differences), "backward": sum(d < -t for d in differences)}
                  for t in (Decimal('0.05'), Decimal('0.5'), Decimal('1.0'))}
        checks[name + "_intervals_match"] = all(abs(d - r["interval"][stored]) < Decimal('0.000001')
                                                for d, r in zip(differences, rows[1:]))
        checks[name + "_jump_counts_match"] = counts == jumps[name]["counts"]
        checks[name + "_elapsed_positive"] = all(m > 0 for m in mono_deltas)
        checks[name + "_jump_events_match"] = [r["sample_index"] for r,d in zip(rows[1:],differences) if abs(d)>Decimal('0.05')] == [r["sample_index"] for r in jumps[name]["events_over_50ms"]]
        interval_results[name] = {"counts": counts, "min_difference_seconds": min(differences),
            "max_difference_seconds": max(differences), "backward_wall_intervals": sum(w < 0 for w in wall_deltas),
            "max_monotonic_interval_seconds": max(mono_deltas)}
    result = {"directory": directory.name, "method": "Decimal raw endpoint and interval subtraction; host ElapsedTicks/Frequency",
              "samples_sha256": hashlib.sha256(raw).hexdigest(), "sample_count": len(rows),
              "host_stopwatch_seconds": stopwatch, "host_wall_seconds": host_wall,
              "enclosing_counter_seconds": Decimal(host["enclosing_counter_end"] - host["enclosing_counter_start"]) / host["stopwatch_frequency"],
              "elapsed_seconds": elapsed,
              "host_minus_guest_seconds": {k: stopwatch - v for k, v in elapsed.items()},
              "wall_minus_monotonic_seconds": elapsed["python_time"] - elapsed["python_monotonic"],
              "java_wall_minus_nano_seconds": elapsed["java_currentTimeMillis"] - elapsed["java_nanoTime"],
              "intervals": interval_results, "checks": checks, "all_checks_pass": all(checks.values())}
    (directory / "independent-calculation.json").write_text(
        json.dumps(result, indent=2, default=lambda v: float(v)) + "\n")
    return result


if __name__ == "__main__":
    results = [calculate(Path(arg)) for arg in sys.argv[1:]]
    print(json.dumps(results, indent=2, default=lambda v: float(v)))
    raise SystemExit(0 if results and all(r["all_checks_pass"] for r in results) else 1)
