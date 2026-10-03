"""Small synthetic raw inputs stay in temporary caches, away from formal results."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

P1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P1 / "scripts"))
import goal2r_analysis as analysis


class Goal2RAnalysisTests(unittest.TestCase):
    def setUp(self):
        (P1 / ".cache").mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=P1 / ".cache")
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def clock_fixture(self):
        def reading(raw, tick):
            return dict(before_ns=dict(RAW=raw, MONOTONIC=raw, REALTIME=raw),
                        after_ns=dict(RAW=raw + 1000, MONOTONIC=raw + 50000000, REALTIME=raw - 100000000),
                        host_tick=tick, frequency_hz=1000000, host_pid=45, host_managed_thread_id=1)
        rows = []
        for index, phase in enumerate(("before", "after")):
            offset = index * 20000000000
            first, last = reading(offset + 1000000000, 1000000), reading(offset + 11000000000, 11000000)
            data = dict(complete=True, lifecycle_valid=True, host_frequency_hz=1000000, host_pid=45,
                        host_managed_thread_id=1, intervals=[dict(first=first, last=last)])
            raw = self.root / f"clock-{phase}.json"
            raw.write_text(json.dumps(data))
            rows.append(dict(type="clock_block_check", block_id="seed-1", phase=phase, valid=True,
                        raw_path=str(raw.relative_to(P1)), sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                        protocol_sha256="new", boot_id="boot", attempt_id=phase))
        (self.root / "block_checks.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
        starts = {phase:dict(boot_id="boot", clock_start_ns=dict(raw=index * 20000000000))
                  for index, phase in enumerate(("before", "after"))}
        ends = {phase:dict(clock_end_ns=dict(raw=index * 20000000000 + 12000000000))
                for index, phase in enumerate(("before", "after"))}
        return json.loads((self.root / "clock-before.json").read_text()), self.root / "clock-before.json", rows, starts, ends

    def test_raw_clock_is_not_vetoed_by_auxiliary_backwards_or_width(self):
        _, _, _, starts, ends = self.clock_fixture()
        blocks, checks = analysis.clock_checks(self.root, "new", starts, ends)
        self.assertTrue(blocks["seed-1"]["valid"])
        self.assertEqual(blocks["seed-1"]["raw_begin_ns"], 12000000000)
        self.assertEqual(blocks["seed-1"]["raw_end_ns"], 20000000000)
        self.assertEqual(len(checks), 2)

    def test_clock_source_hash_or_boot_change_cannot_pass(self):
        _, raw, _, starts, ends = self.clock_fixture()
        raw.write_text(raw.read_text() + " ")
        with self.assertRaises(ValueError):
            analysis.clock_checks(self.root, "new", starts, ends)
        self.clock_fixture()
        starts["after"]["boot_id"] = "other-boot"
        with self.assertRaises(ValueError):
            analysis.clock_checks(self.root, "new", starts, ends)

    def test_old_qpc_interval_cannot_be_relabelled_as_later_check(self):
        _, _, rows, starts, ends = self.clock_fixture()
        rows[1].update(raw_path=rows[0]["raw_path"], sha256=rows[0]["sha256"])
        (self.root / "block_checks.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
        with self.assertRaises(ValueError):
            analysis.clock_checks(self.root, "new", starts, ends)

    def test_shared_panel_cost_is_once_and_unknown_not_complete(self):
        journal = self.root / "panel.jsonl"
        journal.write_text("{\"type\":\"measurement_start\"}\n{\"type\":\"measurement_start\"}\n")
        starts = dict(type="task_start", attempt_id="one", task="shared", role="shared_confirmation",
                      journal=str(journal.relative_to(P1)), boot_id="boot",
                      clock_start_ns=dict(raw=0, monotonic=0, realtime=0))
        end = dict(type="task_end", attempt_id="one", task="shared", role="shared_confirmation",
                   n4096_calls=2, n4096_calls_known=True, returncode=0, reason=None,
                   clock_end_ns=dict(raw=2000000000, monotonic=1000000000, realtime=-100000000000),
                   clock_elapsed_s=dict(raw=2, monotonic=1, realtime=-100), driver_raw_s=2,
                   driver_wall_s=1, resource_s=2, resource_wall_s=2, resource_clock="CLOCK_MONOTONIC_RAW")
        path = self.root / "ledger.jsonl"
        path.write_text(json.dumps(starts) + "\n" + json.dumps(end) + "\n")
        cost, _, _ = analysis.project_costs(path)
        self.assertEqual((cost["n4096_calls"], cost["resource_s"]), (2, 2))
        self.assertTrue(cost["complete"])
        pending = dict(starts, attempt_id="pending", task="unfinished")
        closed = path.read_text()
        path.write_text(closed + json.dumps(pending) + "\n")
        cost, _, _ = analysis.project_costs(path)
        self.assertFalse(cost["complete"])
        path.write_text(closed)
        path.write_text(path.read_text() + json.dumps(end) + "\n")
        with self.assertRaises(ValueError):
            analysis.project_costs(path)

    def test_same_choice_still_needs_three_real_panel_rounds(self):
        searches = [dict(stage="comparison", seed=1, algorithm=name, block=1, returned_s=128,
                         returned_opt="O2", valid=True, process_runs=8, search_driver_raw_s=100)
                    for name in ("random", "recheck")]
        samples = [dict(stage="comparison", seed=1, role="shared_confirmation", round=r, s=128,
                        opt="O2", kernel_s=t, valid=True) for r, t in ((1, 40), (2, 43), (3, 37))]
        pair = analysis.comparisons(searches, samples, dict(s=128, opt="O2"), "comparison", [1])[0]
        self.assertTrue(pair["valid"])
        self.assertEqual(pair["gain_panel_rounds_pp"], [0, 0, 0])
        pair = analysis.comparisons(searches, samples[:2], dict(s=128, opt="O2"), "comparison", [1])[0]
        self.assertFalse(pair["valid"])

    def test_failed_addition_preserves_original_request(self):
        seeds = list(range(1, 7))
        searches, samples = [], []
        for seed in seeds:
            for name, s in (("random", 16), ("recheck", 128)):
                searches.append(dict(stage="comparison", seed=seed, algorithm=name, block=seed,
                    returned_s=s, returned_opt="O2", valid=True, process_runs=8, search_driver_raw_s=100))
            for round_id, gain in enumerate((-3, 0, 1), 1):
                for s, value in ((16, 40 * (1 + gain / 100)), (128, 40)):
                    samples.append(dict(stage="comparison", seed=seed, role="shared_confirmation",
                        round=round_id, s=s, opt="O2", kernel_s=value, valid=True))
        reference = dict(s=128, opt="O2")
        original = analysis.comparisons(searches, samples, reference, "comparison", seeds)
        self.assertEqual(analysis.confirmation_additions(original), [1, 2])
        for round_id in (4, 5):
            for s in (16, 128):
                samples.append(dict(stage="comparison", seed=1, role="shared_confirmation",
                    round=round_id, s=s, opt="O2", kernel_s=40, valid=False))
            combined = analysis.comparisons(searches, samples, reference, "comparison", seeds)
            self.assertFalse(analysis.goal2r_decision(combined, 6)["evaluation_complete"])
            base = analysis.comparisons(searches, [r for r in samples if r["round"] <= 3],
                                        reference, "comparison", seeds)
            self.assertEqual(base, original)
            self.assertEqual(analysis.confirmation_additions(base), [1, 2])


if __name__ == "__main__":
    unittest.main()
