#!/usr/bin/env python3
"""Exercise the real runner without using SPEC as a stress-test fixture."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


runner = Path(__file__).resolve().parents[2] / "scripts/run-spec.py"
results = []
with tempfile.TemporaryDirectory(prefix="a2-runner-test-") as directory:
    root = Path(directory)
    (root / "jdk/bin").mkdir(parents=True)
    (root / "spec/results").mkdir(parents=True)
    java = root / "jdk/bin/java"
    java.write_text('''#!/usr/bin/env python3
import os, signal, sys, time
if sys.argv[1] == "flood":
    for i in range(300):
        os.write(1, b"O" * 1024)
        os.write(2, b"E" * 1024)
    os.write(1, b"\\nSTDOUT-END\\n")
    os.write(2, b"\\nSTDERR-END\\n")
elif sys.argv[1] == "exit7":
    sys.exit(7)
else:
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    os.write(1, b"READY\\n")
    while True:
        time.sleep(0.1)
''')
    java.chmod(0o755)
    env = dict(os.environ, JAVA_HOME=str(root / "jdk"), SPEC_HOME=str(root / "spec"))

    def launch(name, mode):
        command = [sys.executable, str(runner), str(root / name), mode]
        with (root / (name + ".driver.log")).open("wb") as log:
            return subprocess.Popen(command, env=env, stdout=log, stderr=log)

    for mode, expected in (("flood", 0), ("exit7", 7)):
        process = launch(mode, mode)
        assert process.wait(timeout=10) == expected
        record = json.loads((root / mode / "run.json").read_text())
        assert record["exit_code"] == expected and record["end"]
        for clock, field in (("realtime", "wall_clock_seconds"),
                             ("monotonic", "monotonic_seconds")):
            elapsed = record["clock_end"][clock] - record["clock_start"][clock]
            assert abs(record[field] - elapsed) < 0.000001
        assert record["wall_seconds"] == record["monotonic_seconds"]
        assert record["clocksource_start"] and record["clocksource_end"]
        case = {"case": mode, "runner_exit": process.returncode, "java_exit": record["exit_code"]}
        if mode == "flood":
            for stream, byte in (("stdout", b"O"), ("stderr", b"E")):
                data = (root / mode / (stream + ".log")).read_bytes()
                assert data == byte * (300 * 1024) + b"\n" + stream.upper().encode() + b"-END\n"
                case[stream] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "tail_complete": True}
        results.append(case)

    for sig in (signal.SIGINT, signal.SIGTERM):
        name = sig.name.lower()
        process = launch(name, "sleep")
        deadline = time.monotonic() + 10
        ready = root / name / "stdout.log"
        while not ready.exists() or b"READY" not in ready.read_bytes():
            assert process.poll() is None and time.monotonic() < deadline
            time.sleep(0.05)
        blocked = launch(name + "-concurrent", "flood")
        assert blocked.wait(timeout=10) != 0
        assert not (root / (name + "-concurrent")).exists()
        process.send_signal(sig)
        assert process.wait(timeout=10) == 128 + sig
        record = json.loads((root / name / "run.json").read_text())
        assert record["exit_code"] == -sig and record["signal_received"] == sig.name
        assert record["end"]
        results.append({"case": name, "runner_exit": process.returncode, "java_exit": record["exit_code"], "concurrent_run_rejected": True})

    replaced = launch("flood", "flood")
    assert replaced.wait(timeout=10) != 0
    results.append({"case": "existing_output", "overwrite_rejected": True})

    java.unlink()
    failed = launch("missing_java", "flood")
    assert failed.wait(timeout=10) == 127
    record = json.loads((root / "missing_java/run.json").read_text())
    assert record["exit_code"] == 127 and record["launch_error"] and record["end"]
    results.append({"case": "missing_java", "runner_exit": 127, "metadata_saved": True})

output = {"runner_sha256": hashlib.sha256(runner.read_bytes()).hexdigest(), "tests": results}
(runner.parents[1] / "evidence/final/runner-tests-stage5.json").write_text(
    json.dumps(output, indent=2) + "\n")
print(json.dumps(output, indent=2))
