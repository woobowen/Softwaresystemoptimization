"""Logic and real subprocess tests; small C fixtures are never benchmark data."""

import contextlib
import io
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import autotuner as at


class LogicTests(unittest.TestCase):
    def test_space_complete_stable_and_checked(self):
        space = at.ConfigSpace()
        self.assertEqual(len(space.configs), 20)
        self.assertEqual(len(set(space.configs)), 20)
        self.assertEqual([c.opt for c in space.configs[:4]], list(at.OPTS))
        self.assertEqual(space.configs[8], at.Config(24, "O0"))
        for blocks, opts in (((), at.OPTS), ((0,), at.OPTS), ((True,), at.OPTS),
                             ((8, 8), at.OPTS), ((8,), ("O4",)), ((8,), ("O0", "O0"))):
            with self.subTest(blocks=blocks, opts=opts), self.assertRaises(ValueError):
                at.ConfigSpace(blocks, opts)
        with self.assertRaises(ValueError):
            space.check(at.Config(32, "O3"))
        self.assertEqual(space.neighbors(at.Config(24, "O2")), [at.Config(16, "O2"),
            at.Config(24, "O1"), at.Config(24, "O3"), at.Config(64, "O2")])
        self.assertEqual(space.neighbors(at.Config(8, "O0")), [at.Config(8, "O1"), at.Config(16, "O0")])

    def test_parser_rejects_missing_nonfinite_nonpositive_and_malformed(self):
        for text in ("", "\n1.0", "nan", "inf", "-inf", "0", "-1", "elapsed=1", "1 2"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                at.TargetProgram.parse(text)
        self.assertEqual(at.TargetProgram.parse("0.125000\nchecksum=42\n"), .125)
        for text in ("1\nchecksum=nan", "1\nchecksum=inf", "1\nchecksum=no", "1\nchecksum 42",
                     "1\nchecksum=1\nchecksum=1"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                at.TargetProgram.parse(text)

    @staticmethod
    def visit(strategy, budget, score):
        visited = []
        for i in range(budget):
            config = strategy.suggest()
            if config is None:
                break
            visited.append(config)
            strategy.observe(config, score(config, i))
        return visited

    def test_random_without_replacement_and_seed_reproducible(self):
        space = at.ConfigSpace()
        a = self.visit(at.SearchStrategy("random", space, 17), 20, lambda c, i: 1)
        b = self.visit(at.SearchStrategy("random", space, 17), 20, lambda c, i: 1)
        c = self.visit(at.SearchStrategy("random", space, 18), 20, lambda c, i: 1)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(set(a), set(space.configs))
        self.assertEqual(len(set(a)), 20)

    def test_greedy_seeded_start_ties_and_no_improvement(self):
        space = at.ConfigSpace()
        for seed in (0, 9, 43):
            strategy = at.SearchStrategy("greedy", space, seed)
            start = random.Random(seed).choice(space.configs)
            self.assertEqual(strategy.suggest(), start)
            visited = self.visit(strategy, 20, lambda c, i: 1)
            self.assertEqual(visited, [start, *space.neighbors(start)])
            self.assertEqual(strategy.current, start)
            self.assertIsNone(strategy.suggest())

    def test_greedy_mid_neighborhood_budget_and_failed_feedback(self):
        space = at.ConfigSpace()
        for budget in (0, 1, 3):
            strategy = at.SearchStrategy("greedy", space, 7)
            visited = self.visit(strategy, budget, lambda c, i: 10 - i)
            self.assertEqual(len(visited), budget)
            self.assertEqual(len(set(visited)), budget)
        strategy = at.SearchStrategy("greedy", at.ConfigSpace((8,), ("O0",)), 1)
        config = strategy.suggest()
        strategy.observe(config, None)
        self.assertIsNone(strategy.suggest())
        with self.assertRaises(ValueError):
            at.SearchStrategy("unknown", space)
        with self.assertRaises(ValueError):
            at.SearchStrategy("grid", space).observe(space.configs[1], 1)

    def test_journal_resume_fingerprint_and_truncated_tail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            journal = at.Journal(path, {"protocol": "a"})
            journal.append("note", text="中文")
            journal.close()
            with path.open("ab") as stream:
                stream.write(b'{"type": "broken')
            with self.assertRaises(ValueError):
                at.Journal(path, {"protocol": "b"}, True)
            journal = at.Journal(path, {"protocol": "a"}, True)
            self.assertEqual(journal.records[-1]["type"], "journal_recovery")
            self.assertEqual(journal.records[-1]["discarded_fragment"], '{"type": "broken')
            journal.append("note", text="after recovery")
            journal.close()
            self.assertEqual(len([json.loads(line) for line in path.read_text().splitlines()]), 4)
            with self.assertRaises(FileExistsError):
                at.Journal(path, {"protocol": "a"})

    def test_cli_invalid_arguments_and_list(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(at.main(["list"]), 0)
        self.assertEqual(len(json.loads(output.getvalue())), 20)
        for args in (["list", "--budget", "-1"], ["list", "--repeats", "0"],
                     ["list", "--timeout", "nan"], ["list", "--blocks", "8,8"],
                     ["list", "--opts", "O4"], ["run", "--s", "32", "--opt", "O0"],
                     ["run", "--s", "8"], ["search", "--resume"]):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                at.main(args)
            self.assertEqual(error.exception.code, 2)


@unittest.skipUnless(shutil.which("gcc"), "gcc is required for real subprocess tests")
class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "fixture.c"
        self.source.write_text('#include <stdio.h>\n#include <stdlib.h>\n'
                               'int main(int argc, char **argv) {\n'
                               'if (argc != 2) return 2;\n'
                               'printf("%.6f\\nchecksum=1\\n", atoi(argv[1]) / 100.0);\n'
                               'return 0;\n}\n')
        self.target = at.TargetProgram(self.source, cache_dir=self.directory / "cache")

    def evaluator(self, name, repeats=1, timeout=2, space=None, resume=False, metadata=None):
        space = space or at.ConfigSpace()
        metadata = metadata or {"fixture": "small logic-only C target", "repeats": repeats}
        journal = at.Journal(self.directory / (name + ".jsonl"), metadata, resume)
        self.addCleanup(journal.close)
        return at.Evaluator(self.target, space, journal, repeats, timeout)

    def test_budget_zero_one_twenty_and_independent_search_runs(self):
        for budget in (0, 1, 20):
            evaluator = self.evaluator("budget" + str(budget))
            result = at.search(at.SearchStrategy("grid", evaluator.space), evaluator, budget)
            self.assertEqual(result["attempted_trials"], budget)
            self.assertEqual(result["process_runs"], budget)
            self.assertEqual(result["distinct_configs"], budget)
            self.assertEqual(result["completed_configs"], budget)
            self.assertEqual(result["best"] is None, budget == 0)
        evaluator = self.evaluator("independent", repeats=2)
        result = at.search(at.SearchStrategy("grid", evaluator.space), evaluator, 20)
        self.assertEqual(result["process_runs"], 40)
        self.assertEqual(result["compile_processes"], 0)
        self.assertEqual(result["cached_builds"], 20)
        self.assertEqual(result["compile_wall_s"], 0)
        self.assertEqual(result["best"]["config"], {"s": 8, "opt": "O0"})
        with self.assertRaisesRegex(ValueError, "completed trial configuration mismatch"):
            evaluator.evaluate(at.Config(16, "O0"), 0)
        trials = [r for r in evaluator.journal.records if r["type"] == "trial"]
        self.assertTrue(all(r["trial_wall_s"] > 0 and r["started_at"] and r["ended_at"] for r in trials))
        self.assertEqual(sorted(r["tuning_elapsed_s"] for r in trials), [r["tuning_elapsed_s"] for r in trials])

    def test_build_cache_identity_and_binary_corruption(self):
        first = self.target.build("O2")
        second = self.target.build("O2")
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(first["binary_sha256"], second["binary_sha256"])
        self.assertEqual(second["flags"], [*at.COMMON_FLAGS, "-O2"])
        Path(first["binary"]).write_bytes(b"damaged cache")
        repaired = self.target.build("O2")
        self.assertFalse(repaired["cached"])
        self.assertEqual(repaired["binary_sha256"], first["binary_sha256"])
        alternate = at.TargetProgram(self.source, flags=(*at.COMMON_FLAGS, "-DTEST=1"),
                                     cache_dir=self.target.cache_dir).build("O2")
        self.assertNotEqual(alternate["build_key"], first["build_key"])
        self.source.write_text(self.source.read_text() + "\n")
        with self.assertRaises(ValueError):
            self.target.build("O2")

    def test_cache_hit_log_failure_is_not_swallowed_or_recompiled(self):
        self.target.build("O0")
        def fail(kind, data):
            raise OSError("test-only simulated journal failure")
        with mock.patch.object(at, "process", side_effect=AssertionError("must not compile")):
            with self.assertRaises(OSError):
                self.target.build("O0", fail)

    def test_declared_checksum_output_is_required(self):
        self.source.write_text('#include <stdio.h>\nint main(int argc, char **argv) {\n'
            '(void)argv; if(argc==99) printf("checksum=1\\n"); puts("1.0"); return 0; }\n')
        self.target = at.TargetProgram(self.source, cache_dir=self.target.cache_dir)
        self.assertTrue(self.target.require_checksum)
        evaluator = self.evaluator("missing-checksum")
        result = at.search(at.SearchStrategy("grid", evaluator.space), evaluator, 1)
        self.assertIsNone(result["best"])
        measurement = next(r for r in evaluator.journal.records if r["type"] == "measurement")
        self.assertEqual(measurement["status"], "parse_error")
        self.assertIn("missing checksum", measurement["error"])

    def test_compile_failure_is_recorded_and_consumes_attempt_budget(self):
        self.source.write_text("this is not C;\n")
        self.target = at.TargetProgram(self.source, cache_dir=self.target.cache_dir)
        evaluator = self.evaluator("compile-error")
        result = at.search(at.SearchStrategy("grid", evaluator.space), evaluator, 2)
        self.assertEqual(result["attempted_trials"], 2)
        self.assertEqual(result["failed_trials"], 2)
        self.assertEqual(result["compile_processes"], 2)
        self.assertEqual(result["process_runs"], 0)
        self.assertIsNone(result["best"])
        builds = [r for r in evaluator.journal.records if r["type"] == "build"]
        self.assertTrue(all(r["compile"]["returncode"] != 0 and r["compile"]["stderr"] for r in builds))

    def test_timeout_nonzero_and_bad_output_are_not_best(self):
        sources = {
            "timeout": '#include <unistd.h>\nint main(void) { sleep(2); return 0; }\n',
            "nonzero": 'int main(void) { return 4; }\n',
            "parse_error": '#include <stdio.h>\nint main(void) { puts("nan"); return 0; }\n',
        }
        for status, code in sources.items():
            self.source.write_text(code)
            self.target = at.TargetProgram(self.source, cache_dir=self.target.cache_dir)
            evaluator = self.evaluator(status, timeout=.05)
            result = at.search(at.SearchStrategy("grid", evaluator.space), evaluator, 1)
            self.assertEqual(result["process_runs"], 1)
            self.assertEqual(result["failed_trials"], 1)
            self.assertIsNone(result["best"])
            record = next(r for r in evaluator.journal.records if r["type"] == "measurement")
            self.assertEqual(record["status"], status)
            self.assertGreater(record["process_wall_s"], 0)
            self.assertTrue(record["started_at"] and record["ended_at"])

    def test_resume_preserves_completed_repeat_and_replays_search(self):
        evaluator = self.evaluator("partial", repeats=3)
        strategy = at.SearchStrategy("random", evaluator.space, 9)
        original = self.target.measure
        calls = 0

        def interrupt_between_repeats(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt
            return original(*args, **kwargs)

        with mock.patch.object(self.target, "measure", interrupt_between_repeats):
            with self.assertRaises(KeyboardInterrupt):
                at.search(strategy, evaluator, 4)
        self.assertEqual(len([r for r in evaluator.journal.records if r["type"] == "measurement"]), 1)
        evaluator.journal.close()
        resumed = self.evaluator("partial", repeats=3, resume=True)
        result = at.search(at.SearchStrategy("random", resumed.space, 9), resumed, 4)
        self.assertEqual(result["process_runs"], 12)
        self.assertEqual(result["attempted_trials"], 4)
        trials = [at.Config(**r["config"]) for r in resumed.journal.records if r["type"] == "trial"]
        expected = LogicTests.visit(at.SearchStrategy("random", resumed.space, 9), 4, lambda c, i: 1)
        self.assertEqual(trials, expected)
        self.assertIsNone(next(r for r in resumed.journal.records if r["type"] == "trial")["trial_wall_s"])
        self.assertEqual(at.search(at.SearchStrategy("random", resumed.space, 9), resumed, 4), result)

    def test_greedy_resume_reconstructs_moves_from_own_feedback(self):
        evaluator = self.evaluator("greedy-partial", repeats=2)
        original = self.target.measure
        calls = 0
        def interrupt(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise KeyboardInterrupt
            return original(*args, **kwargs)
        with mock.patch.object(self.target, "measure", interrupt), self.assertRaises(KeyboardInterrupt):
            at.search(at.SearchStrategy("greedy", evaluator.space, 9), evaluator, 8)
        evaluator.journal.close()
        resumed = self.evaluator("greedy-partial", repeats=2, resume=True)
        result = at.search(at.SearchStrategy("greedy", resumed.space, 9), resumed, 8)
        expected = LogicTests.visit(at.SearchStrategy("greedy", resumed.space, 9), 8, lambda c, i: c.s / 100)
        actual = [at.Config(**r["config"]) for r in resumed.journal.records if r["type"] == "trial"]
        self.assertEqual(actual, expected)
        self.assertEqual(result["process_runs"], 2 * len(expected))
        self.assertEqual(result["distinct_configs"], len(expected))

    def test_orphan_process_on_resume_is_failed_without_rerun(self):
        evaluator = self.evaluator("orphan", repeats=2)
        config = evaluator.space.configs[0]
        evaluator.journal.append("trial_start", trial_id=0, config=at.asdict(config))
        self.target.build(config.opt, lambda kind, data: evaluator.journal.append(kind,
            trial_id=0, config=at.asdict(config), **data))
        evaluator.journal.append("measurement_start", trial_id=0, config=at.asdict(config),
                                 repeat=0, command=["test-only"], started_at=at.now(), spawned=True)
        evaluator.journal.close()
        resumed = self.evaluator("orphan", repeats=2, resume=True)
        with mock.patch.object(self.target, "measure", side_effect=AssertionError("must not rerun")):
            result = at.search(at.SearchStrategy("grid", resumed.space), resumed, 1)
        self.assertEqual(result["process_runs"], 1)
        self.assertEqual(result["interrupted_runs"], 1)
        self.assertEqual(result["failed_trials"], 1)
        self.assertIsNone(result["best"])

    def test_resume_refuses_live_group_and_marks_unknown_hard_exit_costs(self):
        evaluator = self.evaluator("live")
        config = evaluator.space.configs[0]
        evaluator.journal.append("trial_start", trial_id=0, config=at.asdict(config))
        evaluator.journal.append("build_start", trial_id=0, config=at.asdict(config), pid=os.getpgrp())
        evaluator.journal.append("session_start", started_at=at.now())
        with self.assertRaisesRegex(ValueError, "still present"):
            at.search(at.SearchStrategy("grid", evaluator.space), evaluator, 1)
        # Simulate a vanished old group, without killing any real process.
        with mock.patch.object(os, "killpg", side_effect=ProcessLookupError):
            result = at.search(at.SearchStrategy("grid", evaluator.space), evaluator, 1)
        self.assertIsNone(result["compile_wall_s"])
        self.assertEqual(result["compile_wall_recorded_s"], 0)
        self.assertEqual(result["incomplete_builds"], 1)
        self.assertIsNone(result["tuning_wall_s"])
        self.assertEqual(result["incomplete_sessions"], 1)

    def test_start_log_failure_cleans_spawned_process(self):
        started = []
        def fail(record):
            started.append(record["pid"])
            raise OSError("test-only simulated disk failure")
        with self.assertRaises(OSError):
            at.process([sys.executable, "-c", "import time; time.sleep(2)"], 3, fail)
        with self.assertRaises(ProcessLookupError):
            os.killpg(started[0], 0)

    def test_compile_timeout(self):
        compiler = self.directory / "compiler-fixture"
        compiler.write_text('#!/bin/sh\nif [ "$1" = "--version" ]; then echo fixture; '
                            'else sleep 2; fi\n')
        compiler.chmod(0o755)
        self.target = at.TargetProgram(self.source, compiler=str(compiler),
                                       cache_dir=self.target.cache_dir, compile_timeout=.05)
        evaluator = self.evaluator("compile-timeout")
        result = at.search(at.SearchStrategy("grid", evaluator.space), evaluator, 1)
        self.assertEqual(result["failed_builds"], 1)
        build = next(r for r in evaluator.journal.records if r["type"] == "build")
        self.assertEqual(build["status"], "timeout")
        with self.assertRaises(ProcessLookupError):
            os.killpg(build["compile"]["pid"], 0)

    def test_cli_sigterm_records_interrupt_and_stops_target(self):
        self.source.write_text('#include <unistd.h>\nint main(void) { sleep(2); return 0; }\n')
        output = self.directory / "sigterm.jsonl"
        command = [sys.executable, str(Path(at.__file__)), "run", "--target", str(self.source),
                   "--s", "8", "--opt", "O0", "--output", str(output),
                   "--cache-dir", str(self.target.cache_dir)]
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: child.kill() if child.poll() is None else None)
        deadline = time.monotonic() + 5
        records = []
        while time.monotonic() < deadline:
            if output.exists():
                records = [json.loads(line) for line in output.read_text().splitlines()]
                if any(r["type"] == "measurement_start" for r in records):
                    break
            time.sleep(.01)
        self.assertTrue(any(r["type"] == "measurement_start" for r in records))
        child.send_signal(signal.SIGTERM)
        stdout, stderr = child.communicate(timeout=3)
        self.assertEqual(child.returncode, 130, (stdout, stderr))
        records = [json.loads(line) for line in output.read_text().splitlines()]
        measurement = next(r for r in records if r["type"] == "measurement")
        self.assertEqual(measurement["status"], "interrupted")
        with self.assertRaises(ProcessLookupError):
            os.killpg(measurement["pid"], 0)

    def test_cli_real_run_and_fingerprint_rejects_changed_repeats(self):
        path = self.directory / "cli.jsonl"
        args = ["run", "--target", str(self.source), "--cache-dir", str(self.target.cache_dir),
                "--output", str(path), "--s", "24", "--opt", "O1", "--timeout", "2"]
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(at.main(args), 0)
        self.assertEqual(json.loads(output.getvalue())["best"]["score"], .24)
        header = json.loads(path.read_text().splitlines()[0])
        self.assertEqual(header["metadata"]["target"]["source_sha256"], at.digest(self.source.read_bytes()))
        self.assertIsNone(header["metadata"]["target"]["n"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            at.main([*args, "--resume", "--repeats", "2"])

    def test_build_action_resume_refuses_unrecorded_live_compiler(self):
        path = self.directory / "build-cli.jsonl"
        args = ["build", "--target", str(self.source), "--cache-dir", str(self.target.cache_dir),
                "--output", str(path), "--opts", "O0"]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(at.main(args), 0)
        records = [json.loads(line) for line in path.read_text().splitlines()]
        start = next(r for r in records if r["type"] == "build_start")
        start["pid"] = os.getpgrp()
        path.write_text(json.dumps(records[0]) + "\n" + json.dumps(start) + "\n")
        shutil.rmtree(self.target.cache_dir)
        with contextlib.redirect_stderr(io.StringIO()) as error, self.assertRaises(SystemExit):
            at.main([*args, "--resume"])
        self.assertIn("still present", error.getvalue())
        self.assertEqual(len(path.read_text().splitlines()), 2)

    def test_build_action_interrupt_stops_further_compilation(self):
        path = self.directory / "build-interrupt.jsonl"
        with mock.patch.object(at.TargetProgram, "build", return_value={"status": "interrupted"}) as build:
            with contextlib.redirect_stderr(io.StringIO()):
                result = at.main(["build", "--target", str(self.source), "--output", str(path)])
        self.assertEqual(result, 130)
        self.assertEqual(build.call_count, 1)


if __name__ == "__main__":
    unittest.main()
