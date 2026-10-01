"""Temporary, synthetic journals; no compiler or n=4096 kernel is executed."""

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import tempfile
import time
import unittest
from unittest import mock

REAL_P1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REAL_P1 / "scripts"))
sys.path.insert(0, str(REAL_P1 / "src"))
import autotuner as at
import experiment as ex
import summarize as su


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "P1"
        (self.root / "src").mkdir(parents=True)
        (self.root / "evidence").mkdir()
        shutil.copyfile(REAL_P1 / "src/autotuner.py", self.root / "src/autotuner.py")
        (self.root / "src/matrix_multiplication.c").write_text("/* fixture, never compiled */\n#define n 4096\n")
        (self.root / "evidence/approval.json").write_text('{"fixture":true}\n')
        self.protocol = ex.load_json(REAL_P1 / "evidence/protocol_v1.json")
        self.protocol["state"] = "approved"
        self.protocol["approval"]["evidence"] = "evidence/approval.json"
        self.protocol["target"]["sha256"] = ex.sha256(self.root / self.protocol["target"]["path"])
        self.protocol["framework"]["sha256"] = ex.sha256(self.root / self.protocol["framework"]["path"])
        compiler = str(Path(sys.executable).resolve())
        self.protocol["target"]["compiler"] = compiler
        self.protocol["target"]["compiler_identity"] = dict(path=compiler, version="synthetic fixture", sha256=ex.sha256(compiler))
        self.protocol["measurement"]["cpu_affinity"] = sorted(os.sched_getaffinity(0))
        self.protocol["measurement"]["clock_health"].update(status="resolved", timer="CLOCK_MONOTONIC")
        self.protocol["pretest_basis"]["completed"] = True
        self.protocol["strategy_options"]["patience"]["min_relative_improvement"] = .05
        self.protocol["reference"]["noise_relative_range"] = .05
        self.protocol["reference"]["conflict"]["relative_difference"] = .05
        self.protocol["acceptance"].update(epsilon_pct=5, quality_gain_pp=2, quality_gain_s=2, quality_loss_pp=2,
                                           wall_increase_fraction=.1, wall_saving_s=1)
        self.protocol_path = self.root / "evidence/protocol.json"
        self.save_protocol()
        self.patches = [mock.patch.object(ex, "P1", self.root), mock.patch.object(su, "P1", self.root)]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        self.temp.cleanup()

    def save_protocol(self):
        self.protocol_path.write_text(json.dumps(self.protocol, allow_nan=False) + "\n")

    def make_plan(self, stage="selection", algorithms=None):
        directory = self.root / ("results/" + stage + "_v1")
        directory.mkdir(parents=True, exist_ok=True)
        manifest = ex.plan(self.protocol_path, stage, algorithms)
        (directory / "plan.json").write_text(json.dumps(manifest) + "\n")
        return directory, manifest

    def write_job(self, job, directory):
        protocol = self.protocol
        root = self.root

        class FakeTarget:
            def __init__(self, source, compiler, flags, cache_dir, compile_timeout):
                self.cache_dir = Path(cache_dir)
                self.compiler_info = dict(probe={"fixture": True})

            def metadata(self):
                return dict(source=str(root / protocol["target"]["path"]),
                    source_sha256=protocol["target"]["sha256"], n=4096,
                    compiler=protocol["target"]["compiler_identity"], flags=list(at.COMMON_FLAGS),
                    compile_timeout=float(protocol["measurement"]["compile_timeout_s"]),
                    require_checksum=True, kernel_clock="CLOCK_MONOTONIC")

            def build(self, opt, emit):
                result = dict(status="ok", cached=True, compile_wall_s=0, opt=opt)
                emit("build", result)
                return result

            def measure(self, build, config, timeout, on_start):
                value = float(f"{1 + config.s / 1000 + int(config.opt[1]) / 100:.6f}")
                command = ["SYNTHETIC_NOT_EXECUTED", str(config.s), config.opt]
                on_start(dict(command=command, started_at=at.now(), pid=2 ** 30, spawned=True))
                return dict(status="ok", kernel_s=value, checksum=1.0, process_wall_s=value + 1,
                    spawned=True, stdout=f"{value:.6f}\nchecksum=1\n", stderr="", returncode=0,
                    command=command, started_at=at.now(), ended_at=at.now())

        command = ex.command(job, directory, protocol, self.protocol_path)
        with mock.patch.object(at, "TargetProgram", FakeTarget), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(at.main(command[5:]), 0)
        return directory / (job["id"] + ".jsonl")

    @staticmethod
    def rewrite(path, rows):
        path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows))

    def search_job(self, manifest):
        return next(job for job in manifest["jobs"] if job.get("algorithm") == "random")

    def test_plan_counts_seed_rotation_and_single_baseline(self):
        _, selection = self.make_plan()
        _, reference = self.make_plan("reference")
        _, holdout = self.make_plan("holdout", ["random", "stratified", "patience"])
        count = lambda plan: sum(job["repeats"] * job.get("budget", 1) for job in plan["jobs"])
        self.assertEqual((count(reference), count(selection), count(holdout)), (61, 166, 100))
        self.assertEqual(sum(count(plan) for plan in (reference, selection, holdout)), 327)
        self.assertEqual(sum(job.get("algorithm") == "random" for job in selection["jobs"]), 3)
        _, two = self.make_plan("holdout", ["random", "stratified"])
        self.assertEqual([job["algorithm"] for job in two["jobs"] if job["action"] == "search"],
                         ["random", "stratified", "stratified", "random", "random", "stratified"])
        with self.assertRaises(ValueError):
            ex.plan(self.protocol_path, "selection", ["random", "stratified"])

    def test_actual_cli_metadata_and_completed_setting_tampering(self):
        directory, manifest = self.make_plan()
        job = self.search_job(manifest)
        path = self.write_job(job, directory)
        original = ex.read_records(path)
        self.assertEqual(ex.task_status(job, directory, manifest), "complete")
        changes = [("runtime_affinity", [999]), ("min_trials", 6), ("patience", 4),
                   ("min_relative_improvement", .07), ("timeout", 1201), ("repeats", 2),
                   ("blocks", [8]), ("opts", ["O0"]), ("budget", 7), ("seed", 7)]
        for key, value in changes:
            with self.subTest(key=key):
                rows = copy.deepcopy(original)
                rows[0]["metadata"][key] = value
                rows[0]["fingerprint"] = at.fingerprint(rows[0]["metadata"])
                self.rewrite(path, rows)
                with self.assertRaises(ValueError):
                    ex.task_status(job, directory, manifest)
        for key, value in (("flags", ["-Ofast"]), ("compile_timeout", 61), ("kernel_clock", "CLOCK_MONOTONIC_RAW"),
                           ("compiler", {"path": "other", "version": "other", "sha256": "other"})):
            with self.subTest(target_key=key):
                rows = copy.deepcopy(original)
                rows[0]["metadata"]["target"][key] = value
                rows[0]["fingerprint"] = at.fingerprint(rows[0]["metadata"])
                self.rewrite(path, rows)
                with self.assertRaises(ValueError):
                    ex.task_status(job, directory, manifest)

    def test_warmup_kept_in_raw_and_excluded_from_three_reference_samples(self):
        directory, manifest = self.make_plan("reference")
        for job in manifest["jobs"]:
            if job["role"] == "warmup" or (job["s"] == 128 and job["opt"] == "O3"):
                self.write_job(job, directory)
        batch = su.read_batch(directory, ex.sha256(self.protocol_path))
        samples = su.sample_rows(batch, .005)
        grid = su.grid_table(samples, self.protocol)
        cell = next(row for row in grid if row["s"] == 128 and row["opt"] == "O3")
        self.assertEqual(len(samples), 4)
        self.assertEqual(cell["valid_runs"], 3)
        self.assertEqual(sorted(json.loads(cell["rounds"])), [1, 2, 3])

    def test_clone_historical_analysis_and_strict_resume(self):
        directory, manifest = self.make_plan()
        job = self.search_job(manifest)
        path = self.write_job(job, directory)
        clone = Path(self.temp.name) / "clone/P1"
        shutil.copytree(self.root, clone)
        cloned_directory = clone / directory.relative_to(self.root)
        with mock.patch.object(ex, "P1", clone), mock.patch.object(su, "P1", clone):
            self.assertEqual(ex.task_status(job, cloned_directory, manifest, historical_only=True), "complete")
            with self.assertRaises(ValueError):
                ex.task_status(job, cloned_directory, manifest)
            with self.assertRaises(ValueError):
                ex.check_frozen(self.protocol, clone / self.protocol_path.relative_to(self.root), manifest)
            rows = ex.read_records(clone / path.relative_to(self.root))
            rows[0]["metadata"]["runtime_affinity"] = [999]
            rows[0]["fingerprint"] = at.fingerprint(rows[0]["metadata"])
            self.rewrite(clone / path.relative_to(self.root), rows)
            with self.assertRaises(ValueError):
                ex.task_status(job, cloned_directory, manifest, historical_only=True)

    def test_partial_resume_reserves_remaining_processes(self):
        self.protocol["resources"]["max_process_runs"] = 8
        self.save_protocol()
        directory, manifest = self.make_plan()
        job = self.search_job(manifest)
        manifest["jobs"] = [job]
        (directory / "plan.json").write_text(json.dumps(manifest))
        path = self.write_job(job, directory)
        full = ex.read_records(path)
        second_trial = next(i for i, row in enumerate(full) if row["type"] == "trial" and row["trial_id"] == 1)
        self.rewrite(path, full[:second_trial + 1])
        with (directory / "driver.jsonl").open("a") as stream:
            ex.append_event(stream, "task_start", task=job["id"], attempt_id=0)
            ex.append_event(stream, "task_end", task=job["id"], attempt_id=0, driver_wall_s=1)
        self.assertEqual(ex.recorded_usage(self.protocol, manifest["protocol_sha256"])[0], 2)

        class FakeChild:
            pid = 2 ** 30

            def wait(child, timeout=None):
                self.rewrite(path, full)
                return 0

        with mock.patch.object(ex.subprocess, "Popen", return_value=FakeChild()), contextlib.redirect_stdout(io.StringIO()):
            ex.execute(directory, manifest, 1)
        self.assertEqual(ex.task_status(job, directory, manifest), "complete")
        self.assertEqual(ex.recorded_usage(self.protocol, manifest["protocol_sha256"])[0], 8)

    def test_hard_recovery_torn_tail_unknown_cost_and_no_zero(self):
        directory, manifest = self.make_plan()
        job = manifest["jobs"][0]
        path = self.write_job(job, directory)
        self.rewrite(path, [row for row in ex.read_records(path) if row["type"] != "summary"])
        ledger = directory / "driver.jsonl"
        with ledger.open("a") as stream:
            ex.append_event(stream, "task_start", task=job["id"], attempt_id=0,
                monotonic_s=time.monotonic() - 10, boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(), existing_records=0)
            ex.append_event(stream, "task_process", task=job["id"], attempt_id=0, pid=2 ** 30)
        with ledger.open("ab") as stream:
            stream.write(b'{"type":"task_end"')
        before = ledger.read_bytes()
        with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
            ex.execute(directory, manifest, 1)
        self.assertEqual(ledger.read_bytes(), before)
        inspection = self.root / "evidence/inspection.txt"
        inspection.write_text("Synthetic fixture: no test subprocess was spawned.\n")
        evidence = self.root / "evidence/recovery.json"
        evidence.write_text(json.dumps(dict(protocol_sha256=manifest["protocol_sha256"], task=job["id"], attempt_id=0,
            verified_no_live_processes=True, inspection="evidence/inspection.txt")))
        with contextlib.redirect_stdout(io.StringIO()):
            ex.recover(directory, manifest, evidence)
        events = ex.read_records(ledger)
        recovered = events[-1]
        self.assertEqual(events[-2]["discarded_fragment_hex"], b'{"type":"task_end"'.hex())
        self.assertIsNone(recovered["driver_wall_s"])
        self.assertGreater(recovered["resource_wall_upper_s"], recovered["driver_wall_recorded_lower_bound_s"])
        self.assertEqual(recovered["unrecorded_process_run_upper"], 1)
        self.assertEqual(ex.recorded_usage(self.protocol, manifest["protocol_sha256"])[0], 2)

    def test_raw_stdout_repeat_counts_and_clock_rejection(self):
        directory, manifest = self.make_plan()
        job = self.search_job(manifest)
        path = self.write_job(job, directory)
        rows = ex.read_records(path)
        task = dict(job=job, records=rows, summary=rows[-1])
        su.check_trials(task, .005)
        measurement = next(row for row in rows if row["type"] == "measurement")
        measurement["stdout"] = "999\nchecksum=1\n"
        with self.assertRaises(ValueError):
            su.check_trials(task, .005)
        measurement["stdout"] = f"{measurement['kernel_s']:.6f}\nchecksum=1\n"
        measurement["kernel_s"] = measurement["process_wall_s"] + .0051
        self.rewrite(path, rows)
        self.assertEqual(ex.task_status(job, directory, manifest), "clock_error")

    def test_conflict_cap_interleaving_and_original_reference_unchanged(self):
        request_path = self.root / "evidence/request.json"
        events = [dict(returned_config=dict(s=s, opt="O0"), reference_config=dict(s=128, opt="O3")) for s in (8, 16)]
        request_path.write_text(json.dumps(dict(protocol_sha256=ex.sha256(self.protocol_path), source_stage="selection", events=events)))
        manifest = ex.plan(self.protocol_path, "conflict_selection", conflict_request=request_path)
        self.assertEqual(len(manifest["jobs"]), 12)
        self.assertEqual([job["member"] for job in manifest["jobs"][:6]],
                         ["returned", "reference", "reference", "returned", "returned", "reference"])
        request = ex.load_json(request_path)
        request["events"].append(dict(returned_config=dict(s=24, opt="O0"), reference_config=dict(s=128, opt="O3")))
        request_path.write_text(json.dumps(request))
        with self.assertRaises(ValueError):
            ex.plan(self.protocol_path, "conflict_selection", conflict_request=request_path)
        decisions = [dict(stage="selection", algorithm="stratified", decision="KEEP", reasons=[])]
        su.apply_reference_checks(decisions, dict(complete=True, noisy_configs=[],
            conflicts=[dict(stage="selection", algorithm="random")]))
        self.assertEqual(decisions[0]["decision"], "INCONCLUSIVE")
        self.assertFalse(self.protocol["reference"]["conflict"]["replace_original_reference"])

    def test_complete_states_required_for_keep_and_raw_output_protected(self):
        rows = []
        for seed in self.protocol["online"]["seeds"]:
            for algorithm in ("random", "stratified", "patience"):
                rows.append(dict(stage="selection", algorithm=algorithm, seed=seed, state="complete",
                    confirmation_state="complete", gap_pct=10 if algorithm == "random" else 6,
                    confirmed_s=10 if algorithm == "random" else 6,
                    confirmed_min_s=10 if algorithm == "random" else 6,
                    confirmed_max_s=10 if algorithm == "random" else 6, reference_median_s=100,
                    total_wall_s=20 if algorithm == "random" else 18,
                    search_process_runs=8 if algorithm != "patience" else 6, near_optimal=False))
        self.assertTrue(all(row["decision"] == "KEEP" for row in su.compare(rows, self.protocol, "selection")))
        rows[1]["state"] = "partial"
        self.assertEqual(su.compare(rows, self.protocol, "selection")[0]["decision"], "INCONCLUSIVE")
        raw = self.root / "results/reference_v1"
        for destination in (raw, raw / "plot.png", raw / "derived"):
            with self.assertRaises(ValueError):
                su.protect_output(destination, [], self.protocol)

    def test_frozen_driver_and_compiler_identity(self):
        _, manifest = self.make_plan()
        ex.check_frozen(self.protocol, self.protocol_path, manifest)
        manifest["driver_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            ex.check_frozen(self.protocol, self.protocol_path, manifest)

    def test_popen_pid_log_failure_cleans_child_without_fake_completion(self):
        directory, manifest = self.make_plan()
        manifest["jobs"] = [manifest["jobs"][0]]
        (directory / "plan.json").write_text(json.dumps(manifest))
        child = mock.Mock(pid=2 ** 30)
        child.wait.return_value = 0
        original_append = ex.append_event

        def fail_pid_record(stream, kind, **fields):
            if kind == "task_process":
                raise OSError("synthetic log write failure")
            return original_append(stream, kind, **fields)

        with mock.patch.object(ex.subprocess, "Popen", return_value=child), \
                mock.patch.object(ex, "append_event", side_effect=fail_pid_record), \
                contextlib.redirect_stdout(io.StringIO()), self.assertRaises(OSError):
            ex.execute(directory, manifest, 1)
        child.send_signal.assert_called_once_with(signal.SIGTERM)
        child.wait.assert_called_once_with()
        self.assertEqual([r["type"] for r in ex.read_records(directory / "driver.jsonl")], ["task_start"])

    def test_complete_legal_driver_row_without_newline_preserved(self):
        directory, manifest = self.make_plan()
        job = manifest["jobs"][0]
        self.write_job(job, directory)
        manifest["jobs"] = [job]
        (directory / "plan.json").write_text(json.dumps(manifest))
        ledger = directory / "driver.jsonl"
        start = dict(type="task_start", task=job["id"], attempt_id=0)
        end = dict(type="task_end", task=job["id"], attempt_id=0, driver_wall_s=1)
        ledger.write_text(json.dumps(start) + "\n" + json.dumps(end))
        with contextlib.redirect_stdout(io.StringIO()):
            ex.execute(directory, manifest, 0)
        events = ex.read_records(ledger)
        self.assertEqual(events[:2], [start, end])
        self.assertEqual(events[2]["type"], "driver_newline_recovery")
        self.assertEqual(ex.recorded_usage(self.protocol, manifest["protocol_sha256"])[1], 1)

    def test_raw_checksum_duplicate_repeat_and_summary_count_rejected(self):
        directory, manifest = self.make_plan()
        job = self.search_job(manifest)
        path = self.write_job(job, directory)
        original = ex.read_records(path)
        for change in ("checksum", "repeat", "process_count"):
            with self.subTest(change=change):
                rows = copy.deepcopy(original)
                measurement = next(row for row in rows if row["type"] == "measurement")
                if change == "checksum":
                    measurement["stdout"] = f"{measurement['kernel_s']:.6f}\nchecksum=2\n"
                elif change == "repeat":
                    rows.insert(rows.index(measurement), copy.deepcopy(measurement))
                else:
                    rows[-1]["process_runs"] += 1
                with self.assertRaises(ValueError):
                    su.check_trials(dict(job=job, records=rows, summary=rows[-1]), .005)

    def test_exit_spawn_and_process_start_completion_rejected(self):
        directory, manifest = self.make_plan()
        job = self.search_job(manifest)
        path = self.write_job(job, directory)
        original = ex.read_records(path)
        for change in ("nonzero_exit", "not_spawned", "unmatched_start", "missing_start", "duplicate_start"):
            with self.subTest(change=change):
                rows = copy.deepcopy(original)
                measurement = next(row for row in rows if row["type"] == "measurement")
                start = next(row for row in rows if row["type"] == "measurement_start")
                if change == "nonzero_exit":
                    measurement["returncode"] = 7
                    self.assertFalse(su.valid_measurement(measurement, .005))
                elif change == "not_spawned":
                    measurement["spawned"] = False
                    rows[-1]["process_runs"] -= 1
                    self.assertFalse(su.valid_measurement(measurement, .005))
                elif change == "unmatched_start":
                    extra = copy.deepcopy(start)
                    extra["repeat"] = 999
                    rows.insert(-1, extra)
                elif change == "missing_start":
                    rows.remove(start)
                else:
                    rows.insert(rows.index(start), copy.deepcopy(start))
                with self.assertRaises(ValueError):
                    su.check_trials(dict(job=job, records=rows, summary=rows[-1]), .005)
        start_index = next(i for i, row in enumerate(original) if row["type"] == "measurement_start")
        partial = original[:start_index + 1]
        su.check_trials(dict(job=job, records=partial, summary=None), .005)
        with self.assertRaisesRegex(ValueError, "unfinished process"):
            su.check_trials(dict(job=job, records=partial, summary=original[-1]), .005)

    def sensitivity_rows(self, ranges):
        rows = []
        for seed, (lower, upper, median) in zip(self.protocol["online"]["seeds"], ranges):
            rows.append(dict(stage="selection", algorithm="random", seed=seed, state="complete",
                confirmation_state="complete", gap_pct=0, confirmed_s=100,
                confirmed_min_s=100, confirmed_max_s=100, reference_median_s=100,
                total_wall_s=1000, search_process_runs=8, near_optimal=True))
            for algorithm in ("stratified", "patience"):
                rows.append(dict(stage="selection", algorithm=algorithm, seed=seed, state="complete",
                    confirmation_state="complete", gap_pct=-median, confirmed_s=100-median,
                    confirmed_min_s=100-upper, confirmed_max_s=100-lower, reference_median_s=100,
                    total_wall_s=1000 if algorithm == "stratified" else 900,
                    search_process_runs=8 if algorithm == "stratified" else 6, near_optimal=-median <= 5))
        return rows

    def test_robust_gain_count_and_risk_endpoints(self):
        self.protocol["acceptance"].update(quality_gain_pp=12, quality_gain_s=5.6)
        cases = [
            ([(12, 14, 13), (12, 14, 13), (0, 14, 13)], "KEEP"),
            ([(12, 14, 13), (10, 14, 13), (10, 14, 13)], "INCONCLUSIVE"),
            ([(12, 14, 13), (0, 11, 10), (0, 11, 10)], "REJECT"),
            ([(12, 14, 13), (12, 14, 13), (-2, 0, -1)], "KEEP"),
            ([(12, 14, 13), (12, 14, 13), (-3, -2, -2.5)], "INCONCLUSIVE"),
            ([(12, 14, 13), (12, 14, 13), (-4, -3, -3.5)], "REJECT"),
        ]
        for ranges, decision in cases:
            with self.subTest(ranges=ranges):
                result = su.compare(self.sensitivity_rows(ranges), self.protocol, "selection")
                self.assertEqual(result[0]["decision"], decision)

    def test_clear_cost_rejection_survives_reference_uncertainty(self):
        decision = dict(stage="selection", algorithm="patience", decision="REJECT",
                        clear_constraint_failure=["processes"], reasons=["processes"])
        su.apply_reference_checks([decision], dict(complete=False, noisy_configs=[],
            reference_best_noisy=True, relevant_return_noise=[], conflicts=[dict(stage="selection", algorithm="random")]))
        self.assertEqual(decision["decision"], "REJECT")
        self.assertTrue(decision["diagnostic_flags"])

    def test_same_configuration_conflict_only_three_diagnostic_runs(self):
        request_path = self.root / "evidence/request.json"
        config = dict(s=128, opt="O3")
        request_path.write_text(json.dumps(dict(protocol_sha256=ex.sha256(self.protocol_path), source_stage="holdout",
            events=[dict(returned_config=config, reference_config=config)])))
        manifest = ex.plan(self.protocol_path, "conflict_holdout", conflict_request=request_path)
        self.assertEqual(len(manifest["jobs"]), 3)
        self.assertTrue(all(job["member"] == "both" for job in manifest["jobs"]))

    def test_complete_framework_summary_does_not_hide_torn_driver_cost(self):
        directory, manifest = self.make_plan()
        job = manifest["jobs"][0]
        self.write_job(job, directory)
        manifest["jobs"] = [job]
        (directory / "plan.json").write_text(json.dumps(manifest))
        ledger = directory / "driver.jsonl"
        with ledger.open("a") as stream:
            ex.append_event(stream, "task_start", task=job["id"], attempt_id=0)
        with ledger.open("ab") as stream:
            stream.write(b'{"type":"task_end"')
        original = ledger.read_bytes()
        with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
            ex.execute(directory, manifest, 0)
        self.assertEqual(ledger.read_bytes(), original)

    def test_summary_cli_and_relocated_clone_produce_identical_tables(self):
        reference, ref_plan = self.make_plan("reference")
        selection, selected_plan = self.make_plan()
        for job in ref_plan["jobs"]:
            self.write_job(job, reference)
        search = self.search_job(selected_plan)
        confirmation = next(job for job in selected_plan["jobs"] if job.get("depends_on") == search["id"])
        self.write_job(search, selection)
        self.write_job(confirmation, selection)
        output = self.root / "results/derived"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(su.main(["--protocol", str(self.protocol_path), "--reference", str(reference),
                                     "--runs", str(selection), "--output-dir", str(output)]), 0)
        summary = ex.load_json(output / "summary.json")
        self.assertTrue(summary["reference_complete"])
        self.assertTrue(all(cost["actual_driver_wall_s"] is None for cost in summary["costs"]))
        clone = Path(self.temp.name) / "clone/P1"
        shutil.copytree(self.root, clone)
        cloned_output = clone / "results/regenerated"
        with mock.patch.object(ex, "P1", clone), mock.patch.object(su, "P1", clone), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(su.main(["--protocol", str(clone / "evidence/protocol.json"),
                "--reference", str(clone / reference.relative_to(self.root)),
                "--runs", str(clone / selection.relative_to(self.root)), "--output-dir", str(cloned_output)]), 0)
        for path in output.iterdir():
            self.assertEqual(path.read_bytes(), (cloned_output / path.name).read_bytes(), path.name)

    def test_negative_and_overflowed_acceptance_numbers_rejected(self):
        for key in ("epsilon_pct", "quality_gain_pp", "quality_gain_s", "quality_loss_pp", "wall_increase_fraction", "wall_saving_s"):
            with self.subTest(key=key):
                previous = self.protocol["acceptance"][key]
                self.protocol["acceptance"][key] = -1
                self.save_protocol()
                manifest = ex.plan(self.protocol_path, "selection")
                with self.assertRaises(ValueError):
                    ex.check_frozen(self.protocol, self.protocol_path, manifest)
                self.protocol["acceptance"][key] = previous
        self.save_protocol()
        self.protocol_path.write_text(self.protocol_path.read_text().replace('"epsilon_pct": 5', '"epsilon_pct": 1e309'))
        with self.assertRaises(ValueError):
            ex.load_json(self.protocol_path)
        invalid = self.root / "invalid.jsonl"
        invalid.write_text('{"type":"measurement","kernel_s":1e309}\n')
        with self.assertRaises(ValueError):
            ex.read_records(invalid)

    def test_end_to_end_driver_wall_sums_attempts_and_confirmation(self):
        directory, manifest = self.make_plan()
        job = self.search_job(manifest)
        confirmation = next(item for item in manifest["jobs"] if item.get("depends_on") == job["id"])
        self.write_job(job, directory)
        self.write_job(confirmation, directory)
        with (directory / "driver.jsonl").open("a") as stream:
            for attempt, task, wall in ((0, job["id"], 5), (1, job["id"], 7), (2, confirmation["id"], 3)):
                ex.append_event(stream, "task_start", task=task, attempt_id=attempt)
                ex.append_event(stream, "task_end", task=task, attempt_id=attempt, driver_wall_s=wall)
        batch = su.read_batch(directory, ex.sha256(self.protocol_path))
        runs, _ = su.run_tables([batch], self.protocol, 1)
        row = next(item for item in runs if item["algorithm"] == "random" and item["seed"] == job["seed"])
        self.assertEqual(row["search_full_driver_wall_s"], 12)
        self.assertEqual(row["confirmation_full_driver_wall_s"], 3)
        self.assertEqual(row["total_wall_s"], 15)
        self.assertNotEqual(row["total_wall_s"], row["internal_search_return_wall_s"])

    def test_hard_driver_recovery_does_not_use_internal_wall_as_actual_cost(self):
        directory, manifest = self.make_plan()
        job = self.search_job(manifest)
        confirmation = next(item for item in manifest["jobs"] if item.get("depends_on") == job["id"])
        self.write_job(job, directory)
        self.write_job(confirmation, directory)
        with (directory / "driver.jsonl").open("a") as stream:
            ex.append_event(stream, "task_start", task=job["id"], attempt_id=0)
            ex.append_event(stream, "task_recovery", task=job["id"], attempt_id=0, driver_wall_s=None,
                driver_wall_recorded_lower_bound_s=1, resource_wall_upper_s=100, unrecorded_process_run_upper=0)
            ex.append_event(stream, "task_start", task=confirmation["id"], attempt_id=1)
            ex.append_event(stream, "task_end", task=confirmation["id"], attempt_id=1, driver_wall_s=3)
        batch = su.read_batch(directory, ex.sha256(self.protocol_path))
        runs, _ = su.run_tables([batch], self.protocol, 1)
        row = next(item for item in runs if item["algorithm"] == "random" and item["seed"] == job["seed"])
        self.assertIsNotNone(row["internal_search_return_wall_s"])
        self.assertIsNone(row["search_full_driver_wall_s"])
        self.assertIsNone(row["total_wall_s"])

    def test_machine_rounding_at_two_pp_twelve_pp_and_five_point_six_seconds(self):
        self.protocol["acceptance"].update(quality_gain_pp=12, quality_gain_s=5.6)
        rows = self.sensitivity_rows([(12, 14, 13), (12, 14, 13), (-2, -2, -2)])
        last_seed = self.protocol["online"]["seeds"][-1]
        for row in (item for item in rows if item["seed"] == last_seed):
            time_value = 50 if row["algorithm"] == "random" else 51
            row.update(confirmed_s=time_value, confirmed_min_s=time_value, confirmed_max_s=time_value,
                       reference_median_s=50, gap_pct=100 * (time_value / 50 - 1))
        result = su.compare(rows, self.protocol, "selection")[0]
        self.assertEqual(result["decision"], "KEEP")
        self.assertTrue(result["conditions"]["no_excess_loss"])
        for row in (item for item in rows if item["seed"] != last_seed):
            time_value = 100 if row["algorithm"] == "random" else 94.4
            row.update(confirmed_s=time_value, confirmed_min_s=time_value, confirmed_max_s=time_value,
                       reference_median_s=5.6 / .12, gap_pct=100 * (time_value / (5.6 / .12) - 1))
        result = su.compare(rows, self.protocol, "selection")[0]
        self.assertEqual(result["decision"], "KEEP")
        self.assertEqual(result["robust_gain_pairs"], 2)


if __name__ == "__main__":
    unittest.main()
