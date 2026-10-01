#!/usr/bin/env python3
"""Read bounded guest logs and host suspend/time-event metadata for one probe."""
import base64
import datetime
import json
from pathlib import Path
import subprocess
import sys

directory = Path(sys.argv[1])
summary = json.loads((directory / "summary.json").read_text())
start, end = summary["started_at"], summary["ended_at"]
datetime.datetime.fromisoformat(start)
datetime.datetime.fromisoformat(end)

def decode(data):
    for encoding in ("utf-8", "gb18030", "utf-16-le"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8 with replacement"

def capture(command):
    result = subprocess.run(command, capture_output=True, timeout=30)
    stdout, stdout_encoding = decode(result.stdout)
    stderr, stderr_encoding = decode(result.stderr)
    return {"command": command, "exit_code": result.returncode,
            "stdout": stdout, "stderr": stderr,
            "stdout_encoding": stdout_encoding, "stderr_encoding": stderr_encoding}

query = ("$ErrorActionPreference='Stop'; try {"
    "$s=[DateTimeOffset]::Parse('" + start + "').LocalDateTime; "
    "$e=[DateTimeOffset]::Parse('" + end + "').LocalDateTime; "
    "$ev=Get-WinEvent -FilterHashtable @{LogName='System';StartTime=$s;EndTime=$e;"
    "ProviderName=@('Microsoft-Windows-Kernel-Power','Microsoft-Windows-Power-Troubleshooter',"
    "'Microsoft-Windows-Kernel-General','Microsoft-Windows-Time-Service')}; "
    "$r=@($ev|Where-Object {$_.Id -in @(1,41,42,107,506,507,35,37)}|ForEach-Object {"
    "[pscustomobject]@{TimeCreated=$_.TimeCreated.ToString('o');Id=$_.Id;Provider=$_.ProviderName}}); "
    "[pscustomobject]@{Status='QuerySucceeded';Timezone=[TimeZoneInfo]::Local.Id;Events=$r}"
    "|ConvertTo-Json -Depth 4} catch {"
    "$status=if ($_.FullyQualifiedErrorId -like 'NoMatchingEventsFound*') {'NoMatchingEvents'} else {'QueryFailed'}; "
    "[pscustomobject]@{Status=$status;ErrorId=$_.FullyQualifiedErrorId;"
    "Category=$_.CategoryInfo.Category.ToString()}|ConvertTo-Json }")
encoded = base64.b64encode(query.encode("utf-16-le")).decode()
host = capture(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded])
host["query"] = query
host["command"] = host["command"][:-1] + ["<UTF-16LE base64 of query above>"]
host["scope"] = "Event timestamps, IDs and provider names only; no event message dump"
(directory / "host-event-check.json").write_text(json.dumps(host, indent=2) + "\n")
print("Host event query:", host["exit_code"], host["stdout"].strip())
commands = [
    ["journalctl", "-k", "-b", "--since", start, "--until", end, "--no-pager"],
    ["journalctl", "-u", "systemd-timesyncd", "--since", start, "--until", end, "--no-pager"],
    ["timedatectl", "timesync-status"], ["timedatectl", "show-timesync", "--all"]]
records = [capture(command) for command in commands]
record = {"checked_at": datetime.datetime.now().astimezone().isoformat(),
          "commands": records,
          "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
          "clocksource": Path("/sys/devices/system/clocksource/clocksource0/current_clocksource").read_text().strip()}
(directory / "guest-diagnostics.json").write_text(json.dumps(record, indent=2) + "\n")
print("Relevant kernel entries:")
print("\n".join(line for line in records[0]["stdout"].splitlines()
      if any(word in line.lower() for word in ("clocksource", "suspend", "resume", "timekeeping"))))
