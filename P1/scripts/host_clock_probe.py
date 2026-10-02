#!/usr/bin/env python3
"""Bracket a read-only Windows QPC interval with Linux clock reads."""

import argparse
import json
import os
import selectors
import signal
import subprocess
import sys
import time


POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
BRIDGE = r"""
$ErrorActionPreference = 'Stop'
$p1ClockMarker = 'P1Goal2ClockProbe'
$started = (Get-Process -Id $PID).StartTime.ToUniversalTime().Ticks
[Console]::Out.WriteLine(('ready:{0}:{1}:{2}:{3}' -f [System.Diagnostics.Stopwatch]::Frequency, [System.Diagnostics.Stopwatch]::IsHighResolution, $PID, $started))
[Console]::Out.Flush()
while ($null -ne ($line = [Console]::ReadLine())) {
    if ($line -eq 'quit') { break }
    if ($line -notmatch '^sample:([0-9]+)$') { throw 'unexpected clock request' }
    [Console]::Out.WriteLine(('sample:{0}:{1}:{2}:{3}:{4}' -f $Matches[1], [System.Diagnostics.Stopwatch]::GetTimestamp(), [System.Diagnostics.Stopwatch]::Frequency, [System.Diagnostics.Stopwatch]::IsHighResolution, $PID))
    [Console]::Out.Flush()
}
"""
CLOCKS = {"MONOTONIC": time.CLOCK_MONOTONIC,
          "RAW": time.CLOCK_MONOTONIC_RAW, "REALTIME": time.CLOCK_REALTIME,
          "PROCESS_CPU": time.CLOCK_PROCESS_CPUTIME_ID}


def clocks():
    return {name: time.clock_gettime_ns(clock) for name, clock in CLOCKS.items()}


def line(bridge, timeout=10):
    deadline = time.clock_gettime(time.CLOCK_MONOTONIC_RAW) + timeout
    pending = getattr(bridge, "clock_pending", b"")
    with selectors.DefaultSelector() as selector:
        selector.register(bridge.stdout, selectors.EVENT_READ)
        while b"\n" not in pending:
            remaining = deadline - time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
            if remaining <= 0 or not selector.select(remaining):
                raise ValueError("host clock reply timed out")
            part = os.read(bridge.stdout.fileno(), 4096)
            if not part:
                raise ValueError("host clock bridge closed without a complete reply")
            pending += part
            bridge.clock_pending = pending
            if len(pending) > 4096:
                raise ValueError("host clock reply exceeded the byte limit")
    value, bridge.clock_pending = pending.split(b"\n", 1)
    return value.decode("ascii").strip()


def sample(bridge, sequence, frequency, host_pid, readings):
    before = clocks()
    previous = readings[-1] if readings else None
    row = dict(sequence=sequence, before_ns=before, request=f"sample:{sequence}")
    readings.append(row)
    bridge.stdin.write(f"sample:{sequence}\n".encode())
    bridge.stdin.flush()
    try:
        response = line(bridge)
        row["response"] = response
    finally:
        row["after_ns"] = clocks()
        row["partial_reply"] = getattr(bridge, "clock_pending", b"").decode(errors="replace")
    fields = response.split(":")
    after = row["after_ns"]
    if len(fields) != 6 or fields[0] != "sample" or int(fields[1]) != sequence or \
            int(fields[3]) != frequency or fields[4] != "True" or int(fields[5]) != host_pid:
        raise ValueError("host reply sequence or frequency changed")
    tick = int(fields[2])
    if tick <= 0 or any(after[name] < before[name] for name in CLOCKS) or previous and any(
            before[name] < previous["after_ns"][name] for name in CLOCKS):
        raise ValueError("clock read went backwards")
    if previous and tick < previous["host_tick"]:
        raise ValueError("host QPC counter went backwards")
    row.update(host_tick=tick, frequency_hz=frequency, is_high_resolution=True, host_pid=host_pid)
    return row


