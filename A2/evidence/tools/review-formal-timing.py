#!/usr/bin/env python3
"""Review host/guest raw timing before any SPEC score is read."""
import base64
import datetime
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys


def host_events(directory, host):
    query = """$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
try {
    $s=[DateTimeOffset]::Parse('START').LocalDateTime
    $e=[DateTimeOffset]::Parse('END').LocalDateTime
    $events=@(Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$s; EndTime=$e;
        ProviderName=@('Microsoft-Windows-Kernel-Power','Microsoft-Windows-Power-Troubleshooter')})
    $selected=@($events | Where-Object {$_.Id -in @(1,41,42,107,506,507)} | ForEach-Object {
        [pscustomobject]@{time=$_.TimeCreated.ToString('o'); id=$_.Id; provider=$_.ProviderName}})
    @{status='QuerySucceeded'; events=$selected} | ConvertTo-Json -Depth 4
} catch {
    if ($_.FullyQualifiedErrorId -like 'NoMatchingEventsFound*') {
        @{status='NoMatchingEvents'; events=@()} | ConvertTo-Json
    } else { throw }
}
""".replace("START", host["host_start_utc"]).replace("END", host["host_end_utc"])
    command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand",
               base64.b64encode(query.encode("utf-16-le")).decode()]
    result = subprocess.run(command, capture_output=True, timeout=30)
    evidence = {"query": query, "exit_code": result.returncode,
                "stdout": result.stdout.decode("utf-8-sig"), "stderr": result.stderr.decode("utf-8", errors="replace")}
    if result.returncode == 0:
        evidence["parsed"] = json.loads(evidence["stdout"])
    (directory / "host-event-check.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return result.returncode == 0 and not evidence["parsed"]["events"]


def service_journal(directory, host):
    # Use guest realtime bounds: host and guest epochs can have a fixed offset.
    if (directory / "launcher-summary.json").exists():
        guest = json.loads((directory / "launcher-summary.json").read_text())
        start, end = guest["start"]["realtime"], guest["end"]["realtime"]
    else:
        rows = [json.loads(line) for line in (directory / "samples.jsonl").read_text().splitlines()]
        start, end = rows[0]["python_time"], rows[-1]["python_time"]
    command = ["journalctl", "-u", "systemd-timesyncd.service", "--since", f"@{start:.6f}",
               "--until", f"@{end:.6f}", "--no-pager", "--output=json", "--quiet"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    (directory / "service-journal.json").write_text(json.dumps({"argv": command,
        "exit_code": result.returncode, "stderr": result.stderr, "entries": rows}, indent=2) + "\n")
    return result.returncode == 0 and not rows


def review(directory, gate=False):
    host = json.loads((directory / "host-summary.json").read_text())
    no_sleep = host_events(directory, host)
    stopwatch = host["stopwatch_elapsed_ticks"] / host["stopwatch_frequency"]
    checks = {"host_ticks_consistent": abs(stopwatch - host["host_stopwatch_seconds"]) < .000001,
              "host_exit_zero": host["wsl_exit_code"] == 0 and not host["wrapper_error"],
              "host_awake_requested_and_cleared": host["temporary_awake_set_return"] != 0 and host["temporary_awake_clear_return"] != 0,
              "no_host_sleep_events": no_sleep}
    checks["no_timesyncd_activity_during_interval"] = service_journal(directory, host)
    if gate:
        guest = json.loads((directory / "guest-summary.json").read_text())
        independent = json.loads((directory / "independent-calculation.json").read_text())
        mono = guest["elapsed_seconds"]["python_monotonic"]
        raw = guest["elapsed_seconds"]["python_monotonic_raw"]
        drift = guest["python_wall_minus_monotonic_seconds"]
        steps = independent["intervals"]
        largest = max(abs(v[k]) for v in steps.values() for k in ("min_difference_seconds", "max_difference_seconds"))
        checks.update(raw_recalculation=independent["all_checks_pass"],
                      guest_integrity=guest["probe_integrity_ok"],
                      no_steps_over_50ms=all(sum(v["counts"]["0.05"].values()) == 0 for v in steps.values()),
                      service_inactive=guest["service_before"] == guest["service_after"] == "inactive")
        clock_values = guest["clocksource_values"]
        boots = [guest["boot_id_before"], guest["boot_id_after"]]
        overhead = guest["entry_to_first_sample_seconds"] + guest["last_sample_to_summary_seconds"]
    else:
        guest = json.loads((directory / "launcher-summary.json").read_text())
        run = json.loads((directory / "benchmark/run.json").read_text())
        samples = [json.loads(line, parse_float=Decimal) for line in (directory / "timing/samples.jsonl").read_text().splitlines()]
        elapsed = {key: float(samples[-1][key] - samples[0][key]) for key in ("wall", "monotonic", "raw", "boottime")}
        differences = [float((b["wall"]-a["wall"])-(b["monotonic"]-a["monotonic"])) for a,b in zip(samples,samples[1:])]
        mono, raw = guest["elapsed"]["monotonic"], guest["elapsed"]["raw"]
        drift = elapsed["wall"] - elapsed["monotonic"]
        largest = max(map(abs,differences), default=0)
        clock_values = sorted({s["clocksource"] for s in samples})
        boots = sorted({s["boot_id"] for s in samples} | {guest["start"]["boot_id"], guest["end"]["boot_id"]})
        overhead = mono - run["monotonic_seconds"]
        checks.update(monitor_exit_zero=guest["monitor_exit_code"] == 0,
            no_periodic_corrections_over_50ms=sum(abs(d) > .05 for d in differences) == 0,
            runner_boot_unchanged=run["boot_id_start"] == run["boot_id_end"] == boots[0],
            sample_indices_contiguous=[s["sample_index"] for s in samples] == list(range(len(samples))),
            sample_intervals_complete=len(samples)>1 and all(0 < float(b["monotonic"]-a["monotonic"]) < 20 for a,b in zip(samples,samples[1:])),
            monitor_encloses_benchmark=float(samples[0]["monotonic"]) <= run["clock_start"]["monotonic"] < run["clock_end"]["monotonic"] <= float(samples[-1]["monotonic"]),
            runner_clock_drift_small=abs(run["wall_clock_seconds"]-run["monotonic_seconds"]) < .5,
            service_inactive=guest["start"]["timesyncd"] == guest["end"]["timesyncd"] == run["timesyncd_state_start"] == run["timesyncd_state_end"] == "inactive",
            runner_clocks_tsc=run["clocksource_start"] == run["clocksource_end"] == "tsc",
            no_suspend_gap=abs(elapsed["boottime"]-elapsed["monotonic"]) < .5)
    checks.update(host_guest_elapsed_agree=0 <= stopwatch-mono < 2,
                  host_raw_elapsed_agree=abs(stopwatch-raw) < 2,
                  wall_mono_drift_small=abs(drift) < .5,
                  no_discrete_steps=largest < .5,
                  clocksource_tsc=clock_values == ["tsc"], boot_id_unchanged=len(set(boots)) == 1)
    result = {"run": directory.name, "host_seconds": stopwatch, "guest_monotonic_seconds": mono,
              "guest_raw_seconds": raw, "host_minus_guest_seconds": stopwatch-mono,
              "wall_minus_monotonic_seconds": drift, "largest_step_seconds": largest,
              "guest_preparation_cleanup_seconds": overhead, "clocksource": clock_values,
              "boot_id": boots[0], "timesyncd": "inactive" if checks["service_inactive"] else "unexpected",
              "checks": checks, "status": "PASS" if all(checks.values()) else "REVIEW_REQUIRED",
              "thresholds_are_internal_not_spec_rules": True}
    (directory / "timing-review.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    result = review(Path(sys.argv[1]), "--gate" in sys.argv[2:])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "PASS" else 1)
