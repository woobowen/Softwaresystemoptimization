"""S3 uses fresh online processes; fixtures here never become experiment data."""

import contextlib
import io
import json
import math
import os
from pathlib import Path
import random
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import autotuner as at


class Goal2StrategyTests(unittest.TestCase):
    def strategy(self, budget=8, space=None, seed=17):
        return at.SearchStrategy("recheck", space or at.ConfigSpace(), seed, budget=budget)

    def explore(self, strategy, scores):
        configs = []
        for score in scores:
            config = strategy.suggest()
            configs.append(config)
            strategy.observe(config, score)
        return configs

    def test_same_random_prefix_and_no_free_exploration(self):
        strategy = self.strategy()
        random_order = at.SearchStrategy("random", strategy.space, 17).order
        configs = self.explore(strategy, [8, 7, 6, 5, 4, 3])
        self.assertEqual(configs, random_order[:6])
        self.assertEqual(strategy.finalists, [configs[5], configs[4]])
        for config in strategy.finalists:
            self.assertEqual(strategy.suggest(), config)
            strategy.observe(config, 10)
        self.assertIsNone(strategy.suggest())
        self.assertEqual(len(strategy.first_scores), 6)
        self.assertEqual(len(strategy.rechecked), 2)

    def test_recheck_can_raise_best_and_replace_first_sample_winner(self):
        strategy = self.strategy()
        configs = self.explore(strategy, [1, 2, 10, 11, 12, 13])
        self.assertEqual(strategy.best()["score"], 1)
        strategy.observe(strategy.suggest(), 100)
        self.assertEqual(strategy.scores[configs[0]], 50.5)
        self.assertEqual(strategy.best()["score"], 50.5)
        strategy.observe(strategy.suggest(), 2)
        self.assertEqual(strategy.best(require_review=True), dict(config=at.asdict(configs[1]), score=2))
        self.assertNotIn(configs[2], strategy.rechecked)

    def test_finalists_and_final_ties_follow_visit_order(self):
        strategy = self.strategy()
        configs = self.explore(strategy, [2, 1, 1, 1, 3, 4])
        self.assertEqual(strategy.finalists, [configs[1], configs[2]])
        strategy.observe(strategy.suggest(), 3)
        strategy.observe(strategy.suggest(), 3)
        self.assertEqual(strategy.best(require_review=True)["config"], at.asdict(configs[1]))

    def test_failures_consume_slots_and_invalidate_rechecked_candidate(self):
        strategy = self.strategy()
        configs = self.explore(strategy, [None, 1, 2, 3, 4, None])
        self.assertEqual(strategy.finalists, [configs[1], configs[2]])
        strategy.observe(strategy.suggest(), None)
        self.assertIsNone(strategy.best())
        self.assertIsNone(strategy.scores[configs[1]])
        self.assertEqual(strategy.config_samples[configs[1]], [1])
        strategy.observe(strategy.suggest(), 10)
        self.assertEqual(strategy.best(require_review=True)["config"], at.asdict(configs[2]))
        self.assertIsNone(strategy.suggest())

    def test_no_valid_finalists_or_one_finalist_do_not_fill_budget(self):
        failed = self.strategy()
        self.explore(failed, [None] * 6)
        self.assertEqual(failed.finalists, [])
        self.assertIsNone(failed.suggest())
        self.assertIsNone(failed.best(require_review=True))
        single = self.strategy()
        configs = self.explore(single, [None, None, 1, None, None, None])
        single.observe(single.suggest(), 3)
        self.assertIsNone(single.suggest())
        self.assertEqual(single.best(require_review=True), dict(config=at.asdict(configs[2]), score=2))

    def test_small_space_and_minimum_budget(self):
        for count in (1, 2):
            space = at.ConfigSpace((8,), at.OPTS[:count])
            strategy = self.strategy(4, space)
            self.explore(strategy, [1] * count)
            for _ in range(count):
                strategy.observe(strategy.suggest(), 2)
            self.assertIsNone(strategy.suggest())
            self.assertEqual(len(strategy.rechecked), count)
        for budget in (None, 0, 1, 3, True, 4.0):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                at.SearchStrategy("recheck", at.ConfigSpace(), budget=budget)

    def test_feedback_contract_nonfinite_and_no_external_observation(self):
        strategy = self.strategy()
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                strategy.observe(strategy.suggest(), value)
        with self.assertRaises(ValueError):
            strategy.observe(strategy.order[1], 1)
        self.explore(strategy, [1] * 6)
        for _ in range(2):
            strategy.observe(strategy.suggest(), 1)
        with self.assertRaises(ValueError):
            strategy.observe(strategy.order[0], .001)

    def test_restore_replays_fresh_scores_instead_of_aggregates(self):
        original = self.strategy()
        feedback = [1, 2, 3, 4, 5, 6, 100, 2]
        history = []
        for score in feedback:
            config = original.suggest()
            history.append((config, score))
            original.observe(config, score)
        restored = self.strategy()
        for config, score in history[:7]:
            restored.observe(config, score)
        self.assertEqual(restored.suggest(), history[-1][0])
        restored.observe(*history[-1])
        self.assertEqual(restored.config_samples, original.config_samples)
        self.assertEqual(restored.best(require_review=True), original.best(require_review=True))

    def test_explicit_greedy_start_changes_only_diagnostic_start(self):
        space = at.ConfigSpace()
        chosen = at.Config(8, "O0")
        self.assertEqual(at.SearchStrategy("greedy", space, 17, start=chosen).suggest(), chosen)
        self.assertEqual(at.SearchStrategy("greedy", space, 17).suggest(), random.Random(17).choice(space.configs))
        with self.assertRaises(ValueError):
            at.SearchStrategy("random", space, start=chosen)
        with self.assertRaises(ValueError):
            at.SearchStrategy("greedy", space, start=at.Config(32, "O0"))


