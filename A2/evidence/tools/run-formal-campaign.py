#!/usr/bin/env python3
"""Run the authorized gate and seven measurements, restoring timesyncd in finally.

Each phase stops on an error so its raw evidence can be inspected before retry.
This driver does not choose parameters, change clocks, or edit benchmark results.
"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import statistics
import subprocess
import sys
import time

tools = Path(__file__).resolve().parent
a2 = tools.parents[1]
output = a2 / "evidence/formal-campaign"


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def capture(command):
    result = subprocess.run(command, capture_output=True, timeout=30)
    return {"argv": command, "exit_code": result.returncode,
            "stdout": result.stdout.decode("utf-8-sig", errors="replace"),
            "stderr": result.stderr.decode("utf-8", errors="replace")}


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, tools / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def service(action):
    return capture(["wsl.exe", "--distribution", "Ubuntu-24.04", "--user", "root",
                    "--exec", "systemctl", action, "systemd-timesyncd.service"])


def run_checked(command, logfile):
    with logfile.open("w") as stream:
        subprocess.run(command, stdout=stream, stderr=stream, check=True)


def host_run(script, directory, arguments):
    windows_path = subprocess.check_output(["wslpath", "-w", str(tools / script)], text=True).strip()
    command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
               "-File", windows_path, "-GuestOutput", str(directory), *arguments]
    print("Starting", directory.name, datetime.datetime.now().astimezone().isoformat(), flush=True)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout_bytes, stderr_bytes = process.communicate()
    except BaseException:
        # Interrupt the known guest process first, allowing its own finally cleanup.
        for metadata, field in ((directory / "launcher-summary.json", "pid"),
                                (directory / "command.json", "python_pid")):
            if metadata.exists():
                try:
                    os.kill(json.loads(metadata.read_text())[field], signal.SIGINT)
                except ProcessLookupError:
                    pass
                break
        try:
            process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.communicate(timeout=10)
        raise
    directory.mkdir(exist_ok=True)
    # Windows emits CRLF; JSON is preserved after decoding and newline normalization.
    stdout = stdout_bytes.decode("utf-8-sig").replace("\r\n", "\n")
    (directory / "host-summary.json").write_text(stdout)
    (directory / "wrapper-stderr.log").write_bytes(stderr_bytes)
    save(directory / "wrapper-command.json", {"argv": command, "process_exit_code": process.returncode})
    json.loads(stdout)
    return process.returncode


def interrupt(signum, frame):
    raise InterruptedError(signal.Signals(signum).name)


for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, interrupt)

snapshots = load_tool("capture-isolation-state")
reviewer = load_tool("review-formal-timing")
campaign_id = "a2-formal-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
preflight = json.loads((output / "resumed-preflight.json").read_text())
assert preflight["service_state"] == "active" and preflight["service_enable_state"] == "enabled"
status = {"campaign_id": campaign_id, "status": "PREPARING", "completed_runs": []}
save(output / "campaign.json", status)
stopped = False
try:
    # Direct host/guest alignment replaces the old NTP-offset blocking condition.
    comparison = subprocess.check_output(["wslpath", "-w", str(tools / "compare-host-current-time.ps1")], text=True).strip()
    batches = []
    for attempt in range(12):  # About five minutes, plus at most five for active corrections.
        command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", comparison]
        measured = subprocess.run(command, capture_output=True, timeout=90)
        measured.check_returncode()
        rows = json.loads(measured.stdout.decode("utf-8-sig"))
        offsets = [r["alignment_error_seconds"] for r in rows]
        uncertainty = max(r["practical_uncertainty_seconds"] for r in rows)
        stable = max(offsets)-min(offsets) < max(.25, 2*uncertainty)
        aligned = stable and all(abs(r["alignment_error_seconds"])+r["practical_uncertainty_seconds"] < .5 for r in rows)
        batch = {"argv": command, "exit_code": measured.returncode, "samples": rows,
                 "median_seconds": statistics.median(offsets), "min_seconds": min(offsets),
                 "max_seconds": max(offsets), "variation_seconds": max(offsets)-min(offsets),
                 "max_uncertainty_seconds": uncertainty, "stable": stable, "aligned_below_half_second": aligned,
                 "timesync_status": capture(["timedatectl", "timesync-status"])}
        batches.append(batch)
        save(output / "alignment-observations.json", batches)
        print("Direct alignment", attempt+1, batch["median_seconds"], batch["variation_seconds"], flush=True)
        if aligned or (attempt >= 5 and stable):
            break
    decision = "PRE_SYNC_ALIGNED" if aligned else "PRE_SYNC_FIXED_OFFSET" if stable else "PRE_SYNC_ACTIVE_CORRECTION"
    save(output / "pre-sync-decision.json", {"status": decision, "latest_batch": batch,
        "batch_count": len(batches), "reason": "The authorized timesyncd-off host-referenced elapsed-time gate decides measurement reliability; no NTP configuration or time write."})
    before = snapshots.snapshot()
    save(output / "synchronized-state.json", before)
    assert before["service_state"] == "active" and before["current_clocksource"] == "tsc"
    spec_home = Path.home() / ".local/opt/specjvm2008"
    installed = json.loads((a2 / "evidence/environment/installed-kit-sha256.json").read_text())
    assert json.loads((output / "resumed-kit-check.json").read_text())["reuse_verified_hashes"]
    env = {k: os.environ.get(k) for k in ("JAVA_HOME", "PATH", "CLASSPATH", "JAVA_TOOL_OPTIONS",
        "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "LD_PRELOAD", "LANG", "LC_ALL")}
    environment = {"campaign_id": campaign_id, "invoking_environment": env,
        "spec_home": str(spec_home), "spec_version": (spec_home / "version.txt").read_text(),
        "installed_kit_files_unchanged": len(installed),
        "properties_sha256": {str(p.relative_to(spec_home)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((spec_home / "props").glob("*")) if p.is_file()},
        "commands": [capture(c) for c in (["cat", "/etc/os-release"], ["lscpu", "-J"], ["nproc"], ["free", "-b"])],
        "tool_sha256": {str(p.relative_to(a2)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [a2 / "scripts/run-spec.py", a2 / "scripts/run-formal.sh", tools / "clock-monitor.py",
                      tools / "measure-formal-run.py", tools / "run-host-formal.ps1", tools / "run-host-reference-gate.ps1",
                      tools / "host-reference-probe.py", tools / "HostReferenceClock.java"]}}
    environment["state_before_stop"] = before
    stopped = True  # Restore even if the stop command returns an unexpected status.
    stop = service("stop")
    assert stop["exit_code"] == 0
    after_stop = snapshots.snapshot()
    save(output / "timesync-stop.json", {"at": datetime.datetime.now().astimezone().isoformat(),
         "before": before, "command": stop, "after": after_stop})
    save(output / "after-stop.json", after_stop)
    assert after_stop["service_state"] == "inactive"
    settle_start = time.monotonic()
    time.sleep(75)
    settled = snapshots.snapshot()
    save(output / "settling.json", {"elapsed_monotonic_seconds": time.monotonic()-settle_start, "state": settled})
    assert settled["service_state"] == "inactive" and settled["current_clocksource"] == "tsc"
    assert settled["boot_id"] == preflight["boot_id"]
    gate = output / "final-gate"
    gate_exit = host_run("run-host-reference-gate.ps1", gate,
        ["-Mode", "Probe", "-Seconds", "1800", "-ExpectedService", "inactive"])
    assert gate_exit == 0, "Probe process failure; inspect before retry"
    run_checked([sys.executable, "-B", str(tools / "recalculate-host-reference.py"), str(gate)],
                gate / "recalculation-console.json")
    gate_review = reviewer.review(gate, gate=True)
    assert gate_review["status"] == "PASS", "Gate timing requires inspection before a second attempt"
    status["status"] = "FINAL_TIMING_GATE_PASS"
    save(output / "campaign.json", status)
    environment["gate"] = gate_review
    environment["state_after_gate"] = snapshots.snapshot()
    save(output / "campaign-environment.json", environment)
    print("FINAL_TIMING_GATE_PASS", json.dumps(gate_review), flush=True)

    for kind, count in (("base", 1), ("repeat", 3), ("parameter", 3)):
        for number in range(1, count+1):
            directory = output / f"{kind}-{number}"
            exit_code = host_run("run-host-formal.ps1", directory,
                ["-Kind", kind, "-CampaignId", campaign_id])
            timing = reviewer.review(directory)
            assert timing["status"] == "PASS", f"{directory.name}: timing requires inspection"
            assert exit_code == 0, f"{directory.name}: process failure"
            run = json.loads((directory / "benchmark/run.json").read_text())
            assert len(run["result_paths"]) == 1
            # Correctness and resource checks precede formal publication of this run.
            run_checked([sys.executable, "-B", str(tools / "check-run.py"), str(directory / "benchmark"),
                         run["result_paths"][0], "base" if kind == "base" else "single"],
                        directory / "correctness-console.json")
            run_checked([sys.executable, "-B", str(tools / "preserve-results.py"),
                         str(directory / "benchmark/run.json"), str(a2 / "results" / kind)],
                        directory / "copy-console.json")
            status["completed_runs"].append({"slot": directory.name,
                "run_id": Path(run["result_paths"][0]).name, "timing": "PASS", "correctness": "PASS"})
            status["status"] = "MEASURING"
            save(output / "campaign.json", status)
            print("Accepted", directory.name, run["result_paths"], flush=True)
            if kind == "base":
                environment["formal_environment"] = run["environment"]
                save(output / "campaign-environment.json", environment)
                run_checked([sys.executable, "-B", str(a2 / "scripts/summarize-spec.py"), str(a2 / "results/base")], output / "base-parsed.json")
            if not (kind == "parameter" and number == 3):
                time.sleep(60)
    status["status"] = "MEASUREMENTS_COMPLETE"
except BaseException as error:
    status["status"] = "STOPPED_FOR_INSPECTION"
    status["error"] = f"{type(error).__name__}: {error}"
    raise
finally:
    if stopped:
        restore_command = service("start")
        restored = snapshots.snapshot()
        unchanged = {
            "active": restored["service_state"] == "active",
            "enable_state": restored["service_enable_state"] == preflight["service_enable_state"],
            "clocksource": restored["current_clocksource"] == preflight["current_clocksource"] == "tsc",
            "boot_id": restored["boot_id"] == preflight["boot_id"],
            "kernel": restored["kernel_release"] == preflight["kernel_release"],
            "linux_configs": restored["config_sha256"] == preflight["config_sha256"],
            "windows_config": restored["windows"]["wslconfig_sha256"] == preflight["windows"]["wslconfig_sha256"],
            "windows_time_service": restored["windows"]["windows_time_service"] == preflight["windows"]["windows_time_service"],
            "power_plan": restored["windows"]["active_power_scheme"] == preflight["windows"]["active_power_scheme"]}
        save(output / "restore.json", {"command": restore_command, "state": restored, "checks": unchanged})
        print("TIMESYNCD_RESTORED", json.dumps(unchanged), flush=True)
    save(output / "campaign.json", status)
print(json.dumps(status), flush=True)
