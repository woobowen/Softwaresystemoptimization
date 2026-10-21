#!/usr/bin/env python3
"""Capture a real xterm on a temporary authenticated Xvfb display."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command_file", type=Path)
    parser.add_argument("image", type=Path)
    parser.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.inside:
        # xvfb-run creates a private authorization file and removes it on exit.
        subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 1600x1000x24 -nolisten tcp",
                        sys.executable, __file__, str(args.command_file.resolve()),
                        str(args.image.resolve()), "--inside"], check=True)
        return
    xterm = shutil.which("xterm") or str(ROOT / ".cache/P2/tools/xterm")
    args.image.parent.mkdir(parents=True, exist_ok=True)
    if args.image.exists():
        raise RuntimeError("Image already exists; review it before replacing")
    with tempfile.TemporaryDirectory(prefix="p2-capture-") as tmp:
        directory = Path(tmp)
        done = directory / "done"
        wrapper = directory / "view.sh"
        wrapper.write_text('bash "$1"\nstatus=$?\nprintf "%s" "$status" > "$2"\nexit "$status"\n')
        command = [xterm, "-hold", "-fa", "DejaVu Sans Mono", "-fs", "12",
                   "-geometry", "158x46+8+8", "-bg", "#111827", "-fg", "#e5e7eb",
                   "-title", "P2: saved results and source", "-e", "bash", str(wrapper),
                   str(args.command_file.resolve()), str(done)]
        with (directory / "xterm.log").open("w") as log:
            terminal = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=log,
                                        env=dict(os.environ, LC_ALL="C.UTF-8"))
            try:
                deadline = time.monotonic() + 30
                while not done.exists():
                    if terminal.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError("Terminal did not finish: " + (directory / "xterm.log").read_text())
                    time.sleep(.1)
                if done.read_text() != "0":
                    raise RuntimeError("Displayed command failed")
                time.sleep(.3)
                capture = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "x11grab",
                           "-video_size", "1600x1000", "-i", os.environ["DISPLAY"],
                           "-frames:v", "1", "-threads", "1", str(args.image)]
                subprocess.run(capture, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                record = dict(image=str(args.image.relative_to(ROOT)),
                              command_file=str(args.command_file.relative_to(ROOT)),
                              command_text=args.command_file.read_text(),
                              image_sha256=hashlib.sha256(args.image.read_bytes()).hexdigest(),
                              command_sha256=hashlib.sha256(args.command_file.read_bytes()).hexdigest(),
                              display=os.environ["DISPLAY"], actual_xterm=True,
                              transport="authenticated local Xvfb; TCP disabled", capture=capture)
            finally:
                terminal.terminate()
                try:
                    terminal.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    terminal.kill()
                    terminal.wait()
        record["terminal_exit"] = terminal.returncode
    with (ROOT / "P2/evidence/commands/screenshots.jsonl").open("a") as output:
        output.write(json.dumps(record) + "\n")
    print(record["image"], record["image_sha256"])


if __name__ == "__main__":
    main()