class Goal2ClockTests(unittest.TestCase):
    def test_ns_time_domains_remain_separate_and_children_cpu_is_not_wall(self):
        names = ("CLOCK_MONOTONIC", "CLOCK_MONOTONIC_RAW", "CLOCK_REALTIME")
        begin = {name: 10 ** 18 + i for i, name in enumerate(names)}
        end = dict(zip(names, (begin[names[0]] + 1_000_000_000,
                              begin[names[1]] + 2_000_000_000,
                              begin[names[2]] - 3_000_000_000)))
        usage = [mock.Mock(ru_utime=4, ru_stime=2), mock.Mock(ru_utime=4.2, ru_stime=2.1)]
        with mock.patch.object(at, "clock_readings_ns", side_effect=[begin, end]), \
                mock.patch.object(at.resource, "getrusage", side_effect=usage):
            result = at.process([sys.executable, "-c", "print('short clock fixture')"], 2)
        self.assertEqual(result["process_wall_s"], 1)
        self.assertEqual(result["process_wall_clock"], "CLOCK_MONOTONIC")
        self.assertEqual(result["clock_read_order"], list(names))
        self.assertEqual(result["clock_start_ns"], begin)
        self.assertEqual(result["boundary_read_order"], dict(start=[*names, "RUSAGE_CHILDREN"],
            end=["RUSAGE_CHILDREN", *names]))
        self.assertEqual(result["child_cpu_start_s"], dict(user=4, system=2))
        self.assertEqual(result["child_cpu_end_s"], dict(user=4.2, system=2.1))
        self.assertEqual(result["clock_deltas_s"]["CLOCK_MONOTONIC_RAW"], 2)
        self.assertEqual(result["clock_deltas_s"]["CLOCK_REALTIME"], -3)
        self.assertAlmostEqual(result["child_user_cpu_s"], .2)
        self.assertAlmostEqual(result["child_system_cpu_s"], .1)

    def test_actual_subprocess_clock_units_and_fields(self):
        result = at.process([sys.executable, "-c", "print('fresh process')"], 2)
        self.assertEqual(result["status"], "ok")
        for name in result["clock_read_order"]:
            self.assertIsInstance(result["clock_start_ns"][name], int)
            self.assertIsInstance(result["clock_end_ns"][name], int)
            self.assertEqual(result["clock_deltas_s"][name],
                (result["clock_end_ns"][name] - result["clock_start_ns"][name]) / 1e9)
        self.assertGreater(result["process_wall_s"], 0)
        self.assertGreaterEqual(result["child_user_cpu_s"], 0)


