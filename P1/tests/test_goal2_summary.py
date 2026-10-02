"""Synthetic counterexamples for Goal 2 analysis; fixtures never enter results/."""

import copy
import json
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest import mock

P1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P1 / "scripts"))
import summarize_v2 as su


def protocol(rho=1):
    data = json.loads((P1 / "evidence/protocol_v2.json").read_text())
    data["state"] = "approved"
    data["acceptance"]["state"] = "frozen"
    data["measurement"]["clock_health"]["resolution_pp"] = rho
    return data


def paired(gain=0, saving=.1, same=True):
    return dict(valid=True, same_config=same, gain_ref_pp=gain,
        gain_ref_low_pp=gain, gain_ref_high_pp=gain,
        gain_panel_low_pp=gain, gain_panel_high_pp=gain,
        reference_panel_conflict=False, wall_saving_fraction=saving,
        baseline_calls=8, candidate_calls=8)


def metadata(name="recheck", budget=8):
    return dict(algorithm=name, seed=7, blocks=[8, 16, 24, 64, 128],
                opts=["O0", "O1", "O2", "O3"], budget=budget, repeats=1)


def random_order(meta):
    configs = [dict(s=s, opt=opt) for s in meta["blocks"] for opt in meta["opts"]]
    random.Random(meta["seed"]).shuffle(configs)
    return configs


def aa_fixture():
    jobs = json.loads((P1 / "evidence/protocol_diagnostic.json").read_text())["diagnostic_jobs"]
    samples = []
    for job in jobs:
        value = 40 if job["tier"] == "F" else 60
        if job["label"] == "B":
            value *= 1.1 if job["method"] == "M0" else 1.005
        samples.append(dict(role=job["role"], block=job["block"], method=job["method"], tier=job["tier"],
            label=job["label"], pair=job["pair"], **job["config"], kernel_s=value, valid=True))
    return samples


def synthetic_task():
    meta = dict(metadata("grid", 1), target=dict(kernel_clock="CLOCK_MONOTONIC", require_checksum=True,
        source_sha256="fixture-source", compiler={"path": "fixture-compiler"}, flags=["-std=c11"]))
    meta.update(blocks=[8], opts=["O2"])
    config = dict(s=8, opt="O2")
    identity = dict(meta["target"], flags=["-std=c11", "-O2"])
    build = dict(type="build", trial_id=0, config=config, status="ok", opt="O2",
        source_sha256="fixture-source", compiler=meta["target"]["compiler"], flags=identity["flags"],
        build_key=su.ex.at.fingerprint(identity), binary="fixture-binary", binary_sha256="fixture-hash",
        cached=True, compile_wall_s=0)
    measurement = dict(type="measurement", trial_id=0, repeat=0, config=config, spawned=True,
        command=["fixture-binary", "8"], pid=123, status="ok", returncode=0,
        kernel_s=1, kernel_unit="s", kernel_clock="CLOCK_MONOTONIC",
        process_wall_s=1.1, process_wall_clock="CLOCK_MONOTONIC", clock_unit="ns",
        clock_start_ns={name: 10000000000 for name in ("CLOCK_MONOTONIC", "CLOCK_MONOTONIC_RAW", "CLOCK_REALTIME")},
        clock_end_ns={name: 11100000000 for name in ("CLOCK_MONOTONIC", "CLOCK_MONOTONIC_RAW", "CLOCK_REALTIME")},
        clock_deltas_s={name: 1.1 for name in ("CLOCK_MONOTONIC", "CLOCK_MONOTONIC_RAW", "CLOCK_REALTIME")},
        stdout="1.000000\nchecksum=4096\n", checksum=4096, build_key=build["build_key"], binary_sha256="fixture-hash")
    best = dict(config=config, score=1)
    summary = dict(type="summary", best=best, stop_reason="budget", proposals=1, attempted_trials=1,
        process_runs=1, distinct_configs=1, failed_runs=0, failed_trials=0, completed_configs=1,
        interrupted_runs=0, compile_wall_s=0, compile_processes=0, incomplete_builds=0,
        cached_builds=1, tuning_wall_s=2)
    records = [dict(type="header", metadata=meta, fingerprint=su.ex.at.fingerprint(meta)),
        dict(type="session_start"), dict(type="trial_start", trial_id=0, config=config), build,
        dict(type="measurement_start", trial_id=0, repeat=0, config=config, spawned=True,
             command=measurement["command"], pid=123), measurement,
        dict(type="trial", trial_id=0, config=config, samples=[1], status="ok", score=1, best_so_far=best),
        dict(type="session_end", wall_s=2), summary]
    for row in records:
        row["run_id"] = "synthetic-unit-fixture-only"
    return dict(records=records, summary=summary)


