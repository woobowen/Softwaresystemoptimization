#!/usr/bin/env python3
"""Recompute tables and online curves from preserved experiment journals."""

import argparse
import csv
import json
import math
from pathlib import Path
import statistics

from experiment import P1, driver_attempts, load_json, read_records, sha256, task_status


def at_least(value, threshold):
    # This only covers binary-float rounding, far below six-decimal C output.
    return value >= threshold or math.isclose(value, threshold, rel_tol=1e-12, abs_tol=1e-12)


def at_most(value, threshold):
    return value <= threshold or math.isclose(value, threshold, rel_tol=1e-12, abs_tol=1e-12)


def write_csv(path, rows, fields):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_batch(directory, protocol_hash):
    directory = Path(directory).resolve()
    manifest = load_json(directory / "plan.json")
    if manifest["protocol_sha256"] != protocol_hash:
        raise ValueError(f"batch has another protocol: {directory}")
    tasks = []
    for job in manifest["jobs"]:
        path = directory / (job["id"] + ".jsonl")
        rows = read_records(path) if path.exists() else []
        tasks.append(dict(job=job, state=task_status(job, directory, manifest, historical_only=True), records=rows,
                          summary=next((r for r in reversed(rows) if r["type"] == "summary"), None)))
    return dict(path=directory, manifest=manifest, tasks=tasks)


def valid_measurement(record, tolerance):
    value, wall = record.get("kernel_s"), record.get("process_wall_s")
    return record["status"] == "ok" and record.get("returncode") == 0 and record.get("spawned") is True and \
        value is not None and wall is not None and \
        math.isfinite(value) and value > 0 and math.isfinite(wall) and wall > 0 and value <= wall + tolerance


def check_trials(task, tolerance):
    rows = task["records"]
    if not rows:
        return
    repeats = rows[0]["metadata"]["repeats"]
    trial_starts, process_starts, completions = {}, {}, {}
    for record in rows:
        kind = record["type"]
        if kind == "trial_start":
            trial_id = record["trial_id"]
            if trial_id in trial_starts:
                raise ValueError(f"duplicate trial start: {task['job']['id']}")
            trial_starts[trial_id] = record
        elif kind in ("measurement_start", "measurement"):
            key = record["trial_id"], record["repeat"]
            trial_start = trial_starts.get(key[0])
            if type(key[1]) is not int or not 0 <= key[1] < repeats or trial_start is None or \
                    record["config"] != trial_start["config"]:
                raise ValueError(f"measurement has no matching trial/repeat: {task['job']['id']}")
            if kind == "measurement_start":
                if key in process_starts or key in completions or record.get("spawned") is not True:
                    raise ValueError(f"duplicate or invalid process start: {task['job']['id']}")
                process_starts[key] = record
            else:
                if key in completions or type(record.get("spawned")) is not bool:
                    raise ValueError(f"duplicate or invalid process completion: {task['job']['id']}")
                start = process_starts.get(key)
                if record["spawned"] != (start is not None) or \
                        (start and (record["config"] != start["config"] or record["command"] != start["command"])):
                    raise ValueError(f"process start/completion mismatch: {task['job']['id']}")
                completions[key] = record
    if task["summary"] and any(key not in completions for key in process_starts):
        raise ValueError(f"complete summary hides an unfinished process: {task['job']['id']}")
    best = None
    for trial in (r for r in rows if r["type"] == "trial"):
        measurements = [r for r in rows if r["type"] == "measurement" and r["trial_id"] == trial["trial_id"]]
        if len({r["repeat"] for r in measurements}) != len(measurements) or \
                any(r["config"] != trial["config"] for r in measurements):
            raise ValueError(f"duplicate repeats or inconsistent configuration: {task['job']['id']}")
        values = [r["kernel_s"] for r in measurements if valid_measurement(r, tolerance)]
        for record in measurements:
            if not valid_measurement(record, tolerance):
                continue
            lines = record["stdout"].splitlines()
            if not lines or float(lines[0]) != record["kernel_s"]:
                raise ValueError(f"recorded kernel time differs from raw stdout: {task['job']['id']}")
            if rows[0]["metadata"]["target"]["require_checksum"]:
                checksum = [line for line in lines[1:] if line.startswith("checksum=")]
                if len(checksum) != 1 or not math.isfinite(float(checksum[0].split("=", 1)[1])) or \
                        float(checksum[0].split("=", 1)[1]) != record.get("checksum"):
                    raise ValueError(f"checksum differs from raw stdout: {task['job']['id']}")
        if trial["score"] is not None:
            if len(measurements) != repeats or len(values) != repeats or \
                    sorted(r["repeat"] for r in measurements) != list(range(repeats)):
                raise ValueError(f"score includes failed/missing samples: {task['job']['id']}")
            score = statistics.median(values)
            if not math.isclose(score, trial["score"], rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f"score does not match raw median: {task['job']['id']}")
            if best is None or score < best["score"]:
                best = dict(config=trial["config"], score=score)
        if trial["best_so_far"] != best:
            raise ValueError(f"best-so-far differs from observed prefix: {task['job']['id']}")
    if task["summary"] and task["summary"]["best"] != best:
        raise ValueError(f"returned best differs from actual trials: {task['job']['id']}")
    if task["summary"]:
        summary = task["summary"]
        measurements = [r for r in rows if r["type"] == "measurement"]
        trials = [r for r in rows if r["type"] == "trial"]
        counts = dict(process_runs=len(process_starts),
                      failed_runs=sum(r["status"] != "ok" for r in measurements),
                      failed_trials=sum(r["status"] != "ok" for r in trials),
                      distinct_configs=len({(r["config"]["s"], r["config"]["opt"]) for r in trials}),
                      proposals=sum(r["type"] == "trial_start" for r in rows))
        if any(summary[key] != value for key, value in counts.items()):
            raise ValueError(f"summary counts differ from the raw journal: {task['job']['id']}")
        sessions = [r["wall_s"] for r in rows if r["type"] == "session_end"]
        unclosed = sum(r["type"] == "session_start" for r in rows) - len(sessions)
        expected_wall = None if unclosed else sum(sessions)
        if summary["tuning_wall_s"] != expected_wall or summary["tuning_wall_recorded_s"] != sum(sessions):
            raise ValueError(f"summary wall cost differs from recorded sessions: {task['job']['id']}")