def interval(first, last, frequency):
    ticks = last["host_tick"] - first["host_tick"]
    if ticks <= 0 or frequency <= 0:
        raise ValueError("host clock interval must be positive")
    host_s = ticks / frequency
    host_low, host_high = host_s - 2 / frequency, host_s + 2 / frequency
    if host_low <= 0:
        raise ValueError("host interval is below its quantization allowance")
    endpoint_s = [max((reading["after_ns"][name] - reading["before_ns"][name]) / 1e9
                     for name in ("MONOTONIC", "RAW", "REALTIME"))
                  for reading in (first, last)]
    bounds = {}
    for name in ("MONOTONIC", "RAW", "REALTIME"):
        lower = (last["before_ns"][name] - first["after_ns"][name]) / 1e9
        upper = (last["after_ns"][name] - first["before_ns"][name]) / 1e9
        if lower <= 0 or upper < lower:
            raise ValueError("Linux interval has no positive ordered bounds")
        bounds[name] = dict(lower_s=lower, upper_s=upper,
                            host_to_linux_ratio_bounds=[host_low / upper, host_high / lower],
                            linux_to_host_ratio_bounds=[lower / host_high, upper / host_low],
                            bracket_width_fraction=(upper - lower) / host_s)
    usable = max(endpoint_s) <= .02 and all(
        row["bracket_width_fraction"] <= .002 for row in bounds.values())
    raw_bounds = bounds["RAW"]["linux_to_host_ratio_bounds"]
    return dict(host_elapsed_s=host_s, endpoint_bracket_s=endpoint_s,
                host_quantization_allowance_s=2 / frequency,
                linux_interval_bounds=bounds, usable_brackets=usable,
                endpoint_limits_pass=[value <= .02 for value in endpoint_s],
                width_limits_pass={name: row["bracket_width_fraction"] <= .002 for name, row in bounds.items()},
                raw_relative_screen_pass=raw_bounds[0] >= .995 and raw_bounds[1] <= 1.005,
                limits=dict(endpoint_s=.02, relative_bracket_width=.002))


def host_cleanup(pid, started):
    # Inspect only our recorded PID. A reused PID is never stopped.
    command = f"""$ErrorActionPreference = 'Stop'
$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue
if ($null -eq $p) {{ [Console]::Out.WriteLine('absent'); exit 0 }}
$null = $p.Handle
if ($p.StartTime.ToUniversalTime().Ticks -ne {started}) {{ [Console]::Out.WriteLine('pid-reused'); exit 0 }}
Stop-Process -InputObject $p -Force
if (-not $p.WaitForExit(1000)) {{ [Console]::Out.WriteLine('owned-process-still-present'); exit 5 }}
[Console]::Out.WriteLine('stopped-recorded-owned-process')
"""
    check = subprocess.run([POWERSHELL, "-NoLogo", "-NoProfile", "-NonInteractive",
                            "-Command", command], capture_output=True, timeout=5)
    state = check.stdout.decode("ascii").strip()
    if check.returncode or state not in ("absent", "pid-reused", "stopped-recorded-owned-process"):
        raise ValueError("recorded Windows clock PID cleanup could not be verified")
    return dict(command=command, returncode=check.returncode, state=state,
                stderr=check.stderr.decode(errors="replace"))


