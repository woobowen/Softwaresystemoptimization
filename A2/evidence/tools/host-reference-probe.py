#!/usr/bin/env python3
"""Sample guest clocks together, under an enclosing Windows Stopwatch."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import time


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def service_state(path):
    result = subprocess.run(
        ["systemctl", "is-active", "systemd-timesyncd.service"],
        capture_output=True, text=True, timeout=10)
    path.write_text("$ systemctl is-active systemd-timesyncd.service\n" +
                    result.stdout + result.stderr + f"exit_code={result.returncode}\n")
    return result.stdout.strip()


def main():
    entry_monotonic = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--jdk", type=Path,
                        default=Path.home() / ".local/opt/java-se-7u75-ri")
    parser.add_argument("--expected-service", choices=["active", "inactive"], required=True)
    args = parser.parse_args()
    if args.seconds < 1:
        parser.error("seconds must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    clock_path = Path("/sys/devices/system/clocksource/clocksource0/current_clocksource")
    boot_path = Path("/proc/sys/kernel/random/boot_id")
    boot_before = boot_path.read_text().strip()
    state_before = service_state(args.output / "service-state-before.txt")
    if state_before != args.expected_service or clock_path.read_text().strip() != "tsc":
        raise RuntimeError("Unexpected initial service state or clocksource")
    source = Path(__file__).with_name("HostReferenceClock.java")
    command = {"python_argv": [sys.executable, *sys.argv], "python_pid": os.getpid(),
               "jdk": str(args.jdk), "expected_service": args.expected_service,
               "target_seconds": args.seconds, "termination_clock": "CLOCK_MONOTONIC",
               "sampling_seconds": 1, "source_sha256": {
                   p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (Path(__file__), source,
                             Path(__file__).with_name("run-host-reference-gate.ps1"))},
               "java_option_environment": {k: os.environ.get(k) for k in
                   ("JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS")}}
    samples = []
    with tempfile.TemporaryDirectory(prefix="a2-host-clock-") as build:
        compile_command = [str(args.jdk / "bin/javac"), "-d", build, str(source)]
        compiled = subprocess.run(compile_command, capture_output=True, text=True)
        command["compile"] = {"argv": compile_command, "exit_code": compiled.returncode,
                              "stdout": compiled.stdout, "stderr": compiled.stderr}
        write_json(args.output / "command.json", command)
        compiled.check_returncode()
        java_command = [str(args.jdk / "bin/java"), "-cp", build, "HostReferenceClock"]
        with (args.output / "java-stderr.log").open("w") as err, \
                (args.output / "samples.jsonl").open("w") as log:
            child = subprocess.Popen(java_command, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=err, text=True, bufsize=1)
            command.update(java_argv=java_command, java_pid=child.pid)
            write_json(args.output / "command.json", command)
            selector = selectors.DefaultSelector()
            selector.register(child.stdout, selectors.EVENT_READ)
            try:
                if not selector.select(timeout=10) or child.stdout.readline().strip() != "READY":
                    raise RuntimeError("Java did not become ready")
                while True:
                    index = len(samples)
                    begin = time.monotonic()
                    # Keep the requested Python APIs visible in raw evidence.
                    sample = {"sample_index": index, "python_time": time.time(),
                              "python_monotonic": time.monotonic(),
                              "python_monotonic_raw": time.clock_gettime(time.CLOCK_MONOTONIC_RAW),
                              "python_boottime": time.clock_gettime(time.CLOCK_BOOTTIME)}
                    child.stdin.write(str(index) + "\n")
                    child.stdin.flush()
                    if not selector.select(timeout=10):
                        raise RuntimeError("Java sample response timed out")
                    java_index, wall, nano = map(int, child.stdout.readline().split())
                    if java_index != index:
                        raise RuntimeError("Java/Python sample indices differ")
                    sample.update(java_currentTimeMillis=wall, java_nanoTime=nano,
                                  request_roundtrip_seconds=time.monotonic() - begin,
                                  clocksource=clock_path.read_text().strip(),
                                  timestamp=datetime.datetime.fromtimestamp(
                                      sample["python_time"], datetime.timezone.utc).isoformat())
                    if samples:
                        previous = samples[-1]
                        py_wall = sample["python_time"] - previous["python_time"]
                        py_mono = sample["python_monotonic"] - previous["python_monotonic"]
                        java_wall = (wall - previous["java_currentTimeMillis"]) / 1000
                        java_nano = (nano - previous["java_nanoTime"]) / 1e9
                        sample["interval"] = {
                            "python_wall_seconds": py_wall, "python_monotonic_seconds": py_mono,
                            "python_wall_minus_monotonic_seconds": py_wall - py_mono,
                            "java_wall_seconds": java_wall, "java_nano_seconds": java_nano,
                            "java_wall_minus_nano_seconds": java_wall - java_nano}
                    samples.append(sample)
                    log.write(json.dumps(sample) + "\n")
                    log.flush()
                    elapsed = sample["python_monotonic"] - samples[0]["python_monotonic"]
                    if elapsed >= args.seconds:
                        break
                    deadline = samples[0]["python_monotonic"] + min(index + 1, args.seconds)
                    time.sleep(max(0, deadline - time.monotonic()))
                child.stdin.close()
                java_exit = child.wait(timeout=10)
            finally:
                selector.close()
                if child.poll() is None:
                    child.kill()
                    child.wait()
    state_after = service_state(args.output / "service-state-after.txt")
    scales = {"python_time": 1, "python_monotonic": 1, "python_monotonic_raw": 1,
              "python_boottime": 1, "java_currentTimeMillis": 1000, "java_nanoTime": 1e9}
    elapsed = {k: (samples[-1][k] - samples[0][k]) / scale for k, scale in scales.items()}
    jumps = {}
    for language, key in (("python", "python_wall_minus_monotonic_seconds"),
                          ("java", "java_wall_minus_nano_seconds")):
        diffs = [s["interval"][key] for s in samples[1:]]
        jumps[language] = {"min_difference_seconds": min(diffs),
                           "max_difference_seconds": max(diffs),
                           "counts": {str(t): {"forward": sum(d > t for d in diffs),
                                               "backward": sum(d < -t for d in diffs)}
                                      for t in (0.05, 0.5, 1.0)},
                           "events_over_50ms": [{"sample_index": s["sample_index"],
                               "difference_seconds": s["interval"][key]}
                               for s in samples[1:] if abs(s["interval"][key]) > 0.05]}
    write_json(args.output / "jumps.json", jumps)
    summary = {"sample_count": len(samples), "requested_seconds": args.seconds,
               "elapsed_seconds": elapsed, "java_exit_code": java_exit,
               "python_pid": os.getpid(), "java_pid": child.pid,
               "boot_id_before": boot_before, "boot_id_after": boot_path.read_text().strip(),
               "clocksource_values": sorted({s["clocksource"] for s in samples}),
               "service_before": state_before, "service_after": state_after,
               "first_timestamp": samples[0]["timestamp"], "last_timestamp": samples[-1]["timestamp"],
               "entry_to_first_sample_seconds": samples[0]["python_monotonic"] - entry_monotonic,
               "last_sample_to_summary_seconds": time.monotonic() - samples[-1]["python_monotonic"],
               "max_request_roundtrip_seconds": max(s["request_roundtrip_seconds"] for s in samples),
               "max_monotonic_interval_seconds": max(s["interval"]["python_monotonic_seconds"]
                                                      for s in samples[1:]),
               "python_wall_minus_monotonic_seconds": elapsed["python_time"] - elapsed["python_monotonic"],
               "java_wall_minus_nano_seconds": elapsed["java_currentTimeMillis"] - elapsed["java_nanoTime"]}
    summary["probe_integrity_ok"] = (java_exit == 0 and
        summary["clocksource_values"] == ["tsc"] and
        summary["boot_id_before"] == summary["boot_id_after"] and
        state_before == state_after == args.expected_service and
        elapsed["python_monotonic"] >= args.seconds)
    write_json(args.output / "guest-summary.json", summary)
    return 0 if summary["probe_integrity_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