def sample_rows(batch, tolerance):
    samples = []
    for task in batch["tasks"]:
        check_trials(task, tolerance)
        metadata = task["records"][0]["metadata"] if task["records"] else {}
        for record in (r for r in task["records"] if r["type"] == "measurement"):
            values = dict(stage=batch["manifest"]["stage"], task=task["job"]["id"],
                          role=task["job"]["role"],
                          algorithm=task["job"].get("algorithm", task["job"]["role"]),
                          seed=task["job"]["seed"], round=task["job"].get("round"),
                          trial_id=record["trial_id"], repeat=record["repeat"], **record["config"],
                          kernel_s=record.get("kernel_s"), process_wall_s=record.get("process_wall_s"),
                          recorded_status=record["status"],
                          valid_for_analysis=task["state"] == "complete" and valid_measurement(record, tolerance),
                          returncode=record.get("returncode"), stdout=record["stdout"], stderr=record["stderr"],
                          command=json.dumps(record.get("command")), build_key=record.get("build_key"),
                          source_sha256=metadata.get("target", {}).get("source_sha256"),
                          framework_sha256=metadata.get("framework_sha256"),
                          protocol_sha256=metadata.get("protocol_sha256"))
            samples.append(values)
    return samples


def grid_table(samples, protocol):
    grid = []
    reference_samples = [r for r in samples if r["stage"] == "reference" and r["role"] == "reference"]
    for s in protocol["space"]["blocks"]:
        for opt in protocol["space"]["opts"]:
            matching = [r for r in reference_samples if r["s"] == s and r["opt"] == opt]
            values = [r["kernel_s"] for r in matching if r["valid_for_analysis"]]
            median = statistics.median(values) if values else None
            mad = statistics.median(abs(v - median) for v in values) if values else None
            grid.append(dict(s=s, opt=opt, valid_runs=len(values), failed_runs=len(matching) - len(values),
                             median_s=median, min_s=min(values) if values else None,
                             max_s=max(values) if values else None, mad_s=mad,
                             relative_range=(max(values) - min(values)) / median if values else None,
                             rounds=json.dumps([r["round"] for r in matching if r["valid_for_analysis"]]),
                             samples=json.dumps(values)))
    return grid


