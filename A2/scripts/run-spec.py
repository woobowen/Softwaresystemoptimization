#!/usr/bin/env python3
"""Run one JVM, retaining its command, timestamps, output and result paths.

Usage: SPEC_HOME=... JAVA_HOME=... python3 run-spec.py LOG_DIR [java arguments]
Example java arguments: -jar SPECjvm2008.jar --base
"""
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")


def clocks():
    return {"realtime": time.time(), "monotonic": time.monotonic()}


def clocksource():
    path = Path("/sys/devices/system/clocksource/clocksource0/current_clocksource")
    return path.read_text().strip() if path.exists() else None


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    spec = Path(os.environ["SPEC_HOME"]).expanduser().resolve()
    jdk = Path(os.environ["JAVA_HOME"]).expanduser().resolve()
    command = [str(jdk / "bin/java"), *sys.argv[2:]]
    env = os.environ.copy()
    env["JAVA_HOME"] = str(jdk)
    env["PATH"] = str(jdk / "bin") + os.pathsep + env["PATH"]
    # Refuse concurrent runs and accidental replacement of earlier evidence.
    with (spec / ".a2-run.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output = Path(sys.argv[1]).resolve()
        output.mkdir(parents=True, exist_ok=False)
        before = set((spec / "results").glob("SPECjvm2008.*"))
        record = {
            "command": command,
            "shell_command": shlex.join(command),
            "cwd": str(spec),
            "java_path": command[0],
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "environment": {key: env.get(key) for key in (
                "JAVA_HOME", "CLASSPATH", "JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS",
                "JDK_JAVA_OPTIONS", "PATH", "LANG", "LC_ALL", "TZ",
                "LD_PRELOAD", "LD_LIBRARY_PATH", "DISPLAY", "FONTCONFIG_PATH")},
            "java_on_path": subprocess.check_output(
                ["which", "-a", "java"], env=env, text=True).splitlines(),
            "start": now(),
            "end": None,
            "exit_code": None,
            "stdout_path": str(output / "stdout.log"),
            "stderr_path": str(output / "stderr.log"),
            "results_root": str(spec / "results"),
        }
        metadata = output / "run.json"
        metadata.write_text(json.dumps(record, indent=2) + "\n")
        print(f"{record['start']} {record['shell_command']}", flush=True)
        # Real files cannot fill a PIPE buffer, even while neither log is read.
        with (output / "stdout.log").open("wb") as stdout, \
                (output / "stderr.log").open("wb") as stderr:
            record["clocksource_start"] = clocksource()
            record["clock_start"] = clocks()
            try:
                process = subprocess.Popen(command, cwd=spec, env=env,
                                           stdout=stdout, stderr=stderr,
                                           start_new_session=True)
            except OSError as error:
                record["launch_error"] = str(error)
                record["exit_code"] = 127
            else:
                record["pid"] = process.pid
                metadata.write_text(json.dumps(record, indent=2) + "\n")

                def forward_signal(signum, frame):
                    record["signal_received"] = signal.Signals(signum).name
                    # Include startup JVMs; the separate session avoids double Ctrl+C.
                    try:
                        os.killpg(process.pid, signum)
                    except ProcessLookupError:
                        pass

                signal.signal(signal.SIGINT, forward_signal)
                signal.signal(signal.SIGTERM, forward_signal)
                record["exit_code"] = process.wait()
            record["clock_end"] = clocks()
            record["clocksource_end"] = clocksource()
        record["end"] = now()
        for clock, field in (("realtime", "wall_clock_seconds"),
                             ("monotonic", "monotonic_seconds")):
            record[field] = round(record["clock_end"][clock] - record["clock_start"][clock], 6)
        # Keep the historical field for readers of earlier run records.
        record["wall_seconds"] = record["monotonic_seconds"]
        record["result_paths"] = sorted(str(p) for p in
            set((spec / "results").glob("SPECjvm2008.*")) - before)
        metadata.write_text(json.dumps(record, indent=2) + "\n")
        print(f"{record['end']} exit={record['exit_code']}", flush=True)
        code = record["exit_code"]
        sys.exit(code if code >= 0 else 128 - code)


if __name__ == "__main__":
    main()