def run_workload(command, timeout=300):
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
    try:
        stdout, stderr = child.communicate(timeout=timeout)
    except BaseException as error:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
        try:
            stdout, stderr = child.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            stdout, stderr = child.communicate(timeout=1)
        error.workload_raw = dict(pid=child.pid, returncode=child.returncode,
                                  stdout=stdout.decode(), stderr=stderr.decode())
        raise
    return subprocess.CompletedProcess(command, child.returncode,
                                       stdout.decode(), stderr.decode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe")
    parser.add_argument("--cleanup-check", choices=("normal", "error", "timeout", "signal", "cleanup-signal"))
    args = parser.parse_args()
    if not args.probe and not args.cleanup_check:
        parser.error("--probe is required for the two clock intervals")
    def interrupted(signum, frame):
        raise KeyboardInterrupt("clock probe interrupted")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    bridge = subprocess.Popen([POWERSHELL, "-NoLogo", "-NoProfile", "-NonInteractive",
                               "-Command", BRIDGE], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              bufsize=0, start_new_session=True)
    result = dict(complete=False, readings=[], intervals=[],
                  parent_cpu_scope="Python bridge reads only; C workload CPU remains in its original stdout")
    host_pid, started = None, None
    try:
        header_text = line(bridge)
        header = header_text.split(":")
        if len(header) != 5 or header[0] != "ready" or header[2] != "True":
            raise ValueError("host did not report a high-resolution Stopwatch")
        frequency, host_pid, started = int(header[1]), int(header[3]), int(header[4])
        if frequency <= 0 or host_pid <= 0 or started <= 0:
            raise ValueError("invalid host frequency or process ID")
        result.update(host_frequency_hz=frequency, host_pid=host_pid,
                      header=header_text,
                      host_start_utc_ticks=started,
                      bridge_linux_pid=bridge.pid, clock_read_order=list(CLOCKS),
                      host_clock="System.Diagnostics.Stopwatch.GetTimestamp / QPC",
                      host_bridge_source=BRIDGE, handshake=[])
        for sequence in range(5):
            result["handshake"].append(sample(bridge, sequence, frequency, host_pid, result["readings"]))
        if args.cleanup_check:
            result["lifecycle_check"] = args.cleanup_check
            if args.cleanup_check not in ("normal", "cleanup-signal"):
                command = ["/usr/bin/false"] if args.cleanup_check == "error" else [
                    sys.executable, "-B", "-c", "import os,signal,time;print(os.getpid(),flush=True);" +
                    ("os.kill(os.getppid(),signal.SIGTERM);" if args.cleanup_check == "signal" else "") +
                    "time.sleep(30)"]
                try:
                    workload = run_workload(command, timeout=.15 if args.cleanup_check == "timeout" else 300)
                    result["cleanup_workload"] = dict(returncode=workload.returncode, stdout=workload.stdout, stderr=workload.stderr)
                except BaseException as error:
                    result["cleanup_workload"] = error.workload_raw
                    raise
                raise ValueError("intentional failed-workload cleanup check")
        for mode, count, seconds in (() if args.cleanup_check else (("idle", 0, 40), ("work", 8000000000, 0))):
            first = sample(bridge, len(result["readings"]), frequency, host_pid, result["readings"])
            command = ["taskset", "-c", "0", args.probe, mode, str(count), str(seconds)]
            row = dict(mode=mode, command=command, first=first)
            result["intervals"].append(row)
            try:
                workload = run_workload(command)
            except BaseException as error:
                row.update(error.workload_raw)
                raise
            row.update(returncode=workload.returncode, stdout=workload.stdout, stderr=workload.stderr)
            last = sample(bridge, len(result["readings"]), frequency, host_pid, result["readings"])
            row.update(last=last, **interval(first, last, frequency))
            if workload.returncode:
                raise ValueError("the fixed workload failed")
            if not row["usable_brackets"]:
                raise ValueError("host interval brackets exceed the predefined precision limit")
        result["complete"] = not bool(args.cleanup_check)
        result["raw_candidate_feasible"] = all(row["raw_relative_screen_pass"] for row in result["intervals"])
        result["raw_relative_screen_bounds"] = [.995, 1.005]
    except BaseException as error:
        result["error"] = type(error).__name__ + ": " + str(error)
        result["partial_host_reply"] = getattr(bridge, "clock_pending", b"").decode(errors="replace")
        raise
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if args.cleanup_check == "cleanup-signal":
            signal.raise_signal(signal.SIGTERM)
            result["cleanup_signal_ignored"] = True
        if bridge.poll() is None:
            try:
                bridge.stdin.write(b"quit\n")
                bridge.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
        bridge.stdin.close()
        try:
            result["bridge_exit_code"] = bridge.wait(timeout=2)
        except subprocess.TimeoutExpired:
            bridge.kill()
            result["bridge_exit_code"] = bridge.wait(timeout=1)
            result["cleanup_error"] = "host bridge did not exit after its scoped quit request"
        if host_pid is not None:
            try:
                result["host_cleanup"] = host_cleanup(host_pid, started)
            except Exception as error:
                result["cleanup_error"] = str(error)
        else:
            result["host_cleanup"] = dict(state="host PID was not obtained; Windows exit unverified")
        stderr = b""
        with selectors.DefaultSelector() as selector:
            selector.register(bridge.stderr, selectors.EVENT_READ)
            while len(stderr) < 4096 and selector.select(0):
                part = os.read(bridge.stderr.fileno(), 4096 - len(stderr))
                if not part:
                    break
                stderr += part
        result["bridge_stderr"] = stderr.decode(errors="replace")
        result["lifecycle_valid"] = result["bridge_exit_code"] == 0 and not result.get("cleanup_error") and \
            result["host_cleanup"]["state"] in ("absent", "pid-reused", "stopped-recorded-owned-process")
        result["raw_candidate_feasible"] = bool(result["complete"] and result["lifecycle_valid"] and
            len(result["intervals"]) == 2 and all(row.get("raw_relative_screen_pass") is True for row in result["intervals"]))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
    if result["bridge_exit_code"] != 0 or result.get("cleanup_error"):
        raise ValueError("host bridge cleanup failed; inspect its recorded PID")


if __name__ == "__main__":
    main()