def task_driver_walls(batch):
    path = batch["path"] / "driver.jsonl"
    if not path.exists():
        return {}
    starts, ends = driver_attempts(read_records(path))
    walls = {}
    for attempt_id, start in starts.items():
        task = start["task"]
        end = ends.get(attempt_id)
        if end is None or end["type"] == "task_recovery":
            walls[task] = None
        elif walls.get(task, 0) is not None:
            value = end["driver_wall_s"]
            if value is None or not math.isfinite(value) or value < 0:
                raise ValueError("invalid actual driver wall in an experiment journal")
            walls[task] = walls.get(task, 0) + value
    return walls


def run_tables(batches, protocol, reference_time):
    runs, curves = [], []
    for batch in batches:
        driver_walls = task_driver_walls(batch)
        by_id = {task["job"]["id"]: task for task in batch["tasks"]}
        for task in batch["tasks"]:
            job, summary = task["job"], task["summary"]
            if job["action"] != "search":
                continue
            confirm = by_id.get("confirm-" + job["id"])
            confirmed = confirm["summary"] if task["state"] == "complete" and confirm and confirm["state"] == "complete" else None
            found = confirmed["best"]["score"] if confirmed and confirmed["best"] else None
            confirmation_values = [row["kernel_s"] for row in confirm["records"] if row["type"] == "measurement" and row["status"] == "ok"] if confirmed else []
            gap = (found / reference_time - 1) * 100 if found is not None and reference_time is not None else None
            internal_wall = None
            if summary and confirmed and summary["tuning_wall_s"] is not None and confirmed["tuning_wall_s"] is not None:
                internal_wall = summary["tuning_wall_s"] + confirmed["tuning_wall_s"]
            search_wall = driver_walls.get(job["id"])
            confirmation_wall = driver_walls.get("confirm-" + job["id"])
            total_wall = search_wall + confirmation_wall if confirmed and search_wall is not None and confirmation_wall is not None else None
            best = summary.get("best") if summary else None
            runs.append(dict(stage=batch["manifest"]["stage"], algorithm=job["algorithm"], seed=job["seed"],
                             state=task["state"], confirmation_state=confirm["state"] if confirm else "missing",
                             returned_s=best["config"]["s"] if best else None,
                             returned_opt=best["config"]["opt"] if best else None,
                             online_score_s=best["score"] if best else None, confirmed_s=found, gap_pct=gap,
                             confirmed_min_s=min(confirmation_values) if confirmation_values else None,
                             confirmed_max_s=max(confirmation_values) if confirmation_values else None,
                             reference_median_s=reference_time,
                             confirmation_relative_range=(max(confirmation_values) - min(confirmation_values)) / found if confirmation_values else None,
                             near_optimal=at_most(gap, protocol["acceptance"]["epsilon_pct"]) if gap is not None else None,
                             proposals=summary["proposals"] if summary else None,
                             distinct_configs=summary["distinct_configs"] if summary else None,
                             search_process_runs=summary["process_runs"] if summary else None,
                             confirmation_process_runs=confirmed["process_runs"] if confirmed else None,
                             failed_runs=summary["failed_runs"] if summary else None,
                             compile_wall_s=summary["compile_wall_s"] if summary else None,
                             search_internal_window_s=summary["tuning_wall_s"] if summary else None,
                             search_internal_window_recorded_s=summary["tuning_wall_recorded_s"] if summary else None,
                             confirmation_internal_window_s=confirmed["tuning_wall_s"] if confirmed else None,
                             internal_search_return_wall_s=internal_wall,
                             search_full_driver_wall_s=search_wall,
                             confirmation_full_driver_wall_s=confirmation_wall,
                             total_wall_s=total_wall, journal=str((batch["path"] / (job["id"] + ".jsonl")).relative_to(P1))))
            for trial in (r for r in task["records"] if r["type"] == "trial"):
                curves.append(dict(stage=batch["manifest"]["stage"], algorithm=job["algorithm"], seed=job["seed"],
                                   step=trial["trial_id"] + 1, s=trial["config"]["s"], opt=trial["config"]["opt"],
                                   observed_score_s=trial["score"],
                                   best_so_far_s=trial["best_so_far"]["score"] if trial["best_so_far"] else None,
                                   tuning_elapsed_s=trial.get("tuning_elapsed_s"),
                                   tuning_elapsed_recorded_s=trial.get("tuning_elapsed_recorded_s")))
    return runs, curves


