#!/usr/bin/env python3
"""Run a command file in Zutty and capture the actual X11 display, unedited."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from PIL import ImageGrab

commands, image = map(lambda p: Path(p).resolve(), sys.argv[1:])
display = ":91"
if Path("/tmp/.X91-lock").exists():
    sys.exit("Display :91 is in use; leave its owner untouched")
with tempfile.TemporaryDirectory(prefix="a2-terminal-") as directory:
    temp = Path(directory)
    ready = temp / "ready"
    launcher = temp / "launch.sh"
    # The marker is outside the repository and is not displayed in the terminal.
    launcher.write_text('bash "$1"\nscreenshot_status=$?\n'
                        'printf "%s\\n" "$screenshot_status" > "$2"\nread -r -t 60\n')
    with commands.with_suffix(".gui.log").open("wb") as log:
        xvfb = subprocess.Popen(["Xvfb", display, "-screen", "0", "1440x720x24",
                                 "-nolisten", "tcp"], stdout=log, stderr=log)
        terminal = None
        try:
            deadline = time.monotonic() + 10
            while subprocess.run(["xdpyinfo", "-display", display],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 timeout=2).returncode:
                if xvfb.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Xvfb did not start")
                time.sleep(0.1)
            terminal = subprocess.Popen([
                "zutty", "-display", display, "-font", "DejaVuSansMono",
                "-fontsize", "20", "-geometry", "120x30", "-border", "0",
                "-title", "SPECjvm2008", "-e", "/bin/bash", str(launcher),
                str(commands), str(ready)], stdout=log, stderr=log)
            deadline = time.monotonic() + 30
            while not ready.exists() or ready.stat().st_size == 0:
                if terminal.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Terminal command file did not finish")
                time.sleep(0.1)
            command_exit = int(ready.read_text())
            if command_exit:
                raise RuntimeError(f"Terminal command file exited with {command_exit}")
            time.sleep(3)
            ImageGrab.grab(xdisplay=display).save(image)
        finally:
            for process in (terminal, xvfb):
                if process and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
    record = {"image": str(image), "commands": str(commands),
              "command_exit_code": command_exit,
              "commands_sha256": hashlib.sha256(commands.read_bytes()).hexdigest(),
              "captured_at": datetime.datetime.now().astimezone().isoformat(),
              "method": "Real Zutty terminal in Xvfb, Pillow X11 ImageGrab; no pixel edits",
              "sha256": hashlib.sha256(image.read_bytes()).hexdigest()}
    commands.with_suffix(".capture.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
