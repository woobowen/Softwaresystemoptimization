#!/usr/bin/env python3
"""Enclose one runner invocation with the existing low-frequency clock monitor."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

tools = Path(__file__).resolve().parent
a2 = tools.parents[1]
output, kind, campaign_id = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
assert kind in ("base", "repeat", "parameter")
output.mkdir(parents=True, exist_ok=False)


def state():
    return {
        "realtime": time.time(), "monotonic": time.monotonic(),
        "raw": time.clock_gettime(time.CLOCK_MONOTONIC_RAW),
        "boottime": time.clock_gettime(time.CLOCK_BOOTTIME),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "clocksource": Path("/sys/devices/system/clocksource/clocksource0/current_clocksource").read_text().strip(),
        "timesyncd": subprocess.run(["systemctl", "is-active", "systemd-timesyncd.service"],
                                   text=True, capture_output=True, timeout=10).stdout.strip()}


start = state()
assert start["clocksource"] == "tsc" and start["timesyncd"] == "inactive"
java_args = (["-XX:+UseSerialGC"] if kind == "parameter" else [])
java_args += ["-jar", "SPECjvm2008.jar", "--base" if kind == "base" else "compress"]
command = ["bash", str(a2 / "scripts/run-formal.sh"), str(output / "benchmark"), *java_args]
record = {"campaign_id": campaign_id, "kind": kind, "start": start, "argv": command,
          "monitor_interval_seconds": 15, "pid": os.getpid()}
(output / "launcher-summary.json").write_text(json.dumps(record, indent=2) + "\n")
monitor = runner = None


def interrupt(signum, frame):
    if runner and runner.poll() is None:
        runner.send_signal(signum)
    raise InterruptedError(signal.Signals(signum).name)


for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, interrupt)
try:
    with (output / "monitor-console.log").open("w") as log:
        monitor = subprocess.Popen([sys.executable, "-B", str(tools / "clock-monitor.py"),
                                    str(output / "timing"), "--interval", "15"], stdout=log, stderr=log)
        deadline = time.monotonic() + 10
        while not (output / "timing/samples.jsonl").exists() or (output / "timing/samples.jsonl").stat().st_size == 0:
            assert monitor.poll() is None and time.monotonic() < deadline, "Monitor did not start"
            time.sleep(.05)
        with (output / "runner-console.log").open("w") as console:
            runner = subprocess.Popen(command, env=dict(os.environ, A2_CAMPAIGN_ID=campaign_id),
                                      stdout=console, stderr=console)
            record["runner_pid"] = runner.pid
            record["runner_exit_code"] = runner.wait()
finally:
    if runner and runner.poll() is None:
        runner.terminate()
        runner.wait(timeout=60)
    if monitor:
        if monitor.poll() is None:
            monitor.terminate()
        record["monitor_exit_code"] = monitor.wait(timeout=10)
    record["end"] = state()
    record["elapsed"] = {key: record["end"][key] - start[key]
                         for key in ("realtime", "monotonic", "raw", "boottime")}
    (output / "launcher-summary.json").write_text(json.dumps(record, indent=2) + "\n")
sys.exit(record["runner_exit_code"] or record["monitor_exit_code"])