def compare(runs, protocol, stage):
    expected = protocol["online"]["seeds"] if stage == "selection" else protocol["holdout"]["seeds"]
    indexed = {}
    for row in (r for r in runs if r["stage"] == stage):
        key = row["algorithm"], row["seed"]
        if key in indexed:
            raise ValueError("duplicate stage/algorithm/seed measurements; do not choose a preferred rerun")
        indexed[key] = row
    rules = protocol["acceptance"]
    decisions = []
    for algorithm in ("stratified", "patience"):
        pairs = [(indexed.get(("random", seed)), indexed.get((algorithm, seed))) for seed in expected]
        if any(a is None or b is None or a["state"] != "complete" or b["state"] != "complete" or
               a["confirmation_state"] != "complete" or b["confirmation_state"] != "complete" or
               a["gap_pct"] is None or b["gap_pct"] is None or
               a["total_wall_s"] is None or b["total_wall_s"] is None for a, b in pairs):
            decisions.append(dict(stage=stage, algorithm=algorithm, decision="INCONCLUSIVE",
                                  reasons=["missing complete paired searches or common confirmations"]))
            continue
        gains_s = [a["confirmed_s"] - b["confirmed_s"] for a, b in pairs]
        gains = [100 * seconds / a["reference_median_s"] for (a, b), seconds in zip(pairs, gains_s)]
        sensitivity_s = [(a["confirmed_min_s"] - b["confirmed_max_s"],
                          a["confirmed_max_s"] - b["confirmed_min_s"]) for a, b in pairs]
        sensitivity_pp = [(100 * low / a["reference_median_s"], 100 * high / a["reference_median_s"])
                          for (a, b), (low, high) in zip(pairs, sensitivity_s)]
        saved = [a["search_process_runs"] - b["search_process_runs"] for a, b in pairs]
        baseline_wall = statistics.median(a["total_wall_s"] for a, b in pairs)
        candidate_wall = statistics.median(b["total_wall_s"] for a, b in pairs)
        no_excess_loss = all(at_least(gain, -rules["quality_loss_pp"]) for gain in gains)
        if algorithm == "stratified":
            conditions = dict(quality=sum(at_least(gain, rules["quality_gain_pp"]) and at_least(seconds, rules["quality_gain_s"])
                                         for gain, seconds in zip(gains, gains_s)) >= rules["improving_seed_count"],
                              no_excess_loss=no_excess_loss, processes=all(value == 0 for value in saved),
                              wall=at_most(candidate_wall, baseline_wall * (1 + rules["wall_increase_fraction"])))
        else:
            conditions = dict(no_excess_loss=no_excess_loss,
                              near_hits=sum(b["near_optimal"] for a, b in pairs) >= sum(a["near_optimal"] for a, b in pairs),
                              processes=sum(value >= rules["minimum_saved_processes"] for value in saved) >= rules["saving_seed_count"],
                              wall=at_least(baseline_wall - candidate_wall, rules["wall_saving_s"]))
        clear_failure = [name for name in ("processes", "wall") if not conditions[name]]
        if any(not at_least(high, -rules["quality_loss_pp"]) for low, high in sensitivity_pp):
            clear_failure.append("quality_risk")
        uncertain = []
        if any(not at_least(low, -rules["quality_loss_pp"]) and at_least(high, -rules["quality_loss_pp"]) for low, high in sensitivity_pp):
            uncertain.append("observed endpoints cross the quality risk boundary; this is not a confidence interval")
        robust_quality = sum(at_least(low_pp, rules["quality_gain_pp"]) and at_least(low_s, rules["quality_gain_s"])
                             for (low_pp, high_pp), (low_s, high_s) in zip(sensitivity_pp, sensitivity_s))
        possible_quality = sum(at_least(high_pp, rules["quality_gain_pp"]) and at_least(high_s, rules["quality_gain_s"])
                               for (low_pp, high_pp), (low_s, high_s) in zip(sensitivity_pp, sensitivity_s))
        if algorithm == "stratified":
            if possible_quality < rules["improving_seed_count"]:
                clear_failure.append("minimum_quality_gain")
            elif robust_quality < rules["improving_seed_count"]:
                uncertain.append("observed endpoints do not establish the minimum gain for enough pairs")
        decision = "REJECT" if clear_failure else "INCONCLUSIVE" if uncertain else \
                   "KEEP" if all(conditions.values()) else "REJECT"
        decisions.append(dict(stage=stage, algorithm=algorithm, decision=decision,
                              conditions=conditions, clear_constraint_failure=clear_failure,
                              quality_gains_pp=gains, quality_gains_s=gains_s,
                              robust_gain_pairs=robust_quality, possible_gain_pairs=possible_quality,
                              descriptive_gain_ranges_pp=sensitivity_pp, descriptive_gain_ranges_s=sensitivity_s,
                              saved_search_processes=saved,
                              baseline_total_wall_median_s=baseline_wall, candidate_total_wall_median_s=candidate_wall,
                              reasons=[name for name, accepted in conditions.items() if not accepted] + uncertain))
    return decisions


