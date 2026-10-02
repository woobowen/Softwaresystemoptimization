"""Native private-display captures and cleanup after real failures/signals."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

P1=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P1/"scripts"))
import safe_screenshots as ss


class ScreenshotCleanupTests(unittest.TestCase):
    def setUp(self):
        (P1/".cache").mkdir(exist_ok=True)
        self.temporary=tempfile.TemporaryDirectory(prefix="screenshot-test-",dir=P1/".cache")
        self.directory=Path(self.temporary.name)
        self.evidence=self.directory/"captures.jsonl"

    def tearDown(self):
        self.temporary.cleanup()

    def command(self,text):
        path=self.directory/"command.sh"
        path.write_text(text)
        return path

    def check_cleanup(self):
        row=json.loads(self.evidence.read_text().splitlines()[-1])
        self.assertNotEqual(row["empty_authority_returncode"],0)
        self.assertTrue(row["unix_listeners_during"])
        self.assertEqual(row["tcp_listeners_after"],[])
        self.assertEqual(row["unix_listeners_after"],[])
        self.assertEqual(row["cleanup_errors"],[])
        for field in ("owned_processes_stopped","shell_stopped","authorization_removed_on_exit",
                      "display_socket_removed","display_lock_removed"):
            self.assertTrue(row[field],field)
        # Retain actual integration evidence, never authority contents or cookies.
        ss.append(P1/"evidence/commands/screenshot_cleanup_tests.jsonl","integration_test",
                  test=self.id(),capture=row)
        return row

    def test_real_terminal_capture_and_private_authorization(self):
        output=self.directory/"capture.png"
        ss.capture(self.command("printf 'P1 private Unix display test\\n'\n"),output,self.evidence,"P1 native test")
        row=self.check_cleanup()
        self.assertEqual(row["command_returncode"],0)
        self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_failed_terminal_command_cleans_display(self):
        output=self.directory/"failed.png"
        with self.assertRaises(ValueError):
            ss.capture(self.command("exit 7\n"),output,self.evidence,"P1 failure test")
        self.assertEqual(self.check_cleanup()["command_returncode"],7)
        self.assertFalse(output.exists())

    def test_timeout_cleans_its_shell_and_display(self):
        with self.assertRaises(ValueError):
            ss.capture(self.command("sleep 30\n"),self.directory/"timeout.png",self.evidence,
                       "P1 timeout test",timeout=.25)
        self.check_cleanup()

    def test_sigterm_cleans_its_shell_and_display(self):
        command=self.command("sleep 30\n")
        before=set((P1/".cache").glob("screenshot-*"))
        child=subprocess.Popen([sys.executable,"-B",str(P1/"scripts/safe_screenshots.py"),
            "--command-file",str(command),"--output",str(self.directory/"signal.png"),
            "--evidence",str(self.evidence)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                new=set((P1/".cache").glob("screenshot-*"))-before
                if any((path/"shell.pid").exists() for path in new):
                    break
                if child.poll() is not None:
                    self.fail("capture exited before signal: "+child.communicate()[1])
                time.sleep(.05)
            else:
                self.fail("native terminal shell did not start")
            os.kill(child.pid,signal.SIGTERM)
            _,stderr=child.communicate(timeout=15)
            self.assertNotEqual(child.returncode,0,stderr)
            self.check_cleanup()
        finally:
            if child.poll() is None:
                os.kill(child.pid,signal.SIGTERM)
                child.communicate(timeout=15)


if __name__=="__main__": unittest.main()
