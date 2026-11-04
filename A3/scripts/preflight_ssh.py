#!/usr/bin/env python3
"""Small Windows-OpenSSH bridge. No SSH configuration or identity changes."""
import argparse
import base64
import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

EVIDENCE = Path(__file__).resolve().parents[1] / "evidence/remote_preflight/commands"
SSH = ["/mnt/c/Windows/System32/OpenSSH/ssh.exe", "-T", "-o", "BatchMode=yes",
       "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
       "-o", "ConnectTimeout=15", "new-server"]


def run_remote(command, data=None, label="remote", timeout=60):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(SSH + [command], input=data, capture_output=True, timeout=timeout)
    (EVIDENCE / f"{label}.txt").write_bytes(proc.stdout)
    (EVIDENCE / f"{label}.stderr.txt").write_bytes(proc.stderr)
    with (EVIDENCE / "commands.jsonl").open("a") as log:
        log.write(json.dumps({"utc": started, "argv": SSH + [command],
                              "exit_code": proc.returncode, "stdout": f"commands/{label}.txt",
                              "stderr": f"commands/{label}.stderr.txt"}) + "\n")
    return proc


def main():
    global EVIDENCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "put", "get"])
    parser.add_argument("source", help="run: local shell script; put/get: source file")
    parser.add_argument("destination", nargs="?")
    parser.add_argument("--label", required=True, help="unique evidence output name")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    EVIDENCE = args.evidence_dir
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if (EVIDENCE / f"{args.label}.txt").exists():
        parser.error("Evidence label exists; choose a new label")
    if args.action == "run":
        proc = run_remote("bash -s", Path(args.source).read_bytes(), args.label, args.timeout)
    elif args.action == "put":
        data = Path(args.source).read_bytes()
        dest = shlex.quote(args.destination)
        # noclobber protects pre-existing remote content; base64 avoids path/CRLF issues.
        command = f"umask 077; set -C; base64 -d > {dest} && sha256sum {dest}"
        proc = run_remote(command, base64.b64encode(data), args.label, args.timeout)
        expected = hashlib.sha256(data).hexdigest()
        if proc.returncode == 0 and proc.stdout.decode().split()[0] != expected:
            raise RuntimeError("Upload SHA-256 mismatch")
    else:
        source = shlex.quote(args.source)
        proc = run_remote(f"base64 -w0 -- {source}", label=args.label, timeout=args.timeout)
        if proc.returncode == 0:
            data = base64.b64decode(proc.stdout, validate=True)
            with Path(args.destination).open("xb") as output:
                output.write(data)
            print(json.dumps({"download": args.destination, "bytes": len(data),
                              "sha256": hashlib.sha256(data).hexdigest()}))
            # Keep command metadata rather than a redundant base64 trace copy.
            (EVIDENCE / f"{args.label}.txt").write_text("Binary transfer saved to " + args.destination + "\n")
    if args.action != "get":
        sys.stdout.buffer.write(proc.stdout)
    sys.stderr.buffer.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