def reference_checks(grid, runs, protocol):
    complete = all(row["valid_runs"] == protocol["reference"]["rounds"] and
                   sorted(json.loads(row["rounds"])) == list(range(1, protocol["reference"]["rounds"] + 1))
                   and row["failed_runs"] == 0 for row in grid)
    noisy = [dict(s=row["s"], opt=row["opt"], relative_range=row["relative_range"]) for row in grid
             if row["relative_range"] is not None and
             not at_most(row["relative_range"], protocol["reference"]["noise_relative_range"])]
    indexed = {(row["s"], row["opt"]): row for row in grid}
    best = min(grid, key=lambda row: row["median_s"]) if complete else None
    best_noisy = best is not None and any(row["s"] == best["s"] and row["opt"] == best["opt"] for row in noisy)
    relevant_noise = []
    conflicts = []
    for run in runs:
        key = run["returned_s"], run["returned_opt"]
        original = indexed.get(key)
        if run["confirmed_s"] is None or original is None or original["median_s"] is None:
            continue
        if not at_most(original["relative_range"], protocol["reference"]["noise_relative_range"]) or \
                not at_most(run["confirmation_relative_range"], protocol["reference"]["noise_relative_range"]):
            relevant_noise.append(dict(stage=run["stage"], algorithm=run["algorithm"], seed=run["seed"],
                s=key[0], opt=key[1], reference_relative_range=original["relative_range"],
                confirmation_relative_range=run["confirmation_relative_range"]))
        difference = abs(run["confirmed_s"] / original["median_s"] - 1)
        if not at_most(difference, protocol["reference"]["conflict"]["relative_difference"]):
            conflicts.append(dict(stage=run["stage"], algorithm=run["algorithm"], seed=run["seed"],
                                  s=key[0], opt=key[1], relative_difference=difference,
                                  reference_config_median_s=original["median_s"], confirmed_s=run["confirmed_s"]))
    return dict(complete=complete, noisy_configs=noisy,
                reference_best_config=dict(s=best["s"], opt=best["opt"]) if best else None,
                reference_best_noisy=best_noisy, relevant_return_noise=relevant_noise, conflicts=conflicts)