@unittest.skipUnless(shutil.which("gcc"), "gcc is required for fresh subprocess fixtures")
class Goal2ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "fixture.c"
        self.source.write_text('#include <stdio.h>\n#include <stdlib.h>\n'
            'int main(int argc, char **argv) { if(argc != 2) return 2;\n'
            'printf("%.6f\\nchecksum=1\\n", atoi(argv[1])/100.0); return 0; }\n')
        self.target = at.TargetProgram(self.source, cache_dir=self.directory / "build")
        self.space = at.ConfigSpace()

    def evaluator(self, name, resume=False, repeats=1):
        journal = at.Journal(self.directory / (name + ".jsonl"), {"fixture": name}, resume)
        self.addCleanup(journal.close)
        return at.Evaluator(self.target, self.space, journal, repeats, 2)

    def strategy(self):
        return at.SearchStrategy("recheck", self.space, 17, budget=8)

    def test_actual_rechecks_cost_calls_and_log_only_online_samples(self):
        evaluator = self.evaluator("actual")
        result = at.search(self.strategy(), evaluator, 8)
        rows = evaluator.journal.records
        trials = [row for row in rows if row["type"] == "trial"]
        starts = [row for row in rows if row["type"] == "measurement_start"]
        self.assertEqual((result["process_runs"], result["distinct_configs"], result["proposals"]), (8, 6, 8))
        self.assertEqual((result["exploration_trials"], result["recheck_trials"]), (6, 2))
        self.assertEqual(len({row["pid"] for row in starts}), 8)
        self.assertTrue(all(len(row["samples"]) == 1 for row in trials))
        self.assertTrue(all(len(row["config_samples"]) == 2 and row["return_eligible"] for row in trials[-2:]))
        self.assertEqual(result["best"], trials[-1]["best_so_far"])
        self.assertTrue(all(math.isfinite(row["score"]) for row in trials))
        self.assertEqual(at.search(self.strategy(), evaluator, 8), result)

    def test_recheck_call_budget_repeats_and_mismatch_refused(self):
        with self.assertRaises(ValueError):
            at.search(self.strategy(), self.evaluator("repeat", repeats=2), 8)
        with self.assertRaises(ValueError):
            at.search(self.strategy(), self.evaluator("budget"), 7)
        evaluator = self.evaluator("feedback")
        strategy = self.strategy()
        with mock.patch.object(self.target, "build", side_effect=AssertionError("must not build")):
            with self.assertRaises(ValueError):
                evaluator.evaluate(strategy.order[1], 0, strategy)
            with self.assertRaises(ValueError):
                evaluator.evaluate(strategy.order[0], 0, at.SearchStrategy("random", self.space, 17))

    def test_interrupt_between_finalist_calls_resumes_without_double_counting(self):
        evaluator = self.evaluator("resume")
        original = self.target.measure
        calls = 0
        def stop_after_first_finalist(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 8:
                raise KeyboardInterrupt
            return original(*args, **kwargs)
        with mock.patch.object(self.target, "measure", stop_after_first_finalist), self.assertRaises(KeyboardInterrupt):
            at.search(self.strategy(), evaluator, 8)
        prefix = [row for row in evaluator.journal.records if row["type"] == "trial"]
        self.assertEqual(len(prefix), 7)
        evaluator.journal.close()
        resumed = self.evaluator("resume", resume=True)
        result = at.search(self.strategy(), resumed, 8)
        self.assertEqual(result["process_runs"], 8)
        self.assertEqual(result["recheck_trials"], 2)
        self.assertEqual([row for row in resumed.journal.records if row["type"] == "trial"][:7], prefix)
        self.assertEqual(result["eligible_configs"], 2)

    def test_lost_completion_is_failed_and_not_given_a_free_call(self):
        evaluator = self.evaluator("orphan")
        strategy = self.strategy()
        for trial_id in range(7):
            evaluator.evaluate(strategy.suggest(), trial_id, strategy)
        config = strategy.suggest()
        evaluator.journal.append("trial_start", trial_id=7, config=at.asdict(config))
        evaluator.journal.append("measurement_start", trial_id=7, config=at.asdict(config),
            repeat=0, spawned=True, command=["test-only lost completion"], started_at=at.now())
        evaluator.journal.close()
        resumed = self.evaluator("orphan", resume=True)
        with mock.patch.object(self.target, "measure", side_effect=AssertionError("must not rerun")):
            result = at.search(self.strategy(), resumed, 8)
        self.assertEqual(result["process_runs"], 8)
        self.assertEqual(result["failed_runs"], 1)
        self.assertEqual(result["recheck_trials"], 2)
        self.assertEqual(result["eligible_configs"], 1)
        self.assertIsNotNone(result["best"])

    def test_same_domain_guard_and_unmatched_domains_not_compared(self):
        self.target.kernel_clock = "CLOCK_MONOTONIC"
        self.target.build("O0")
        fixture = dict(command=["test-only clock-domain fixture"], started_at=at.now(), ended_at=at.now(),
            spawned=True, stdout="1.0\nchecksum=1\n", stderr="", returncode=0, status="ok", error=None,
            process_wall_s=.01, process_wall_clock="CLOCK_MONOTONIC_RAW")
        config = at.Config(8, "O0")
        with mock.patch.object(at, "process", return_value=fixture.copy()):
            result = self.target.measure(self.target.build("O0"), config, 2)
        self.assertEqual(result["status"], "ok")
        fixture["process_wall_clock"] = "CLOCK_MONOTONIC"
        with mock.patch.object(at, "process", return_value=fixture.copy()):
            result = self.target.measure(self.target.build("O0"), config, 2)
        self.assertEqual(result["status"], "clock_error")

    def test_schema_two_options_and_resume_fingerprints(self):
        for algorithm, extra in (("recheck", []), ("greedy", ["--start-s", "8", "--start-opt", "O0"])):
            output = self.directory / (algorithm + "-cli.jsonl")
            args = ["search", "--target", str(self.source), "--cache-dir", str(self.target.cache_dir),
                "--output", str(output), "--algorithm", algorithm, "--budget", "8", "--seed", "17", *extra]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(at.main(args), 0)
            metadata = json.loads(output.read_text().splitlines()[0])["metadata"]
            self.assertEqual(metadata["schema"], 2)
            if algorithm == "recheck":
                self.assertEqual(metadata["recheck"]["exploration_trials"], 6)
                changes = ["--budget", "9"]
            else:
                self.assertEqual(metadata["greedy_start"], {"s": 8, "opt": "O0"})
                changes = ["--start-s", "16"]
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                at.main([*args, "--resume", *changes])

    def test_cli_rejects_incomplete_start_and_recheck_free_repeats(self):
        for args in (["search", "--algorithm", "recheck", "--budget", "3"],
                     ["search", "--algorithm", "recheck", "--repeats", "2"],
                     ["search", "--algorithm", "greedy", "--start-s", "8"],
                     ["search", "--algorithm", "random", "--start-s", "8", "--start-opt", "O0"]):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                at.main(args)


if __name__ == "__main__":
    unittest.main()
