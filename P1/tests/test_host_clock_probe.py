"""Pure clock counterexamples and five real, scoped Windows cleanup checks."""

import json
import os
from pathlib import Path
import sys
import subprocess
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import host_clock_probe as hp


class HostClockTests(unittest.TestCase):
    def pipe(self):
        read, write = os.pipe()
        stream = os.fdopen(read, "rb", buffering=0)
        self.addCleanup(stream.close)
        self.addCleanup(os.close, write)
        return SimpleNamespace(stdout=stream), write

    def test_partial_line_has_a_deadline(self):
        bridge, write = self.pipe()
        os.write(write, b"partial")
        with self.assertRaisesRegex(ValueError, "timed out"):
            hp.line(bridge, timeout=.02)
        self.assertEqual(bridge.clock_pending, b"partial")

    def test_buffered_second_line_is_not_lost(self):
        bridge, write = self.pipe()
        os.write(write, b"first\r\nsecond\r\n")
        self.assertEqual(hp.line(bridge), "first")
        self.assertEqual(hp.line(bridge), "second")

    def test_oversized_reply_is_rejected(self):
        bridge, write = self.pipe()
        os.write(write, b"x" * 4100)
        with self.assertRaisesRegex(ValueError, "byte limit"):
            hp.line(bridge)

    @staticmethod
    def reading(tick, before, after):
        return dict(host_tick=tick, before_ns={name: before for name in hp.CLOCKS},
                    after_ns={name: after for name in hp.CLOCKS})

    def test_integer_ticks_and_endpoint_uncertainty(self):
        first = self.reading(10**17, 100000000000, 100001000000)
        last = self.reading(10**17 + 400000000, 140000000000, 140001000000)
        value = hp.interval(first, last, 10000000)
        self.assertEqual(value["host_elapsed_s"], 40)
        self.assertTrue(value["usable_brackets"])
        bounds = value["linux_interval_bounds"]["RAW"]["host_to_linux_ratio_bounds"]
        self.assertLess(bounds[0], 1)
        self.assertGreater(bounds[1], 1)
        self.assertEqual(value["host_quantization_allowance_s"], 2e-7)

    def test_excessive_endpoint_latency_cannot_be_usable(self):
        first = self.reading(1, 100000000000, 100030000000)
        last = self.reading(400000001, 140000000000, 140001000000)
        self.assertFalse(hp.interval(first, last, 10000000)["usable_brackets"])

    def test_backwards_interval_is_rejected(self):
        first = self.reading(4, 100000000000, 100001000000)
        last = self.reading(3, 140000000000, 140001000000)
        with self.assertRaisesRegex(ValueError, "positive"):
            hp.interval(first, last, 10000000)

    def test_auxiliary_jump_preserves_primary_brackets(self):
        first = self.reading(100, 100000000000, 100001000000)
        last = self.reading(400000100, 140000000000, 140001000000)
        last["before_ns"]["REALTIME"] = 50000000000
        last["after_ns"]["REALTIME"] = 50001000000
        value = hp.interval(first, last, 10000000)
        self.assertTrue(value["usable_brackets"])
        self.assertTrue(value["raw_relative_screen_pass"])
        self.assertTrue(value["linux_interval_bounds"]["REALTIME"]["auxiliary_anomaly"])

    def test_wide_auxiliary_endpoint_does_not_change_raw_precision(self):
        first = self.reading(100, 100000000000, 100001000000)
        last = self.reading(400000100, 140000000000, 140001000000)
        last["after_ns"]["REALTIME"] += 10000000000
        value = hp.interval(first, last, 10000000)
        self.assertTrue(value["usable_brackets"])
        self.assertFalse(value["width_limits_pass"]["REALTIME"])

    def test_invalid_response_raw_is_preserved(self):
        bridge = SimpleNamespace(stdin=mock.Mock())
        rows = []
        with mock.patch.object(hp, "line", return_value="sample:wrong:10:20:True:30"):
            with self.assertRaises(ValueError):
                hp.sample(bridge, 0, 20, 30, rows)
        self.assertEqual(rows[0]["response"], "sample:wrong:10:20:True:30")
        self.assertIn("after_ns", rows[0])

    def test_cleanup_is_bound_to_a_process_object(self):
        completed = subprocess.CompletedProcess([], 0, b"absent\r\n", b"")
        with mock.patch.object(hp.subprocess, "run", return_value=completed) as run:
            self.assertEqual(hp.host_cleanup(1234, 987654)["state"], "absent")
        command = run.call_args.args[0][-1]
        self.assertTrue(command.startswith("$ErrorActionPreference"))
        self.assertIn("$null = $p.Handle", command)
        self.assertIn("-ne 987654", command)
        self.assertIn("Stop-Process -InputObject $p", command)


@unittest.skipUnless(Path(hp.POWERSHELL).is_file(), "Windows interop is unavailable")
class NativeHostCleanupTests(unittest.TestCase):
    def check(self, mode):
        command = [sys.executable, "-B", str(Path(hp.__file__)), "--cleanup-check", mode]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=40)
        row = json.loads(completed.stdout)
        evidence = os.environ.get("P1_HOST_CLEANUP_LOG")
        if evidence:
            with open(evidence, "a") as out:
                out.write(json.dumps(dict(command=command, returncode=completed.returncode,
                    result=row, stderr=completed.stderr), ensure_ascii=False) + "\n")
        if mode in ("normal", "cleanup-signal"):
            self.assertEqual(completed.returncode, 0)
        else:
            self.assertNotEqual(completed.returncode, 0)
            expected = {"error": "ValueError", "timeout": "TimeoutExpired", "signal": "KeyboardInterrupt"}
            self.assertTrue(row["error"].startswith(expected[mode] + ":"))
        self.assertTrue(row["lifecycle_valid"])
        self.assertEqual(row["host_cleanup"]["state"], "absent")
        self.assertFalse(row["raw_candidate_feasible"])
        if mode in ("timeout", "signal"):
            self.assertFalse(Path(f"/proc/{row['cleanup_workload']['pid']}").exists())

    def test_normal(self):
        self.check("normal")

    def test_failed_workload(self):
        self.check("error")

    def test_timeout(self):
        self.check("timeout")

    def test_sigterm(self):
        self.check("signal")

    def test_sigterm_during_cleanup(self):
        self.check("cleanup-signal")


if __name__ == "__main__":
    unittest.main()