def conflict_request(checks, grid, protocol, protocol_hash, stage):
    events = []
    if checks["complete"]:
        best = min(grid, key=lambda row: row["median_s"])
        limit = protocol["reference"]["conflict"]["max_" + stage + "_events"]
        matching = [row for row in checks["conflicts"] if row["stage"] == stage]
        for original in grid:
            affected = [row for row in matching if row["s"] == original["s"] and row["opt"] == original["opt"]]
            if affected and len(events) < limit:
                events.append(dict(returned_config=dict(s=original["s"], opt=original["opt"]),
                                   reference_config=dict(s=best["s"], opt=best["opt"]), affected=affected))
    return dict(schema=1, source_stage=stage, protocol_sha256=protocol_hash, events=events)


def apply_reference_checks(decisions, checks):
    for decision in decisions:
        reasons = []
        if not checks["complete"]:
            reasons.append("original reference is incomplete")
        if checks.get("reference_best_noisy") or any(row["stage"] == decision["stage"] and
                row["algorithm"] in ("random", decision["algorithm"]) for row in checks.get("relevant_return_noise", [])):
            reasons.append("reference best or a paired returned configuration exceeds the predeclared noise threshold")
        if any(r["stage"] == decision["stage"] and r["algorithm"] in ("random", decision["algorithm"])
               for r in checks["conflicts"]):
            reasons.append("returned confirmation conflicts with the original reference")
        cost_rejection = any(name in ("processes", "wall") for name in decision.get("clear_constraint_failure", []))
        if reasons and not cost_rejection:
            decision["decision_before_reference_checks"] = decision["decision"]
            decision["decision"] = "INCONCLUSIVE"
            decision["reasons"] += reasons
        elif reasons:
            decision["diagnostic_flags"] = reasons


def retained_algorithms(decisions):
    lookup = {(row["stage"], row["algorithm"]): row["decision"] for row in decisions}
    result = []
    for algorithm in ("stratified", "patience"):
        selection = lookup["selection", algorithm]
        holdout = lookup["holdout", algorithm]
        result.append(dict(algorithm=algorithm, selection=selection, holdout=holdout,
                           retained=selection == "KEEP" and holdout == "KEEP"))
    return result


def cost_table(batches):
    costs = []
    for batch in batches:
        rows = [row for task in batch["tasks"] for row in task["records"]]
        ledger_path = batch["path"] / "driver.jsonl"
        events = read_records(ledger_path) if ledger_path.exists() else []
        starts, ends = driver_attempts(events)
        known_driver = sum(row["driver_wall_s"] for row in ends.values() if row["type"] == "task_end")
        recovered_lower = sum(row["driver_wall_recorded_lower_bound_s"] for row in ends.values()
                              if row["type"] == "task_recovery")
        missing_driver = not starts and bool(rows)
        unknown = missing_driver or starts.keys() != ends.keys() or any(row["type"] == "task_recovery" for row in ends.values())
        upper = sum(row["driver_wall_s"] if row["type"] == "task_end" else row["resource_wall_upper_s"]
                    for row in ends.values()) if not missing_driver and starts.keys() == ends.keys() else None
        costs.append(dict(stage=batch["manifest"]["stage"],
            recorded_spawned_processes=sum(row["type"] == "measurement_start" for row in rows),
            unrecorded_process_run_upper=sum(row.get("unrecorded_process_run_upper", 0) for row in ends.values()),
            failed_measurements=sum(row["type"] == "measurement" and row["status"] != "ok" for row in rows),
            known_process_wall_s=sum(row.get("process_wall_s") or 0 for row in rows if row["type"] == "measurement"),
            compile_processes=sum(row["type"] == "build_start" for row in rows),
            known_compile_wall_s=sum(row.get("compile_wall_s") or 0 for row in rows if row["type"] == "build"),
            actual_driver_wall_s=None if unknown else known_driver,
            driver_wall_recorded_lower_bound_s=known_driver + recovered_lower,
            resource_driver_wall_upper_s=upper, unknown_driver_cost=unknown))
    return costs


