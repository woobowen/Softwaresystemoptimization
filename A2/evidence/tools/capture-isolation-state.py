#!/usr/bin/env python3
"""Read-only state snapshot for the timesyncd isolation experiment."""
import base64
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def capture(argv):
    result = subprocess.run(argv, capture_output=True, timeout=30)
    def decode(data):
        return data.decode("utf-16-le" if b"\0" in data else "utf-8", errors="replace")
    return {"argv": argv, "exit_code": result.returncode,
            "stdout": decode(result.stdout), "stderr": decode(result.stderr)}


def snapshot():
    initial_service = capture(["systemctl", "is-active", "systemd-timesyncd.service"])
    paths = [Path("/etc/systemd/timesyncd.conf"), Path("/etc/wsl.conf")]
    for folder in ("/etc/systemd/timesyncd.conf.d", "/run/systemd/timesyncd.conf.d",
                   "/usr/lib/systemd/timesyncd.conf.d", "/etc/systemd/system/systemd-timesyncd.service.d",
                   "/usr/lib/systemd/system/systemd-timesyncd.service.d"):
        paths.extend(sorted(Path(folder).glob("*.conf")))
    commands = [
        ["date", "--iso-8601=ns"], ["uptime"], ["uname", "-a"], ["wsl.exe", "--version"],
        ["timedatectl", "status"], ["timedatectl", "timesync-status"],
        ["timedatectl", "show-timesync", "--all"],
        ["systemctl", "is-active", "systemd-timesyncd.service"],
        ["systemctl", "is-enabled", "systemd-timesyncd.service"],
        ["systemctl", "show", "systemd-timesyncd.service", "-p", "ActiveState", "-p", "SubState",
         "-p", "UnitFileState", "-p", "FragmentPath", "-p", "DropInPaths"],
        ["/home/addaswsw/.local/opt/java-se-7u75-ri/bin/java", "-version"]]
    result = {"captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
              "uptime_proc": Path("/proc/uptime").read_text().strip(),
              "kernel_cmdline": Path("/proc/cmdline").read_text().strip(),
              "kernel_release": Path("/proc/sys/kernel/osrelease").read_text().strip(),
              "current_clocksource": Path("/sys/devices/system/clocksource/clocksource0/current_clocksource").read_text().strip(),
              "available_clocksource": Path("/sys/devices/system/clocksource/clocksource0/available_clocksource").read_text().strip(),
              "clocks": {"realtime": time.time(), "monotonic": time.monotonic(),
                         "raw": time.clock_gettime(time.CLOCK_MONOTONIC_RAW),
                         "boottime": time.clock_gettime(time.CLOCK_BOOTTIME)},
              "config_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                if p.exists() else None for p in paths},
              "commands": [
                  {"argv": c, "exit_code": None, "stdout": "", "stderr": "",
                   "skipped": "Querying the timesync1 D-Bus API would activate the stopped service"}
                  if c[:2] in (["timedatectl", "timesync-status"], ["timedatectl", "show-timesync"])
                     and initial_service["stdout"].strip() != "active"
                  else capture(c) for c in commands]}
    result["service_state"] = result["commands"][7]["stdout"].strip()
    result["service_enable_state"] = result["commands"][8]["stdout"].strip()
    source = Path(__file__).with_name("read-adjtimex.c")
    with tempfile.TemporaryDirectory(prefix="a2-adjtimex-read-") as tmp:
        executable = str(Path(tmp) / "read-adjtimex")
        compiled = capture(["cc", "-Wall", "-Wextra", "-o", executable, str(source)])
        result["adjtimex"] = {"read_only_modes": 0, "compile": compiled,
                             "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        if compiled["exit_code"] == 0:
            result["adjtimex"]["query"] = capture([executable])
    query = r'''
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Windows.Forms
$config = Join-Path $env:USERPROFILE '.wslconfig'
$configHash = if (Test-Path $config) { (Get-FileHash -Algorithm SHA256 $config).Hash } else { $null }
$service = Get-CimInstance Win32_Service -Filter "Name='W32Time'"
[ordered]@{
    date = (Get-Date).ToString('o')
    utc = [DateTime]::UtcNow.ToString('o')
    stopwatch_frequency = [Diagnostics.Stopwatch]::Frequency
    stopwatch_high_resolution = [Diagnostics.Stopwatch]::IsHighResolution
    powershell_version = $PSVersionTable.PSVersion.ToString()
    active_power_scheme = (powercfg /getactivescheme | Out-String).Trim()
    power_line_status = [Windows.Forms.SystemInformation]::PowerStatus.PowerLineStatus.ToString()
    wslconfig_exists = (Test-Path $config)
    wslconfig_sha256 = $configHash
    windows_time_service = @{state=$service.State; start_mode=$service.StartMode}
} | ConvertTo-Json -Depth 4
'''
    encoded = base64.b64encode(query.encode("utf-16-le")).decode()
    host = capture(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded])
    host["argv"][-1] = "<UTF-16LE base64 of query>"
    host["query"] = query
    result["windows_capture"] = host
    if host["exit_code"] == 0:
        result["windows"] = json.loads(host["stdout"])
    return result


if __name__ == "__main__":
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(snapshot(), stream, indent=2)
        stream.write("\n")