class Goal2ReplayTests(unittest.TestCase):
    def test_failed_batch_remains_failed_and_forged_metadata_is_rejected(self):
        task = synthetic_task()
        measurement = task["records"][5]
        measurement.update(status="nonzero", returncode=1, kernel_s=None, stdout="", checksum=None)
        task["records"][6].update(status="failed", samples=[], score=None, best_so_far=None)
        task["summary"].update(best=None, failed_runs=1, failed_trials=1, completed_configs=0)
        meta = copy.deepcopy(task["records"][0]["metadata"])
        job = dict(id="fixture-failure", action="run", role="aa", config=dict(s=8, opt="O2"), repeats=1, seed=7)
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw"
            raw.mkdir()
            (raw / "plan.json").write_text(json.dumps(dict(measurement_root=str(P1), protocol="fixture.json", stage="diagnostic", jobs=[job])))
            proto = Path(directory) / "fixture.json"
            proto.write_text(json.dumps(protocol()))
            journal = raw / "fixture-failure.jsonl"
            journal.write_text("".join(json.dumps(row) + "\n" for row in task["records"]))
            with mock.patch.object(su.ex, "freeze_check"), mock.patch.object(su.ex, "common_metadata", return_value=meta):
                batch = su.read_batch(raw, proto)
                self.assertEqual(batch["tasks"][0]["state"], "failed")
                self.assertFalse(su.samples_from_batches([batch])[0]["valid"])
                task["records"][0]["metadata"]["seed"] = 99
                task["records"][0]["fingerprint"] = su.ex.at.fingerprint(task["records"][0]["metadata"])
                journal.write_text("".join(json.dumps(row) + "\n" for row in task["records"]))
                with self.assertRaises(ValueError):
                    su.read_batch(raw, proto)

    def test_raw_replay_rejects_backfilled_best_and_missing_process(self):
        su.check_trials(synthetic_task())
        for mutate in ("best", "process", "run_id", "build", "cost"):
            task = copy.deepcopy(synthetic_task())
            if mutate == "best":
                task["summary"]["best"] = dict(config=dict(s=8, opt="O2"), score=.5)
            elif mutate == "process":
                task["records"] = [row for row in task["records"] if row["type"] != "measurement_start"]
            elif mutate == "run_id":
                task["records"][4]["run_id"] = "other-search"
            elif mutate == "build":
                task["records"][3]["flags"] = ["-O3"]
            else:
                task["summary"]["compile_wall_s"] = 1
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                su.check_trials(task)

    def test_clock_units_domains_and_nan_do_not_create_a_fastest_sample(self):
        task = synthetic_task()
        row, meta = task["records"][5], task["records"][0]["metadata"]
        self.assertTrue(su.valid_measurement(row, meta))
        for change in (dict(clock_unit="us"), dict(kernel_unit="ns"), dict(process_wall_clock="RAW"),
                       dict(stdout="0.5\nchecksum=4096\n"), dict(checksum=1)):
            damaged = dict(row, **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                su.valid_measurement(damaged, meta)
        self.assertFalse(su.valid_measurement(dict(row, kernel_s=math.nan), meta))
        self.assertFalse(su.valid_measurement(dict(row, kernel_s=2), meta))
        other_meta = copy.deepcopy(meta)
        other_meta["target"]["kernel_clock"] = "CLOCK_MONOTONIC_RAW"
        other = dict(row, kernel_s=2, kernel_clock="CLOCK_MONOTONIC_RAW", stdout="2\nchecksum=4096\n")
        self.assertTrue(su.valid_measurement(other, other_meta))

    def test_recheck_recomputes_best_upward_and_preserves_random_prefix(self):
        meta = metadata()
        order = random_order(meta)
        observations = [dict(config=c, fresh_score=v) for c, v in zip(order[:6], [1, 2, 3, 4, 5, 6])]
        observations += [dict(config=order[0], fresh_score=11), dict(config=order[1], fresh_score=2)]
        result = su.replay_observations(meta, observations)
        self.assertEqual(result["trace"][5]["best_so_far"]["score"], 1)
        self.assertEqual(result["trace"][6]["best_so_far"]["score"], 6)
        self.assertEqual(result["best"], dict(config=order[1], score=2))
        self.assertEqual((result["exploration_trials"], result["recheck_trials"], result["eligible_configs"]), (6, 2, 2))

    def test_recheck_failure_is_ineligible_without_extra_free_exploration(self):
        meta, order = metadata(), random_order(metadata())
        observations = [dict(config=c, fresh_score=1) for c in order[:6]]
        observations += [dict(config=order[0], fresh_score=None), dict(config=order[1], fresh_score=2)]
        result = su.replay_observations(meta, observations)
        self.assertFalse(result["trace"][6]["return_eligible"])
        self.assertEqual(result["best"]["config"], order[1])
        with self.assertRaises(ValueError):
            su.replay_observations(meta, observations + [dict(config=order[6], fresh_score=1)])

    def test_zero_or_one_finalist_stops_without_padding(self):
        meta, order = metadata(), random_order(metadata())
        failed = [dict(config=c, fresh_score=None) for c in order[:6]]
        result = su.replay_observations(meta, failed)
        self.assertTrue(result["exhausted"])
        self.assertIsNone(result["best"])
        failed[2]["fresh_score"] = 3
        result = su.replay_observations(meta, failed + [dict(config=order[2], fresh_score=4)])
        self.assertEqual(result["eligible_configs"], 1)
        self.assertEqual(result["best"]["score"], 3.5)

    def test_final_tie_uses_original_visit_order(self):
        meta, order = metadata(), random_order(metadata())
        observations = [dict(config=c, fresh_score=1) for c in order[:6]]
        observations += [dict(config=order[0], fresh_score=3), dict(config=order[1], fresh_score=3)]
        result = su.replay_observations(meta, observations)
        self.assertEqual(result["best"]["config"], order[0])

    def test_base_order_and_greedy_explicit_start_are_independently_replayed(self):
        meta = metadata("grid")
        result = su.replay_observations(meta, [dict(config=dict(s=8, opt="O0"), fresh_score=5),
                                               dict(config=dict(s=8, opt="O1"), fresh_score=4)])
        self.assertEqual(result["best"]["score"], 4)
        with self.assertRaises(ValueError):
            su.replay_observations(meta, [dict(config=dict(s=128, opt="O3"), fresh_score=1)])
        meta = metadata("greedy")
        meta["greedy_start"] = dict(s=24, opt="O2")
        result = su.replay_observations(meta, [dict(config=meta["greedy_start"], fresh_score=1)])
        self.assertEqual(result["best"]["config"], meta["greedy_start"])

    def test_nonfinite_zero_and_invalid_recheck_contract_are_rejected(self):
        for value in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                su.describe([value])
        with self.assertRaises(ValueError):
            su.replay_observations(metadata(budget=3), [])


class Goal2QualityTests(unittest.TestCase):
    def test_partial_shared_panel_cannot_confirm_same_reference_identity(self):
        task = synthetic_task()
        task.update(state="complete", job=dict(id="search", action="search", role="search",
            block=1, algorithm="random", seed=700001))
        batch = dict(path=Path("unit-fixture"), manifest=dict(stage="comparison"), tasks=[task], driver=[])
        grid = [dict(s=8, opt="O2", gap_ref_pct=0, **su.describe([1, 1, 1]))]
        panel = dict(stage="comparison", block=1, s=8, opt="O2", complete=False, **su.describe([1]))
        rows, _ = su.search_tables([batch], grid, [panel], protocol())
        self.assertEqual(rows[0]["gap_ref_pct"], 0)
        self.assertEqual(rows[0]["quality_class"], "uncertain")
        self.assertIsNone(rows[0]["panel_gap_high_pct"])
        self.assertFalse(rows[0]["confirmation_complete"])
        missing_anchor_grid = [dict(s=8, opt="O1", gap_ref_pct=0, **su.describe([.9, .9, .9])),
            dict(s=8, opt="O2", gap_ref_pct=100/9, **su.describe([1, 1, 1]))]
        complete_return = dict(panel, complete=True, **su.describe([1, 1, 1]))
        missing, _ = su.search_tables([batch], missing_anchor_grid, [complete_return], protocol())
        self.assertFalse(missing[0]["confirmation_complete"])
        self.assertEqual(missing[0]["quality_class"], "uncertain")
        batch["panels"] = [dict(configs=[dict(s=8, opt="O2")], block=1, seed=700001,
                               reference_config=dict(s=8, opt="O2"))]
        samples = [dict(stage="comparison", role="shared_confirmation", block=1, s=8, opt="O2",
                        round=round_id, valid=True, kernel_s=1) for round_id in (1, 1, 3)]
        duplicate = su.panel_table(samples, [batch])
        self.assertFalse(duplicate[0]["complete"])
        returned, _ = su.search_tables([batch], grid, duplicate, protocol())
        self.assertFalse(returned[0]["confirmation_complete"])
        seeds = protocol()["holdout"]["seeds"]
        holdout = [dict(returned[0], stage="confirmation", seed=seed) for seed in seeds]
        self.assertFalse(su.baseline_confirmation(holdout, seeds)["complete"])

    def test_same_identity_scores_zero_despite_independent_time_differences(self):
        a, b, anchor = su.describe([30, 31, 32]), su.describe([36, 37, 38]), su.describe([30, 31, 32])
        self.assertEqual(su.gain_bounds(a, b, anchor, same_config=True), (0, 0))
        self.assertEqual(su.gap_bounds(a, anchor, same_config=True), (0, 0))
        self.assertGreater(100 * (b["median_s"] / a["median_s"] - 1), 5)

    def test_anchor_endpoint_corners_preserve_signed_ranges(self):
        bounds = su.gain_bounds(su.describe([9, 10, 11]), su.describe([10, 11, 12]), su.describe([8, 10, 12]))
        self.assertEqual(bounds, (-37.5, 12.5))
        self.assertEqual(su.gain_bounds({}, {}, {}), (None, None))

    def test_rho_padding_prevents_false_five_percent_classification(self):
        self.assertEqual(su.classify(4.8, (4, 5), (4, 5), resolution_pp=1), "uncertain")
        self.assertEqual(su.classify(0, (0, 0), (0, 0), resolution_pp=20, same_config=True), "near_optimal_observed")
        self.assertEqual(su.classify(20, (19, 21), (19, 21), resolution_pp=2), "clearly_worse_observed")

    def test_disjoint_reference_panel_blocks_keep(self):
        self.assertTrue(su.ranges_conflict((2, 3), (-2, -1), 1))
        self.assertFalse(su.ranges_conflict((2, 3), (0, 1), 1))
        pairs = [paired() for _ in range(6)]
        pairs[0]["reference_panel_conflict"] = True
        self.assertEqual(su.decision(pairs, protocol(), 6)["decision"], "INCONCLUSIVE")

    def test_same_config_efficiency_boundary_and_cost_regression(self):
        self.assertEqual(su.decision([paired() for _ in range(6)], protocol(rho=15), 6)["decision"], "KEEP")
        self.assertEqual(su.decision([paired(saving=-.11) for _ in range(6)], protocol(), 6)["decision"], "REJECT")

    def test_clear_quality_regression_and_unsupported_risk(self):
        self.assertEqual(su.decision([paired(-5, .3, False) for _ in range(6)], protocol(), 6)["decision"], "REJECT")
        self.assertEqual(su.decision([paired(-1.5, .3, False) for _ in range(6)], protocol(), 6)["decision"], "INCONCLUSIVE")
        self.assertEqual(su.decision([paired(-1, .3, False) for _ in range(6)], protocol(), 6)["decision"], "KEEP")

    def test_quality_route_requires_useful_supported_lower_bound(self):
        pairs = [paired(6, 0, False) for _ in range(6)]
        self.assertEqual(su.decision(pairs, protocol(), 6)["decision"], "KEEP")
        for row in pairs:
            row.update(gain_ref_low_pp=-1, gain_panel_low_pp=-1)
        self.assertEqual(su.decision(pairs, protocol(), 6)["decision"], "REJECT")

    def test_missing_holdout_unknown_cost_or_missing_calls_never_retains_candidate(self):
        keep = su.decision([paired() for _ in range(6)], protocol(), 6)
        confirm = su.decision([], protocol(), 3)
        self.assertFalse(su.final_retention(keep, confirm)["retained"])
        pairs = [paired() for _ in range(6)]
        pairs[0]["wall_saving_fraction"] = None
        self.assertEqual(su.decision(pairs, protocol(), 6)["decision"], "INCONCLUSIVE")
        pairs[0].update(wall_saving_fraction=.5, candidate_calls=7)
        self.assertEqual(su.decision(pairs, protocol(), 6)["decision"], "INCONCLUSIVE")
        self.assertEqual(su.decision([paired() for _ in range(6)], protocol(), 6,
                                    project_cost_complete=False)["decision"], "INCONCLUSIVE")

    def test_unfrozen_rules_or_missing_diagnostic_resolution_cannot_keep(self):
        proto = protocol()
        proto["acceptance"]["state"] = "pending"
        self.assertEqual(su.decision([paired() for _ in range(6)], proto, 6)["decision"], "INCONCLUSIVE")
        proto = protocol()
        proto["measurement"]["clock_health"]["resolution_pp"] = None
        self.assertEqual(su.decision([paired() for _ in range(6)], proto, 6)["decision"], "INCONCLUSIVE")


    def test_known_cost_same_identity_cannot_keep_with_clock_conflict(self):
        result = su.decision([paired(saving=.2)] * 6, protocol(), 6,
                             project_cost_complete=True, project_clock_healthy=False)
        self.assertEqual(result["decision"], "INCONCLUSIVE")
        self.assertIn("clock", result["reasons"][0])


class Goal2DiagnosticAndCostTests(unittest.TestCase):
    def test_ledger_snapshot_hash_and_rows_describe_the_same_read(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            first = b'{"type":"task_start","attempt_id":"fixture"}\n'
            path.write_bytes(first)
            data, rows, digest = su.record_snapshot(path)
            path.write_bytes(first + b'{"type":"task_end","attempt_id":"fixture"}\n')
            self.assertEqual(data, first)
            self.assertEqual(rows, [dict(type="task_start", attempt_id="fixture")])
            self.assertEqual(digest, su.hashlib.sha256(first).hexdigest())
            self.assertNotEqual(digest, su.sha256(path))

    def test_complete_clock_check_uses_first_and_previous_same_source(self):
        healthy = su.complete_clock_check("formal_target_process", dict(monotonic=40, raw=40.4, realtime=40), [1.0, 1.01])
        self.assertFalse(healthy["conflict"])
        conflict = su.complete_clock_check("formal_target_process", dict(monotonic=40, raw=41.2, realtime=40), [1.0, 1.015])
        self.assertTrue(conflict["conflict"])
        self.assertEqual(conflict["baseline_ratios"], [1.0, 1.015])
        with self.assertRaises(ValueError):
            su.clock_spans(dict(monotonic=0, raw=0, realtime=0), dict(monotonic=1, raw=-1, realtime=1))

    def test_prefix_conflict_does_not_become_a_complete_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.clocks.jsonl"
            start = dict(task="fixture", clock_start_ns=dict(monotonic=0, raw=0, realtime=0))
            finish = dict(monotonic=40_000_000_000, raw=40_000_000_000, realtime=40_000_000_000)
            checks = [su.complete_clock_check(source, dict(monotonic=40, raw=40, realtime=40), [1.0])
                      for source in ("driver", "formal_target_process")]
            expected = dict(task="fixture", clock_complete_checks=checks, prefix_clock_conflict=True,
                complete_clock_conflict=False, clock_conflict=False, complete_clock_observation=True)
            query = dict(readonly=True, offset_raw=0, frequency_scaled_ppm=0, tick_us=10000,
                         status=0, precision_us=1, returncode=0, offset_unit="us")
            previous, trace = start["clock_start_ns"], []
            for phase, ns in (("start", previous), ("interval", dict(monotonic=12_000_000_000,
                    raw=11_700_000_000, realtime=12_000_000_000)), ("end", finish)):
                prefix = su.clock_spans(start["clock_start_ns"], ns)
                local = su.clock_spans(previous, ns)
                ratio = prefix["raw"] / prefix["monotonic"] if prefix["monotonic"] else None
                trace.append(dict(type="clock_sample", phase=phase, task="fixture", clock_ns=ns, unit="ns",
                    read_order=["monotonic", "raw", "realtime"], prefix_elapsed_s=prefix, local_elapsed_s=local,
                    prefix_ratio=ratio, local_ratio=local["raw"] / local["monotonic"] if local["monotonic"] else None,
                    prefix_clock_conflict=prefix["monotonic"] >= 10 and abs(ratio - 1) > .02, adjtimex=query))
                previous = ns
            trace.append(dict(type="clock_complete", **expected))
            path.write_text("".join(json.dumps(row) + "\n" for row in trace))
            end = dict(clock_end_ns=finish, clock_trace_sha256=su.sha256(path), **expected)
            rows = su.followup_timeline(path, start, end, checks, [1.0])
            self.assertEqual(sum(row["prefix_clock_conflict"] for row in rows), 1)
            bad = copy.deepcopy(trace)
            bad[-1]["complete_clock_conflict"] = True
            path.write_text("".join(json.dumps(row) + "\n" for row in bad))
            end.update(clock_trace_sha256=su.sha256(path), complete_clock_conflict=True)
            with self.assertRaises(ValueError):
                su.followup_timeline(path, start, end, checks, [1.0])

    def test_new_two_pair_aa_preserves_large_label_differences(self):
        rows = [dict(role="clock_followup_aa", tier=tier, label=label, pair=pair, s=128 if tier == "F" else 8,
            opt="O2", valid=True, kernel_s=(40 if tier == "F" else 60) * (1.25 if label == "B" else 1))
            for tier in ("F", "M") for label in ("A", "B") for pair in (1, 2)]
        summary = su.followup_aa_table(rows)
        self.assertTrue(all(row["complete"] for row in summary))
        self.assertTrue(all(abs(row["signed_median_difference_pct"] - 25) < 1e-12 for row in summary))
        with self.assertRaises(ValueError):
            su.followup_aa_table(rows + [rows[0]])

    def test_clock_diagnostics_recompute_nanoseconds_units_and_float_output(self):
        proto = protocol()
        proto["target"].update(sha256="fixture-clock-source", compiler_identity={"path": "fixture-clock-compiler"})
        clock = dict(clock_order=["MONOTONIC", "RAW", "REALTIME", "PROCESS_CPU"],
            start_ns=[10000000000] * 4, end_ns=[11234567890, 11240000000, 11234567890, 11230000000],
            elapsed_s=[1.23456789, 1.24, 1.23456789, 1.23])
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            (raw / "identity.json").write_text(json.dumps(dict(source_sha256="fixture-clock-source",
                compiler=proto["target"]["compiler_identity"])))
            path = raw / "matrix-multiclock-fast.stdout.txt"
            path.write_text("1.234568\nchecksum=1\n" + json.dumps(clock) + "\n")
            summary = su.clock_table(raw, proto)
            self.assertEqual(summary["intervals"][0]["monotonic_s"], 1.23456789)
            self.assertFalse(summary["intervals"][0]["absolute_clock_accuracy_verified"])
            clock["elapsed_s"][1] = 1.25
            path.write_text("1.234568\nchecksum=1\n" + json.dumps(clock) + "\n")
            with self.assertRaises(ValueError):
                su.clock_table(raw, proto)

    def test_actual_aa_labels_remain_distinct_and_m1_rule_is_recomputed(self):
        samples = aa_fixture()
        aa = su.aa_table(samples)
        self.assertAlmostEqual(aa[0]["signed_median_difference_pct"], 10)
        selected = su.choose_arrangement(aa, samples)
        self.assertEqual(selected["arrangement"], "M1")
        self.assertEqual(selected["resolution_pp"], 1)
        self.assertTrue(selected["performance_gate"])
        self.assertFalse(selected["population_false_positive_rate_estimated"])

    def test_duplicate_or_missing_aa_sample_is_not_hidden_by_identity_dedup(self):
        samples = aa_fixture()
        with self.assertRaises(ValueError):
            su.aa_table(samples + [samples[0]])
        samples[0]["valid"] = False
        with self.assertRaises(ValueError):
            su.aa_table(samples)

    def test_partial_aa_preserves_available_labels_without_selecting_arrangement(self):
        samples = aa_fixture()
        samples[0]["valid"] = False
        samples.pop(1)
        aa = su.aa_table(samples, require_complete=False)
        self.assertFalse(aa[0]["complete"])
        self.assertEqual(aa[0]["observed_runs"], 5)
        self.assertEqual(aa[0]["failed_runs"], 1)
        self.assertIsNone(su.choose_arrangement(aa, samples)["arrangement"])
        self.assertFalse(su.choose_arrangement(aa, samples)["performance_gate"])

    def test_zero_m0_branch_does_not_claim_observed_aa_reduction(self):
        samples = aa_fixture()
        for row in samples:
            if row["method"] == "M0":
                row["kernel_s"] = 40 if row["tier"] == "F" else 60
        choice = su.choose_arrangement(su.aa_table(samples), samples)
        self.assertEqual(choice["rationale"], "shorter_confirmation_distance")

    def test_method_rank_reversal_prevents_diagnostic_performance_gate(self):
        samples = aa_fixture()
        for row in samples:
            if row["role"] == "aa" and row["tier"] == "F" and row["block"] in (3, 4):
                row["kernel_s"] = 80
        choice = su.choose_arrangement(su.aa_table(samples), samples)
        self.assertFalse(choice["performance_gate"])

    def test_shared_panel_cost_counted_once_and_unknown_attempt_is_not_zero(self):
        rows = []
        for index, (role, count) in enumerate((("search", 8), ("search", 8), ("shared_confirmation", 3))):
            rows.append(dict(type="task_end", attempt_id=str(index), task=str(index), role=role,
                n4096_calls=count, driver_wall_s=100, resource_wall_s=101,
                clock_end_ns=dict(monotonic=100000000000, raw=101000000000, realtime=100000000000),
                returncode=0, reason=None, clock_elapsed_s=dict(monotonic=100, raw=101, realtime=100)))
        batch = dict(manifest=dict(stage="comparison"), tasks=[], driver=rows)
        cost = su.cost_table([batch])
        self.assertEqual(sum(row["process_runs"] for row in cost["rows"]), 19)
        self.assertEqual(next(row for row in cost["rows"] if row["role"] == "shared_confirmation")["tasks"], 1)
        ledger = [dict(type="task_start", attempt_id=row["attempt_id"], task=row["task"], call_upper=row["n4096_calls"],
                       clock_start_ns=dict(monotonic=0, raw=0, realtime=0)) for row in rows] + rows
        ledger += [dict(type="task_start", attempt_id="unknown", task="interrupted-probe")]
        cost = su.cost_table([batch], ledger)
        self.assertFalse(cost["complete"])
        self.assertEqual(cost["unfinished_attempts"], ["unknown"])
        with self.assertRaises(ValueError):
            su.cost_table([batch, batch])

    def test_internal_rechecks_are_charged_not_external_confirmation(self):
        samples = [dict(stage="comparison", role="search", phase="explore" if i < 6 else "recheck",
            spawned=True, valid=True, kernel_s=10, process_wall_s=11) for i in range(8)]
        costs, builds = su.component_costs([], samples)
        rechecks = next(row for row in costs if row["component"] == "internal_recheck")
        self.assertEqual((rechecks["process_runs"], rechecks["kernel_recorded_s"]), (2, 20))
        self.assertEqual(sum(row["process_runs"] for row in costs), 8)

    def test_recovered_clock_and_call_upper_bound_is_never_actual_complete_cost(self):
        start = dict(type="task_start", attempt_id="recovered", task="interrupted-matrix")
        end = dict(type="task_end", attempt_id="recovered", task="interrupted-matrix", role="diagnostic",
            n4096_calls=1, n4096_calls_known=False, n4096_call_recorded_lower=0,
            driver_wall_s=None, clock_elapsed_s=None, resource_wall_s=40,
            resource_bound_basis="same-boot upper span including downtime", returncode=None,
            reason="hard-exit recovery")
        costs = su.cost_table([], [start, end])
        self.assertFalse(costs["complete"])
        self.assertEqual(costs["rows"][0]["unknown_attempts"], ["recovered"])
        self.assertFalse(costs["rows"][0]["process_runs_known"])
        self.assertIsNone(costs["rows"][0]["domains_s"]["monotonic"])
        self.assertIsNone(costs["rows"][0]["full_driver_wall_s"])
        self.assertEqual(costs["rows"][0]["recorded_process_lower"], 0)

    def test_batch_copy_cannot_disagree_with_global_actual_attempt(self):
        row = dict(type="task_end", attempt_id="1", task="panel", role="shared_confirmation",
            n4096_calls=3, driver_wall_s=100, resource_wall_s=101, returncode=0, reason=None,
            clock_elapsed_s=dict(monotonic=100, raw=101, realtime=100))
        batch = dict(manifest=dict(stage="comparison"), tasks=[], driver=[row])
        ledger = [dict(type="task_start", attempt_id="1", task="panel"), dict(row, n4096_calls=2)]
        with self.assertRaises(ValueError):
            su.cost_table([batch], ledger)

    def test_two_copies_of_forged_cost_cannot_override_original_clock_boundaries(self):
        start = dict(type="task_start", attempt_id="1", task="panel", call_upper=3,
                     clock_start_ns=dict(monotonic=0, raw=0, realtime=0))
        row = dict(type="task_end", attempt_id="1", task="panel", role="shared_confirmation",
            n4096_calls=3, driver_wall_s=100, resource_wall_s=101, returncode=0, reason=None,
            clock_end_ns=dict(monotonic=90000000000, raw=91000000000, realtime=90000000000),
            clock_elapsed_s=dict(monotonic=100, raw=101, realtime=100))
        batch = dict(manifest=dict(stage="comparison"), tasks=[], driver=[row])
        with self.assertRaises(ValueError):
            su.cost_table([batch], [start, row])

    def test_same_attempt_copy_timestamps_are_not_new_cost_or_identity(self):
        start = dict(type="task_start", attempt_id="1", task="panel", call_upper=3,
                     clock_start_ns=dict(monotonic=0, raw=0, realtime=0))
        row = dict(type="task_end", attempt_id="1", task="panel", role="shared_confirmation", at="ledger-time",
            n4096_calls=3, driver_wall_s=100, resource_wall_s=101, returncode=0, reason=None,
            clock_end_ns=dict(monotonic=100000000000, raw=101000000000, realtime=100000000000),
            clock_elapsed_s=dict(monotonic=100, raw=101, realtime=100))
        batch = dict(manifest=dict(stage="comparison"), tasks=[], driver=[dict(row, at="copy-time")])
        self.assertTrue(su.cost_table([batch], [start, row])["complete"])

    def test_matching_cost_copies_cannot_hide_a_raw_target_call(self):
        start = dict(type="task_start", attempt_id="1", task="search", call_upper=8,
                     clock_start_ns=dict(monotonic=0, raw=0, realtime=0))
        row = dict(type="task_end", attempt_id="1", task="search", role="search",
            n4096_calls=7, driver_wall_s=100, resource_wall_s=101, returncode=0, reason=None,
            clock_end_ns=dict(monotonic=100000000000, raw=101000000000, realtime=100000000000),
            clock_elapsed_s=dict(monotonic=100, raw=101, realtime=100))
        task = dict(job=dict(id="search", role="search"), records=[dict(type="measurement_start") for _ in range(8)])
        batch = dict(manifest=dict(stage="comparison"), tasks=[task], driver=[row])
        with self.assertRaises(ValueError):
            su.cost_table([batch], [start, row])

    def test_missing_whole_cost_attempt_is_not_a_complete_project_bill(self):
        task = dict(job=dict(id="missing-search", role="search"), records=[dict(type="measurement_start") for _ in range(8)])
        batch = dict(manifest=dict(stage="comparison"), tasks=[task], driver=[])
        start = dict(type="task_start", attempt_id="probe", task="probe", call_upper=0,
                     clock_start_ns=dict(monotonic=0, raw=0, realtime=0))
        end = dict(type="task_end", attempt_id="probe", task="probe", role="clock_probe", n4096_calls=0,
            driver_wall_s=40, resource_wall_s=40, returncode=0, reason=None,
            clock_end_ns=dict(monotonic=40000000000, raw=40000000000, realtime=40000000000),
            clock_elapsed_s=dict(monotonic=40, raw=40, realtime=40))
        costs = su.cost_table([batch], [start, end])
        self.assertFalse(costs["complete"])
        self.assertEqual(costs["missing_jobs"][0]["recorded_process_starts"], 8)
        self.assertIsNone(costs["totals"]["actual_process_runs"])
        self.assertIsNone(costs["totals"]["charged_process_upper"])
        self.assertEqual(costs["totals"]["recorded_ledger_charged_calls"], 0)
        self.assertEqual(costs["totals"]["missing_job_raw_starts"], 8)

    def test_guarded_task_uses_exact_global_journal_end_without_raw_copy(self):
        task = dict(job=dict(id="interrupted", role="aa"), records=[dict(type="measurement_start")])
        batch = dict(path=su.ex.P1 / "results/diagnostic-fixture", manifest=dict(stage="diagnostic"),
                     tasks=[task], driver=[])
        start = dict(type="task_start", attempt_id="guarded", task="interrupted", call_upper=1,
            journal="results/diagnostic-fixture/interrupted.jsonl",
            clock_start_ns=dict(monotonic=0, raw=0, realtime=0))
        end = dict(type="task_end", attempt_id="guarded", task="interrupted", role="aa", n4096_calls=1,
            n4096_calls_known=True, driver_wall_s=10, resource_wall_s=10, returncode=130, reason="clock_guard",
            clock_end_ns=dict(monotonic=10000000000, raw=9900000000, realtime=10000000000),
            clock_elapsed_s=dict(monotonic=10, raw=9.9, realtime=10))
        costs = su.cost_table([batch], [start, end])
        self.assertTrue(costs["complete"])
        self.assertEqual(costs["totals"]["actual_process_runs"], 1)
        self.assertEqual(costs["rows"][0]["stage"], "diagnostic")
        self.assertEqual(costs["rows"][0]["failed_tasks"], 1)
        self.assertFalse(su.cost_table([batch], [dict(start, journal="results/other/interrupted.jsonl"), end])["complete"])
        with self.assertRaises(ValueError):
            su.cost_table([batch], [start, dict(end, n4096_calls=0)])

    def test_partial_cost_copies_use_all_exact_journal_attempts_once(self):
        task = dict(job=dict(id="search", role="search"), records=[dict(type="measurement_start") for _ in range(8)])
        starts, ends = [], []
        for index, calls in enumerate([3, 5]):
            starts.append(dict(type="task_start", attempt_id=str(index), task="search", call_upper=calls,
                journal="results/comparison-fixture/search.jsonl", clock_start_ns=dict(monotonic=0, raw=0, realtime=0)))
            ends.append(dict(type="task_end", attempt_id=str(index), task="search", role="search", n4096_calls=calls,
                driver_wall_s=10, resource_wall_s=10, returncode=0, reason=None,
                clock_end_ns=dict(monotonic=10000000000, raw=10000000000, realtime=10000000000),
                clock_elapsed_s=dict(monotonic=10, raw=10, realtime=10)))
        batch = dict(path=su.ex.P1 / "results/comparison-fixture", manifest=dict(stage="comparison"), tasks=[task], driver=[ends[1]])
        costs = su.cost_table([batch], [starts[0], ends[0], starts[1], ends[1]])
        self.assertTrue(costs["complete"])
        self.assertEqual(costs["totals"]["actual_process_runs"], 8)
        self.assertEqual(costs["rows"][0]["tasks"], 2)

    def test_two_different_batches_cannot_replace_same_seed_identity(self):
        grid = [dict(s=8, opt="O2", **su.describe([30, 30, 30]))]
        rows = [dict(stage="comparison", algorithm="random", seed=700001) for _ in range(2)]
        with self.assertRaises(ValueError):
            su.paired_rows(rows, grid, [], protocol(), "comparison")

    def test_two_batch_panels_with_same_identity_are_not_new_evidence(self):
        config = dict(s=8, opt="O2")
        panel = dict(block=1, seed=700001, configs=[config], reference_config=config)
        batches = [dict(manifest=dict(stage="comparison"), panels=[panel], path=Path(name)) for name in ("first", "second")]
        samples = [dict(stage="comparison", role="shared_confirmation", block=1, round=r,
                        valid=True, kernel_s=30, **config) for r in (1, 2, 3)]
        with self.assertRaises(ValueError):
            su.panel_table(samples, batches)

    def test_derived_path_cannot_overwrite_or_nest_under_raw(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw"
            for path in (raw, raw / "derived"):
                with self.assertRaises(ValueError):
                    su.safe_destination(path, [dict(path=raw)])
            with self.assertRaises(ValueError):
                su.write_csv(Path(directory) / "derived.csv", [dict(value=math.nan)])
            other = Path(directory) / "old-unlisted-raw"
            other.mkdir()
            (other / "plan.json").write_text('{"fixture":true}')
            with self.assertRaises(ValueError):
                su.safe_destination(other / "derived", [])


if __name__ == "__main__":
    unittest.main()