def diagnostic_table(batches, grid, runs, protocol):
    indexed = {(row["s"], row["opt"]): row for row in grid}
    output = []
    for batch in batches:
        stage = batch["manifest"]["stage"]
        if not stage.startswith("conflict_"):
            continue
        groups = {}
        for task in batch["tasks"]:
            job = task["job"]
            groups.setdefault((job["event"], job["member"]), []).append(task)
        for (event, member), tasks in groups.items():
            config = tasks[0]["job"]
            samples = [row["kernel_s"] for task in tasks if task["state"] == "complete"
                       for row in task["records"] if row["type"] == "measurement" and row["status"] == "ok"]
            median = statistics.median(samples) if len(samples) == protocol["reference"]["conflict"]["repeats_per_config"] else None
            original = indexed[config["s"], config["opt"]]["median_s"]
            reference_change = abs(median / original - 1) if median is not None and original is not None else None
            primary = [row["confirmed_s"] for row in runs if row["stage"] == stage.removeprefix("conflict_") and
                       row["returned_s"] == config["s"] and row["returned_opt"] == config["opt"] and row["confirmed_s"] is not None]
            unstable = median is not None and any(not at_most(abs(median / value - 1), protocol["reference"]["conflict"]["relative_difference"]) for value in primary)
            output.append(dict(stage=stage, event=event, member=member, s=config["s"], opt=config["opt"],
                valid_runs=len(samples), median_s=median, original_reference_config_median_s=original,
                relative_reference_change=reference_change,
                environment_drift=member in ("reference", "both") and reference_change is not None and
                                  not at_most(reference_change, protocol["reference"]["conflict"]["relative_difference"]),
                return_instability=member in ("returned", "both") and unstable, samples=json.dumps(samples)))
    return output


def protect_output(path, batches, protocol):
    destination = Path(path).resolve()
    roots = {batch["path"] for batch in batches} | {(P1 / name).resolve() for name in protocol["resources"]["formal_batches"]}
    if any(destination == root or destination.is_relative_to(root) for root in roots):
        raise ValueError("derived tables and plots must not be written inside raw measurement batches")


