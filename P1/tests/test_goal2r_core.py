"""Goal2R mode and clock fixtures; these are not performance observations."""

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import autotuner as at


class ModeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        binary = self.directory / "unused-fixture"
        binary.write_bytes(b"fixture: process is replaced by a recorded-output mock")
        self.build = dict(binary=str(binary), binary_sha256=at.digest(binary.read_bytes()),
                          build_key="test-only", status="ok", cached=True,
                          compile_wall_s=0, compile_raw_s=0)
        self.target = object.__new__(at.TargetProgram)
        self.target.kernel_clock = "CLOCK_MONOTONIC_RAW"
        self.target.require_checksum = True
        self.target.require_kernel_boundaries = False
        self.config = at.Config(8, "O0")

    def measurement(self, *, mode="benchmark", raw=2, mono=2, realtime=2,
                    kernel=1, stdout=None):
        readings = dict(CLOCK_MONOTONIC=mono, CLOCK_MONOTONIC_RAW=raw,
                        CLOCK_REALTIME=realtime)
        record = dict(command=[self.build["binary"], "8"], started_at=at.now(),
            ended_at=at.now(), spawned=True, status="ok", error=None, returncode=0,
            stdout=stdout if stdout is not None else f"{kernel}\nchecksum=1\n",
            stderr="", process_wall_s=mono, process_wall_clock="CLOCK_MONOTONIC",
            process_raw_s=raw, process_raw_clock="CLOCK_MONOTONIC_RAW",
            clock_start_ns={name: 10 ** 18 for name in readings},
            clock_end_ns={name: 10 ** 18 + int(value * 1e9) for name, value in readings.items()},
            clock_deltas_s=readings, timing_status="ok" if raw > 0 else "invalid",
            timing_error=None if raw > 0 else "primary process clock did not advance",
            auxiliary_clock_anomalies=[n for n in ("CLOCK_MONOTONIC", "CLOCK_REALTIME")
                                       if readings[n] <= 0])
        with mock.patch.object(at, "process", return_value=record):
            return self.target.measure(self.build, self.config, 2, mode=mode)

    def test_auxiliary_reversal_keeps_valid_primary_and_output(self):
        for mode in at.RUN_MODES:
            with self.subTest(mode=mode):
                result = self.measurement(mode=mode, mono=.01, realtime=-3)
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["output_status"], "ok")
                self.assertEqual(result["timing_status"], "ok")
                self.assertEqual(result["score_eligible"], mode == "benchmark")
                self.assertEqual(result["auxiliary_clock_anomalies"], ["CLOCK_REALTIME"])
                self.assertEqual(result["clock_deltas_s"]["CLOCK_REALTIME"], -3)

    def test_primary_reversal_preserves_correctness_output_but_never_scores(self):
        for mode in at.RUN_MODES:
            with self.subTest(mode=mode):
                result = self.measurement(mode=mode, raw=-1)
                self.assertEqual(result["status"], "clock_error" if mode == "benchmark" else "ok")
                self.assertEqual(result["output_status"], "ok")
                self.assertEqual(result["checksum"], 1)
                self.assertEqual(result["timing_status"], "invalid")
                self.assertFalse(result["score_eligible"])

    def test_kernel_overrun_and_nonpositive_timer_are_not_scores(self):
        for kernel, raw in ((3, 2), (-1, 2), (0, 2)):
            for mode in at.RUN_MODES:
                with self.subTest(mode=mode, kernel=kernel):
                    result = self.measurement(mode=mode, raw=raw, kernel=kernel)
                    self.assertEqual(result["status"], "clock_error" if mode == "benchmark" else "ok")
                    self.assertEqual(result["output_status"], "ok")
                    self.assertEqual(result["kernel_s"], kernel)
                    self.assertEqual(result["timing_status"], "invalid")
                    self.assertFalse(result["score_eligible"])

    def test_bad_output_is_an_error_in_every_mode(self):
        for output in ("bad\nchecksum=1\n", "nan\nchecksum=1\n", "1\nchecksum=nan\n", "1\n"):
            for mode in at.RUN_MODES:
                with self.subTest(mode=mode, output=output):
                    result = self.measurement(mode=mode, stdout=output)
                    self.assertEqual(result["status"], "parse_error")
                    self.assertEqual(result["output_status"], "error")
                    self.assertFalse(result["score_eligible"])

    def test_formal_integer_kernel_boundaries_are_required_and_recomputed(self):
        self.target.require_kernel_boundaries = True
        base = 10 ** 18
        output = f"1\nchecksum=1\nkernel_start_ns={base + 1}\nkernel_end_ns={base + 1_000_000_001}\n"
        result = self.measurement(stdout=output)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["kernel_end_ns"] - result["kernel_start_ns"], 1_000_000_000)
        self.assertTrue(result["score_eligible"])
        missing = self.measurement()
        self.assertEqual(missing["status"], "parse_error")
        for begin, end in ((base + 1, base + 2), (base - 1, base + 999_999_999),
                           (base + 1, base + 1), (base + 1, base + 3_000_000_001)):
            output = f"1\nchecksum=1\nkernel_start_ns={begin}\nkernel_end_ns={end}\n"
            for mode in at.RUN_MODES:
                with self.subTest(begin=begin, end=end, mode=mode):
                    result = self.measurement(stdout=output, mode=mode)
                    self.assertEqual(result["status"], "clock_error" if mode == "benchmark" else "ok")
                    self.assertEqual(result["output_status"], "ok")
                    self.assertFalse(result["score_eligible"])
        for fields in ("kernel_start_ns=bad\nkernel_end_ns=2", "kernel_start_ns=1",
                       "kernel_start_ns=1\nkernel_start_ns=1\nkernel_end_ns=2"):
            with self.subTest(fields=fields):
                result = self.measurement(stdout="1\nchecksum=1\n" + fields)
                self.assertEqual(result["status"], "parse_error")

    def test_correctness_trial_succeeds_without_a_performance_best(self):
        space = at.ConfigSpace((8,), ("O0",))
        journal = at.Journal(self.directory / "correctness.jsonl", {"mode": "correctness"})
        self.addCleanup(journal.close)
        evaluator = at.Evaluator(self.target, space, journal, mode="correctness")
        measurement = self.measurement(mode="correctness", raw=-1)
        with mock.patch.object(self.target, "build", return_value=self.build), \
                mock.patch.object(self.target, "measure", return_value=measurement):
            result = at.search(at.SearchStrategy("grid", space), evaluator, 1)
        self.assertEqual(result["completed_configs"], 1)
        self.assertEqual(result["failed_trials"], 0)
        self.assertEqual(result["failed_runs"], 0)
        self.assertIsNone(result["best"])
        trial = next(r for r in journal.records if r["type"] == "trial")
        self.assertIsNone(trial["score"])
        self.assertFalse(trial["score_eligible"])

    def test_raw_online_costs_use_actual_integer_events(self):
        space = at.ConfigSpace((8,), ("O0",))
        journal = at.Journal(self.directory / "events.jsonl", {"fixture": "integer RAW events"})
        self.addCleanup(journal.close)
        evaluator = at.Evaluator(self.target, space, journal)
        base = 10 ** 18
        measurement = self.measurement()
        with mock.patch.object(self.target, "build", return_value=self.build), \
                mock.patch.object(self.target, "measure", return_value=measurement), \
                mock.patch.object(at, "raw_time_ns", side_effect=[base, base + 2,
                    base + 20_000_002, base + 30_000_000]):
            result = at.search(at.SearchStrategy("grid", space), evaluator, 1)
        session = next(r for r in journal.records if r["type"] == "session_end")
        trial = next(r for r in journal.records if r["type"] == "trial")
        self.assertEqual(session["raw_s"], .03)
        self.assertEqual(result["tuning_raw_s"], .03)
        self.assertEqual(trial["trial_raw_s"], .02)
        self.assertEqual(trial["tuning_raw_elapsed_s"], .020000002)
        self.assertEqual(trial["raw_end_ns"] - trial["raw_start_ns"], 20_000_000)

    def test_mode_is_not_a_global_error_bypass(self):
        with self.assertRaises(ValueError):
            self.target.measure(self.build, self.config, 2, mode="ignore_errors")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            at.main(["search", "--mode", "correctness"])

    def test_build_key_ignores_runtime_settings_but_resume_does_not(self):
        metadata = dict(source="fixture.c", source_sha256="source", compiler={"sha256": "compiler"},
            flags=list(at.COMMON_FLAGS), compile_timeout=60, n=4096,
            kernel_clock="CLOCK_MONOTONIC_RAW", require_checksum=True)
        keys = [at.fingerprint(at.build_identity(dict(metadata, compile_timeout=value), "O2"))
                for value in (60, 60.0, 120)]
        self.assertEqual(len(set(keys)), 1)
        changed_flags = dict(metadata, flags=[*at.COMMON_FLAGS, "-DTEST=1"])
        self.assertNotEqual(keys[0], at.fingerprint(at.build_identity(changed_flags, "O2")))
        path = self.directory / "settings.jsonl"
        journal = at.Journal(path, metadata)
        journal.close()
        with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
            at.Journal(path, dict(metadata, compile_timeout=120), True)


if __name__ == "__main__":
    unittest.main()
