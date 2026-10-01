#!/usr/bin/env python3
"""Synthetic fault tests for timing acceptance; these are not measurements."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

tools = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("timing", tools / "review-formal-timing.py")
timing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timing)
# Host event querying was separately exercised against real historical bounds.
timing.host_events = lambda directory, host: True
timing.service_journal = lambda directory, host: True
host = {"stopwatch_elapsed_ticks": 304000000, "stopwatch_frequency": 10000000,
        "host_stopwatch_seconds": 30.4, "wsl_exit_code": 0, "wrapper_error": None,
        "temporary_awake_set_return": 2147483648, "temporary_awake_clear_return": 2147483649}
guest = {"elapsed": {"monotonic": 30.2, "raw": 30.2}, "monitor_exit_code": 0,
         "start": {"boot_id": "test-boot", "timesyncd": "inactive"},
         "end": {"boot_id": "test-boot", "timesyncd": "inactive"}}
run = {"monotonic_seconds": 29.8, "wall_clock_seconds": 29.8,
       "boot_id_start": "test-boot", "boot_id_end": "test-boot",
       "clock_start": {"monotonic": 10.1}, "clock_end": {"monotonic": 39.9},
       "clocksource_start": "tsc", "clocksource_end": "tsc",
       "timesyncd_state_start": "inactive", "timesyncd_state_end": "inactive"}
samples = [{"sample_index": i, "wall": 1000.0 + i*15, "monotonic": 10.0 + i*15,
            "raw": 20.0 + i*15, "boottime": 10.0 + i*15,
            "clocksource": "tsc", "boot_id": "test-boot"} for i in range(3)]
cases = []
with tempfile.TemporaryDirectory(prefix="a2-timing-tests-") as temp:
    root = Path(temp)
    for name in ("healthy", "wall_step", "missing_sample", "active_service", "changed_clocksource",
                 "changed_boot", "host_elapsed_loss", "suspend_gap", "monitor_misses_end", "host_sleep"):
        directory = root / name
        (directory / "timing").mkdir(parents=True)
        (directory / "benchmark").mkdir()
        h, g, r, s = copy.deepcopy((host, guest, run, samples))
        timing.host_events = lambda directory, host: True
        if name == "wall_step":
            s[-1]["wall"] += 2
        elif name == "missing_sample":
            s.pop(1)
        elif name == "active_service":
            r["timesyncd_state_end"] = "active"
        elif name == "changed_clocksource":
            s[1]["clocksource"] = "hyperv_clocksource_tsc_page"
        elif name == "changed_boot":
            s[-1]["boot_id"] = "different-boot"
        elif name == "host_elapsed_loss":
            h["stopwatch_elapsed_ticks"] += 120000000
            h["host_stopwatch_seconds"] += 12
        elif name == "suspend_gap":
            s[-1]["boottime"] += 3
        elif name == "monitor_misses_end":
            r["clock_end"]["monotonic"] = 41
        elif name == "host_sleep":
            timing.host_events = lambda directory, host: False
        for filename, value in (("host-summary.json", h), ("launcher-summary.json", g),
                                ("benchmark/run.json", r)):
            (directory / filename).write_text(json.dumps(value))
        (directory / "timing/samples.jsonl").write_text("\n".join(map(json.dumps,s))+"\n")
        result = timing.review(directory)
        assert (result["status"] == "PASS") == (name == "healthy"), name
        cases.append({"case": name, "status": result["status"],
                      "failed_checks": [k for k,v in result["checks"].items() if not v]})
output = {"role": "synthetic tool tests, not timing evidence", "cases": cases}
(tools.parents[0] / "formal-campaign/tool-self-check/timing-fault-tests.json").write_text(json.dumps(output, indent=2)+"\n")
print(json.dumps(output, indent=2))