def plots(grid, curves, protocol, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if all(row["valid_runs"] >= protocol["reference"]["rounds"] for row in grid):
        data = [[row["median_s"] for row in grid if row["s"] == s] for s in protocol["space"]["blocks"]]
        fig, ax = plt.subplots(figsize=(7, 5))
        im = ax.imshow(data, aspect="auto", cmap="viridis_r")
        ax.set_xticks(range(4), protocol["space"]["opts"])
        ax.set_yticks(range(5), protocol["space"]["blocks"])
        ax.set_xlabel("Compiler optimization level")
        ax.set_ylabel("Block size s")
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=10,
                        color="white" if im.norm(value) > 0.5 else "black")
        fig.colorbar(im, ax=ax, label="Median kernel time (s), 3 runs")
        fig.tight_layout()
        fig.savefig(directory / "grid_median.png", dpi=180)
        plt.close(fig)
    selected = [r for r in curves if r["stage"] == "selection"]
    if selected:
        seeds = protocol["online"]["seeds"]
        fig, axes = plt.subplots(len(seeds), 2, figsize=(11, 3.2 * len(seeds)), squeeze=False)
        for i, seed in enumerate(seeds):
            for algorithm in protocol["online"]["algorithms"]:
                points = [r for r in selected if r["seed"] == seed and r["algorithm"] == algorithm and r["best_so_far_s"] is not None]
                if not points:
                    continue
                axes[i, 0].step([r["step"] for r in points], [r["best_so_far_s"] for r in points],
                                where="post", marker=".", label=algorithm)
                if all(r["tuning_elapsed_s"] is not None for r in points):
                    axes[i, 1].step([r["tuning_elapsed_s"] for r in points], [r["best_so_far_s"] for r in points],
                                    where="post", marker=".", label=algorithm)
            for j, xlabel in enumerate(("Evaluated configurations", "Internal tuning window elapsed (s)")):
                axes[i, j].set_xlabel(xlabel)
                axes[i, j].set_ylabel("Observed best kernel time (s)")
                axes[i, j].set_title(f"seed={seed}, online repeats={protocol['online']['repeats']}")
                axes[i, j].grid(alpha=0.25)
                axes[i, j].legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(directory / "online_search.png", dpi=180)
        plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=P1 / "evidence" / "protocol_v1.json")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--runs", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--plots", type=Path)
    args = parser.parse_args(argv)
    try:
        protocol = load_json(args.protocol)
        reference = read_batch(args.reference, sha256(args.protocol))
        if reference["manifest"]["stage"] != "reference":
            raise ValueError("--reference must identify the original three-round reference batch")
        batches = [reference, *(read_batch(path, sha256(args.protocol)) for path in args.runs)]
        tolerance = protocol["measurement"]["clock_health"]["kernel_over_process_tolerance_s"]
        samples = [row for batch in batches for row in sample_rows(batch, tolerance)]
        grid = grid_table(samples, protocol)
        complete = all(row["valid_runs"] == protocol["reference"]["rounds"] and row["failed_runs"] == 0 and
                       sorted(json.loads(row["rounds"])) == list(range(1, protocol["reference"]["rounds"] + 1)) for row in grid)
        reference_time = min(row["median_s"] for row in grid) if complete else None
        runs, curves = run_tables(batches[1:], protocol, reference_time)
        decisions = [decision for stage in ("selection", "holdout") for decision in compare(runs, protocol, stage)]
        checks = reference_checks(grid, runs, protocol)
        apply_reference_checks(decisions, checks)
        for decision in decisions:
            if decision["stage"] == "holdout" and not any(row["stage"] == "holdout" and row["algorithm"] == decision["algorithm"] for row in runs):
                selection = next(row for row in decisions if row["stage"] == "selection" and row["algorithm"] == decision["algorithm"])
                if selection["decision"] != "KEEP":
                    decision["decision"] = "NOT_REQUIRED"
                    decision["reasons"] = ["candidate was not retained by selection"]
        costs = cost_table(batches)
        diagnostics = diagnostic_table(batches[1:], grid, runs, protocol)
        output = args.output_dir.resolve()
        protect_output(output, batches, protocol)
        if args.plots:
            protect_output(args.plots, batches, protocol)
        output.mkdir(parents=True, exist_ok=True)
        write_csv(output / "grid_summary.csv", grid,
                  ["s", "opt", "valid_runs", "failed_runs", "median_s", "min_s", "max_s", "mad_s", "relative_range", "rounds", "samples"])
        if samples:
            write_csv(output / "measurements.csv", samples, list(samples[0]))
        if runs:
            write_csv(output / "search_summary.csv", runs, list(runs[0]))
        if curves:
            write_csv(output / "online_curves.csv", curves, list(curves[0]))
        write_csv(output / "batch_costs.csv", costs, list(costs[0]))
        if diagnostics:
            write_csv(output / "reference_conflicts.csv", diagnostics, list(diagnostics[0]))
        for stage in ("selection", "holdout"):
            request = conflict_request(checks, grid, protocol, sha256(args.protocol), stage)
            (output / ("conflict_request_" + stage + ".json")).write_text(json.dumps(request, indent=2, allow_nan=False) + "\n")
        summary = dict(reference_complete=complete, reference_median_s=reference_time,
                       process_measurements=len(samples), invalid_measurements=sum(not r["valid_for_analysis"] for r in samples),
                       reference_checks=checks, decisions=decisions, retained=retained_algorithms(decisions),
                       next_holdout_algorithms=["random", *(row["algorithm"] for row in decisions if row["stage"] == "selection" and row["decision"] == "KEEP")],
                       costs=costs, diagnostics=diagnostics,
                       protocol_sha256=sha256(args.protocol), summarize_sha256=sha256(Path(__file__)))
        summary["batch_manifest_sha256"] = {str(batch["path"].relative_to(P1)): sha256(batch["path"] / "plan.json") for batch in batches}
        (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        if args.plots:
            plots(grid, curves, protocol, args.plots)
        print(json.dumps(summary, indent=2, allow_nan=False))
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
