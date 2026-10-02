#!/usr/bin/env python3
"""Recompute Goal 2 identity scores, shared panels, A/A differences and costs."""

import argparse
import csv
import json
import math
from pathlib import Path
import random
import statistics
import struct

import experiment_v2 as ex
from experiment import load_json, read_records, sha256


def finite_positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def at_least(value, bound):
    return value >= bound or math.isclose(value, bound, rel_tol=1e-12, abs_tol=1e-12)


def at_most(value, bound):
    return value <= bound or math.isclose(value, bound, rel_tol=1e-12, abs_tol=1e-12)


def config_key(config):
    return config["s"], config["opt"]


def describe(values):
    if not values:
        return dict(valid_runs=0, median_s=None, min_s=None, max_s=None, mad_s=None,
                    relative_range=None, samples=[])
    if any(not finite_positive(value) for value in values):
        raise ValueError("sample times must be positive and finite")
    median = statistics.median(values)
    return dict(valid_runs=len(values), median_s=median, min_s=min(values), max_s=max(values),
                mad_s=statistics.median(abs(value - median) for value in values),
                relative_range=(max(values) - min(values)) / median, samples=list(values))


def valid_measurement(row, metadata, tolerance=.005):
    if row.get("status") != "ok" or row.get("returncode") != 0 or row.get("spawned") is not True:
        return False
    value, wall = row.get("kernel_s"), row.get("process_wall_s")
    if not finite_positive(value) or not finite_positive(wall):
        return False
    clock = metadata["target"]["kernel_clock"]
    if row.get("kernel_unit") != "s" or row.get("kernel_clock") != clock or \
            row.get("process_wall_clock") != "CLOCK_MONOTONIC":
        raise ValueError("invalid clock domain or time unit")
    if row.get("clock_unit") != "ns":
        raise ValueError("process boundaries must be integer nanoseconds")
    start, end = row["clock_start_ns"], row["clock_end_ns"]
    if start.keys() != end.keys() or any(type(value) is not int for value in [*start.values(), *end.values()]):
        raise ValueError("invalid process clock boundaries")
    deltas = {name: (end[name] - value) / 1e9 for name, value in start.items()}
    if deltas != row["clock_deltas_s"] or any(not math.isfinite(value) or value < 0 for value in deltas.values()) or \
            deltas.get("CLOCK_MONOTONIC") != wall:
        raise ValueError("clock deltas/seconds differ from the original nanosecond boundaries")
    if clock == row["process_wall_clock"] and value > wall + tolerance:
        return False
    if ex.at.TargetProgram.parse(row["stdout"]) != value:
        raise ValueError("kernel field differs from actual stdout")
    checksum = ex.at.TargetProgram.checksum(row["stdout"])
    if metadata["target"]["require_checksum"] and (checksum is None or checksum != row.get("checksum")):
        raise ValueError("missing or inconsistent raw checksum")
    return True


def replay_observations(metadata, observations):
    """Independently reconstruct the four Goal 2 policies from fresh scores."""
    name, blocks, opts = metadata["algorithm"], metadata["blocks"], metadata["opts"]
    if name not in ("grid", "random", "greedy", "recheck"):
        raise ValueError("this analysis only accepts the frozen Goal 2 policies")
    order = [(s, opt) for s in blocks for opt in opts]
    rng = random.Random(metadata["seed"])
    current = config_key(metadata["greedy_start"]) if metadata.get("greedy_start") else \
        rng.choice(order) if name == "greedy" else None
    if name in ("random", "recheck"):
        rng.shuffle(order)
    explore = min(len(order), metadata["budget"] - 2) if name == "recheck" else len(order)
    if name == "recheck" and (metadata["budget"] < 4 or metadata["repeats"] != 1):
        raise ValueError("S3 requires at least four real-call slots and one process per proposal")
    scores, first, samples, rechecked, finalists, trace = {}, {}, {}, set(), None, []
    best = None

    def neighbors(config):
        s, opt = config
        nearby_s = blocks[max(0, blocks.index(s) - 1):blocks.index(s) + 2]
        nearby_o = opts[max(0, opts.index(opt) - 1):opts.index(opt) + 2]
        return [c for c in order if c != config and ((c[1] == opt and c[0] in nearby_s) or
                                                    (c[0] == s and c[1] in nearby_o))]

    def suggest():
        nonlocal current
        if name == "recheck":
            return next((c for c in order if c not in first), None) if len(first) < explore else \
                next((c for c in finalists if c not in rechecked), None)
        if name != "greedy":
            return next((c for c in order if c not in scores), None)
        if current not in scores:
            return current
        while True:
            near = neighbors(current)
            pending = next((c for c in near if c not in scores), None)
            if pending is not None:
                return pending
            value = lambda c: scores[c] if scores[c] is not None else math.inf
            winner = min([current, *near], key=value)
            if value(winner) >= value(current):
                return None
            current = winner

    def aggregate_best(require_review=False):
        candidates = [c for c in order if scores.get(c) is not None and
                      (not (require_review or rechecked) or c in rechecked)]
        if not candidates:
            return None
        winner = min(candidates, key=lambda c: scores[c])
        return dict(config=dict(s=winner[0], opt=winner[1]), score=scores[winner])

    for observation in observations:
        config, fresh = config_key(observation["config"]), observation["fresh_score"]
        if config != suggest() or (fresh is not None and not finite_positive(fresh)):
            raise ValueError("proposal/feedback differs from the frozen online policy")
        row = dict(config=observation["config"])
        if name == "recheck":
            phase = "recheck" if config in first else "explore"
            values = samples.setdefault(config, [])
            if phase == "explore":
                first[config] = fresh
                scores[config] = fresh
                if fresh is not None:
                    values.append(fresh)
                if len(first) == explore:
                    finalists = sorted((c for c in order if first.get(c) is not None), key=lambda c: first[c])[:2]
            else:
                rechecked.add(config)
                if fresh is not None:
                    values.append(fresh)
                scores[config] = statistics.median(values) if fresh is not None else None
            best = aggregate_best()
            row.update(phase=phase, fresh_score=fresh, score=scores[config], config_samples=list(values),
                return_eligible=config in rechecked and scores[config] is not None,
                finalists=[dict(s=c[0], opt=c[1]) for c in finalists] if finalists is not None else None)
        else:
            scores[config] = fresh
            row["score"] = fresh
            if fresh is not None and (best is None or fresh < best["score"]):
                best = dict(config=observation["config"], score=fresh)
        row["best_so_far"] = best
        trace.append(row)
    exhausted = suggest() is None
    result = dict(trace=trace, best=aggregate_best(True) if name == "recheck" else best,
        exhausted=exhausted, stop_reason="budget" if len(trace) >= metadata["budget"] else
            "local_optimum" if name == "greedy" else "candidate_exhausted" if name == "recheck" else "space_exhausted")
    if name == "recheck":
        result.update(exploration_trials=len(first), recheck_trials=len(rechecked),
            eligible_configs=sum(scores[c] is not None for c in rechecked),
            finalists=[dict(s=c[0], opt=c[1]) for c in finalists] if finalists is not None else None)
    return result


def check_trials(task, tolerance=.005):
    """Replay raw observations; external panels cannot alter an online prefix."""
    rows = task["records"]
    if not rows:
        return
    metadata = rows[0]["metadata"]
    if rows[0]["type"] != "header" or rows[0]["fingerprint"] != ex.at.fingerprint(metadata) or \
            any(row.get("run_id") != rows[0]["run_id"] for row in rows):
        raise ValueError("journal metadata fingerprint or run identity differs")
    starts, completions, trial_starts = {}, {}, {}
    builds = {}
    for row in rows:
        kind = row["type"]
        if kind == "trial_start":
            trial_id = row["trial_id"]
            if trial_id in trial_starts:
                raise ValueError("duplicate trial start")
            trial_starts[trial_id] = row
        elif kind == "build" and row.get("status") == "ok":
            identity = dict(metadata["target"], flags=[*metadata["target"]["flags"], "-" + row["opt"]])
            if row.get("source_sha256") != metadata["target"]["source_sha256"] or \
                    row.get("compiler") != metadata["target"]["compiler"] or \
                    row.get("flags") != identity["flags"] or row["build_key"] != ex.at.fingerprint(identity):
                raise ValueError("build differs from frozen source/compiler/flags")
            builds[row["build_key"]] = row
        elif kind in ("measurement_start", "measurement"):
            key = row["trial_id"], row["repeat"]
            initial = trial_starts.get(key[0])
            if initial is None or row["config"] != initial["config"] or \
                    type(key[1]) is not int or not 0 <= key[1] < metadata["repeats"]:
                raise ValueError("measurement has no matching trial/config/repeat")
            if kind == "measurement_start":
                if key in starts or key in completions or row.get("spawned") is not True:
                    raise ValueError("duplicate or invalid process start")
                starts[key] = row
            else:
                if key in completions or type(row.get("spawned")) is not bool:
                    raise ValueError("duplicate or invalid process completion")
                initial_process = starts.get(key)
                if row["spawned"] != (initial_process is not None) or (initial_process and
                        (row["command"] != initial_process["command"] or
                         row.get("pid") != initial_process.get("pid")) and row["status"] != "interrupted"):
                    raise ValueError("start/completion process identity differs")
                if valid_measurement(row, metadata, tolerance):
                    built = builds.get(row.get("build_key"))
                    if built is None or built["binary_sha256"] != row.get("binary_sha256") or \
                            row["command"] != [built["binary"], str(row["config"]["s"])]:
                        raise ValueError("measurement binary or actual command differs from build")
                completions[key] = row
    trials = [row for row in rows if row["type"] == "trial"]
    if [row["trial_id"] for row in trials] != list(range(len(trials))):
        raise ValueError("trial IDs are not the actual contiguous prefix")
    if len(trials) > metadata["budget"]:
        raise ValueError("observations exceed the declared call budget")
    observations = []
    for trial in trials:
        measurements = [row for key, row in completions.items() if key[0] == trial["trial_id"]]
        values = [row["kernel_s"] for row in measurements if valid_measurement(row, metadata, tolerance)]
        complete = len(measurements) == metadata["repeats"] and len(values) == metadata["repeats"]
        fresh_score = statistics.median(values) if complete else None
        if trial["samples"] != values or (trial["status"] == "ok") != complete:
            raise ValueError("trial samples/status differ from raw process observations")
        observations.append(dict(config=trial["config"], fresh_score=fresh_score))
    replay = replay_observations(metadata, observations)
    for trial, expected in zip(trials, replay["trace"]):
        if any(trial.get(name) != value for name, value in expected.items()):
            raise ValueError("online score/best/eligibility differs from independent raw replay")
    summary = task["summary"]
    if summary is None:
        return
    if starts.keys() != {key for key, row in completions.items() if row["spawned"]} or \
            trial_starts.keys() != {row["trial_id"] for row in trials}:
        raise ValueError("summary hides an unfinished target process")
    if summary["best"] != replay["best"] or summary["stop_reason"] != replay["stop_reason"] or \
            (len(trials) < metadata["budget"] and not replay["exhausted"]):
        raise ValueError("returned configuration differs from the actual online search")
    if metadata["algorithm"] == "recheck" and any(summary[name] != replay[name] for name in
            ("exploration_trials", "recheck_trials", "eligible_configs", "finalists")):
        raise ValueError("S3 summary eligibility/phase counts differ from raw replay")
    counts = dict(proposals=len(trial_starts), attempted_trials=len(trials), process_runs=len(starts),
                  distinct_configs=len({config_key(row["config"]) for row in trials}),
                  completed_configs=sum(row["status"] == "ok" for row in trials),
                  failed_runs=sum(row["status"] != "ok" for row in completions.values()),
                  failed_trials=sum(row["status"] != "ok" for row in trials),
                  interrupted_runs=sum(row["status"] == "interrupted" for row in completions.values()))
    if any(summary[name] != value for name, value in counts.items()):
        raise ValueError("summary call/configuration counts differ from the raw journal")
    sessions = [row["wall_s"] for row in rows if row["type"] == "session_end"]
    incomplete = sum(row["type"] == "session_start" for row in rows) - len(sessions)
    if any(not math.isfinite(value) or value < 0 for value in sessions) or \
            summary["tuning_wall_s"] != (None if incomplete else sum(sessions)):
        raise ValueError("invalid or hidden session cost")
    build_rows = [row for row in rows if row["type"] == "build"]
    build_starts = [row for row in rows if row["type"] == "build_start"]
    completed_pids = {row["compile"].get("pid") for row in build_rows if not row["cached"]}
    unfinished = sum(row.get("pid") not in completed_pids for row in build_starts)
    if any(not math.isfinite(row["compile_wall_s"]) or row["compile_wall_s"] < 0 for row in build_rows) or \
            summary["compile_wall_s"] != (None if unfinished else sum(row["compile_wall_s"] for row in build_rows)) or \
            summary["compile_processes"] != len(build_starts) or summary["incomplete_builds"] != unfinished or \
            summary["cached_builds"] != sum(row["cached"] for row in build_rows):
        raise ValueError("invalid or hidden compilation/build-check cost")


def read_batch(directory, protocol_path, reference=None):
    directory = Path(directory).resolve()
    manifest = load_json(directory / "plan.json")
    protocol = load_json(protocol_path)
    protocol.update(protocol_sha256=sha256(protocol_path), measurement_root=manifest["measurement_root"],
                    protocol_path=manifest["protocol"])
    ex.freeze_check(protocol, manifest, protocol_path)
    flat_jobs, panels = [], []
    for job in manifest["jobs"]:
        if job["action"] != "panel":
            flat_jobs.append(job)
            continue
        path = directory / (job["id"] + ".json")
        if not path.exists():
            continue
        if reference is None:
            raise ValueError("shared panel requires its frozen reference input")
        expected = ex.panel(job, directory, reference, protocol, historical=True)
        saved = load_json(path)
        if saved["jobs"] != expected:
            raise ValueError("common panel jobs differ from frozen returns and order")
        panels.append(saved)
        flat_jobs.extend(saved["jobs"])
    if len({job["id"] for job in flat_jobs}) != len(flat_jobs):
        raise ValueError("duplicate actual jobs in a batch")
    tasks = []
    for job in flat_jobs:
        path = directory / (job["id"] + ".jsonl")
        rows = read_records(path) if path.exists() else []
        summary = next((row for row in reversed(rows) if row["type"] == "summary"), None)
        if summary and summary.get("failed_trials", 0) > 0:
            expected = ex.common_metadata(protocol, job, Path(manifest["measurement_root"]))
            if rows[0].get("metadata") != expected or rows[0].get("fingerprint") != ex.at.fingerprint(expected):
                raise ValueError("failed journal settings differ from its frozen job")
            ex.validate_trace(rows, expected, job)
            state = "failed"
        else:
            state = ex.validate_task(job, directory, protocol, historical=True)
        task = dict(job=job, records=rows, state=state, summary=summary)
        check_trials(task)
        tasks.append(task)
    driver = read_records(directory / "driver.jsonl") if (directory / "driver.jsonl").exists() else []
    return dict(path=directory, manifest=manifest, tasks=tasks, panels=panels, driver=driver)


def samples_from_batches(batches):
    samples, binary_ids = [], {}
    for batch in batches:
        for task in batch["tasks"]:
            if not task["records"]:
                continue
            metadata, job = task["records"][0]["metadata"], task["job"]
            for row in (row for row in task["records"] if row["type"] == "measurement"):
                valid = task["state"] == "complete" and valid_measurement(row, metadata)
                if valid:
                    key = metadata["target"]["source_sha256"], row["config"]["opt"]
                    prior = binary_ids.setdefault(key, row["binary_sha256"])
                    if prior != row["binary_sha256"]:
                        raise ValueError("the same target/O has different binaries in a common comparison")
                sample = dict(stage=batch["manifest"]["stage"], task=job["id"],
                    role=job["role"], block=job.get("block"), round=job.get("round"),
                    method=job.get("method"), tier=job.get("tier"), label=job.get("label"), pair=job.get("pair"),
                    seed=job.get("seed"), algorithm=job.get("algorithm"), **row["config"],
                    trial_id=row["trial_id"], repeat=row["repeat"], valid=valid, spawned=row["spawned"],
                    phase=next((trial.get("phase", "explore") for trial in task["records"] if
                        trial["type"] == "trial" and trial["trial_id"] == row["trial_id"]), None),
                    status=row["status"], returncode=row["returncode"], kernel_s=row.get("kernel_s"),
                    process_wall_s=row.get("process_wall_s"), source_sha256=metadata["target"]["source_sha256"],
                    binary_sha256=row.get("binary_sha256"), command=row.get("command"))
                samples.append(sample)
    return samples


def reference_table(samples, protocol):
    grid = []
    for s in protocol["space"]["blocks"]:
        for opt in protocol["space"]["opts"]:
            rows = [row for row in samples if row["role"] == "reference" and (row["s"], row["opt"]) == (s, opt)]
            valid = [row for row in rows if row["valid"]]
            cell = dict(s=s, opt=opt, failed_runs=len(rows) - len(valid), excluded_runs=0,
                        rounds=[row["round"] for row in valid], **describe([row["kernel_s"] for row in valid]))
            grid.append(cell)
    complete = all(row["valid_runs"] == protocol["reference"]["rounds"] and
        sorted(row["rounds"]) == list(range(1, protocol["reference"]["rounds"] + 1)) and
        row["failed_runs"] == 0 for row in grid)
    if complete:
        best = min(grid, key=lambda row: row["median_s"])
        for cell in grid:
            cell["gap_ref_pct"] = 100 * (cell["median_s"] / best["median_s"] - 1)
    return grid, complete


def panel_table(samples, batches):
    panels, identities = [], set()
    for batch in batches:
        for panel in batch["panels"]:
            for config in panel["configs"]:
                identity = batch["manifest"]["stage"], panel["block"], config_key(config)
                if identity in identities:
                    raise ValueError("repeated common-panel identity cannot replace earlier evidence")
                identities.add(identity)
                rows = [row for row in samples if row["stage"] == batch["manifest"]["stage"] and
                    row["role"] == "shared_confirmation" and row["block"] == panel["block"] and
                    (row["s"], row["opt"]) == config_key(config)]
                values = [row["kernel_s"] for row in rows if row["valid"]]
                panels.append(dict(stage=batch["manifest"]["stage"], block=panel["block"], seed=panel["seed"],
                    **config, reference_config=panel["reference_config"],
                    complete=len(values) == 3 and sorted(row["round"] for row in rows if row["valid"]) == [1, 2, 3],
                    actual_processes=len(rows), **describe(values)))
    return panels


def gain_bounds(baseline, candidate, anchor, same_config=False):
    if same_config:
        return 0.0, 0.0
    if not anchor.get("samples") or not baseline.get("samples") or not candidate.get("samples"):
        return None, None
    # All numerator/anchor corners preserve the correct sign when the gap crosses zero.
    values = [100 * numerator / denominator for numerator in
        (baseline["min_s"] - candidate["max_s"], baseline["max_s"] - candidate["min_s"])
        for denominator in (anchor["min_s"], anchor["max_s"])]
    return min(values), max(values)


def gap_bounds(config, reference, same_config=False):
    if same_config:
        return 0.0, 0.0
    if not config.get("samples") or not reference.get("samples"):
        return None, None
    return (100 * (config["min_s"] / reference["max_s"] - 1),
            100 * (config["max_s"] / reference["min_s"] - 1))


def ranges_conflict(a, b, resolution_pp):
    if None in (*a, *b):
        return True
    return max(a[0] - b[1], b[0] - a[1]) > resolution_pp + 1e-12


def classify(gap, ref_bounds, panel_bounds, epsilon=5, resolution_pp=0, same_config=False):
    if gap is None or None in (*ref_bounds, *panel_bounds):
        return "uncertain"
    if ranges_conflict(ref_bounds, panel_bounds, resolution_pp):
        return "reference_panel_conflict"
    padding = 0 if same_config else resolution_pp
    if at_most(max(ref_bounds[1], panel_bounds[1]) + padding, epsilon):
        return "near_optimal_observed"
    if not at_most(min(ref_bounds[0], panel_bounds[0]) - padding, epsilon):
        return "clearly_worse_observed"
    return "uncertain"


def driver_costs(batch):
    costs = {}
    for row in batch["driver"]:
        if row["type"] != "task_end":
            continue
        key = row["task"]
        if row.get("driver_wall_s") is None:
            costs[key] = None
        elif not math.isfinite(row["driver_wall_s"]) or row["driver_wall_s"] < 0:
            raise ValueError("invalid full driver cost")
        elif costs.get(key, 0) is not None:
            costs[key] = costs.get(key, 0) + row["driver_wall_s"]
    return costs


def search_tables(batches, grid, panels, protocol):
    indexed = {config_key(row): row for row in grid}
    complete = all(row.get("gap_ref_pct") is not None for row in grid)
    reference = min(grid, key=lambda row: row["median_s"]) if complete else None
    panel_index = {(row["stage"], row["block"], config_key(row)): row for row in panels}
    runs, curves = [], []
    for batch in batches:
        costs = driver_costs(batch)
        for task in batch["tasks"]:
            job, summary = task["job"], task["summary"]
            if job["action"] != "search":
                continue
            best = summary.get("best") if summary else None
            config = best["config"] if best else None
            cell = indexed.get(config_key(config)) if config else None
            panel = panel_index.get((batch["manifest"]["stage"], job.get("block"), config_key(config))) if config else None
            panel_ref = panel_index.get((batch["manifest"]["stage"], job.get("block"), config_key(reference))) if reference else None
            same_ref = config is not None and reference is not None and config_key(config) == config_key(reference)
            ref_bounds = gap_bounds(cell, reference, same_ref) if cell and reference else (None, None)
            conf_bounds = gap_bounds(panel, panel_ref, same_ref) if panel and panel_ref else (None, None)
            gap = cell.get("gap_ref_pct") if cell else None
            panel_gap = 100 * (panel["median_s"] / panel_ref["median_s"] - 1) if panel and panel_ref and \
                panel["complete"] and panel_ref["complete"] else None
            runs.append(dict(stage=batch["manifest"]["stage"], block=job.get("block"), seed=job["seed"],
                algorithm=job["algorithm"], state=task["state"], returned_s=config["s"] if config else None,
                returned_opt=config["opt"] if config else None, online_score_s=best["score"] if best else None,
                reference_s=cell["median_s"] if cell else None, gap_ref_pct=gap,
                gap_ref_low_pct=ref_bounds[0], gap_ref_high_pct=ref_bounds[1],
                panel_median_s=panel["median_s"] if panel else None, panel_gap_pct=panel_gap,
                panel_gap_low_pct=conf_bounds[0], panel_gap_high_pct=conf_bounds[1],
                point_near_optimal=at_most(gap, protocol["acceptance"]["epsilon_pct"]) if gap is not None else None,
                quality_class=classify(gap, ref_bounds, conf_bounds, protocol["acceptance"]["epsilon_pct"],
                    protocol["measurement"]["clock_health"]["resolution_pp"], same_ref),
                proposals=summary["proposals"] if summary else None,
                distinct_configs=summary["distinct_configs"] if summary else None,
                process_runs=summary["process_runs"] if summary else None,
                internal_rechecks=summary.get("recheck_trials", 0) if summary else None,
                stop_reason=summary["stop_reason"] if summary else None,
                failed_runs=summary["failed_runs"] if summary else None,
                compile_wall_s=summary["compile_wall_s"] if summary else None,
                tuning_wall_s=summary["tuning_wall_s"] if summary else None,
                search_driver_wall_s=costs.get(job["id"]),
                shared_panel_id=f"{batch['manifest']['stage']}/panel-b{job.get('block')}",
                journal=f"{batch['path'].name}/{job['id']}.jsonl"))
            for trial in (row for row in task["records"] if row["type"] == "trial"):
                curves.append(dict(stage=batch["manifest"]["stage"], block=job.get("block"), seed=job["seed"],
                    algorithm=job["algorithm"], step=trial["trial_id"] + 1, **trial["config"],
                    actual_calls=sum(row["type"] == "measurement_start" and row["trial_id"] <= trial["trial_id"]
                        for row in task["records"]),
                    phase=trial.get("phase", "explore"), observed_score_s=trial["score"],
                    fresh_score_s=trial.get("fresh_score", trial["score"]),
                    best_so_far_s=trial["best_so_far"]["score"] if trial["best_so_far"] else None,
                    tuning_elapsed_s=trial.get("tuning_elapsed_s")))
    return runs, curves


def aa_table(samples, require_complete=True):
    rows = []
    for method in ("M0", "M1"):
        for tier in ("F", "M"):
            selected = [row for row in samples if row["role"] == "aa" and row["method"] == method and row["tier"] == tier]
            identities = [(row["label"], row["pair"]) for row in selected]
            if len(set(identities)) != len(identities) or len({config_key(row) for row in selected}) > 1 or \
                    any(label not in ("A", "B") or pair not in (1, 2, 3) for label, pair in identities):
                raise ValueError("A/A labels need six distinct independent samples of the same configuration")
            a = {row["pair"]: row["kernel_s"] for row in selected if row["label"] == "A" and row["valid"]}
            b = {row["pair"]: row["kernel_s"] for row in selected if row["label"] == "B" and row["valid"]}
            complete = len(a) == len(b) == 3 and a.keys() == b.keys()
            if require_complete and not complete:
                raise ValueError("A/A needs three real independent A and B samples per tier/method")
            a_stats, b_stats = describe(list(a.values())), describe(list(b.values()))
            pairs = sorted(a.keys() & b.keys())
            rows.append(dict(method=method, tier=tier, a=a_stats, b=b_stats,
                complete=complete, observed_runs=len(selected), failed_runs=sum(not row["valid"] for row in selected),
                paired_ids=pairs,
                signed_median_difference_pct=100 * (b_stats["median_s"] / a_stats["median_s"] - 1)
                    if a and b else None,
                paired_difference_s=[b[pair] - a[pair] for pair in pairs],
                paired_difference_pct=[100 * (b[pair] / a[pair] - 1) for pair in pairs]))
    return rows


def rank_checks(samples, aa, method, resolution_pp):
    results = []
    for label in ("A", "B"):
        values = {row["tier"]: row[label.lower()]["median_s"] for row in aa if row["method"] == method}
        results.append(dict(group="label_" + label, fast_s=values["F"], medium_s=values["M"]))
    blocks = sorted({row["block"] for row in samples if row["role"] == "aa" and row["method"] == method})
    if len(blocks) != 2:
        raise ValueError("each diagnostic method needs two balanced phases")
    for block in blocks:
        values = {tier: statistics.median(row["kernel_s"] for row in samples if row["role"] == "aa" and
                  row["method"] == method and row["tier"] == tier and row["block"] == block and row["valid"])
                  for tier in ("F", "M")}
        results.append(dict(group=f"phase_{block}", fast_s=values["F"], medium_s=values["M"]))
    for row in results:
        row["signed_gap_pct"] = 100 * (row["medium_s"] / row["fast_s"] - 1)
        row["absolute_gap_pct"] = 100 * (max(row["fast_s"], row["medium_s"]) / min(row["fast_s"], row["medium_s"]) - 1)
    signs = {row["signed_gap_pct"] > 0 for row in results if row["signed_gap_pct"] != 0}
    supported = len(signs) == 1 and all(row["absolute_gap_pct"] > resolution_pp for row in results)
    return dict(comparisons=results, rank_consistent_and_resolved=supported)


def choose_arrangement(aa, samples):
    if len(aa) != 4 or any(not row.get("complete", False) for row in aa):
        return dict(arrangement=None, resolution_pp=None, performance_gate=False,
            rationale="incomplete_independent_AA", metrics=None,
            incomplete_cells=[dict(method=row["method"], tier=row["tier"]) for row in aa if not row["complete"]],
            population_false_positive_rate_estimated=False)
    metrics = {}
    for method in ("M0", "M1"):
        rows = [row for row in aa if row["method"] == method]
        metrics[method] = dict(D=max(abs(row["signed_median_difference_pct"]) for row in rows),
            P=max(abs(value) for row in rows for value in row["paired_difference_pct"]))
    resolutions = {method: max(1, math.ceil(max(values.values()))) for method, values in metrics.items()}
    ranks = {method: rank_checks(samples, aa, method, resolutions[method]) for method in metrics}
    zero, one = metrics["M0"], metrics["M1"]
    improved = zero["D"] > 0 and at_most(one["D"], .75 * zero["D"]) and \
        at_least(zero["D"] - one["D"], 1) and at_most(one["P"], zero["P"] + 2)
    acceptable = at_most(one["D"], zero["D"] + 1) and at_most(one["P"], zero["P"] + 2)
    chosen = "M1" if (improved or acceptable) and ranks["M1"]["rank_consistent_and_resolved"] else "M0"
    return dict(metrics=metrics, arrangement=chosen,
        rationale="observed_AA_reduction" if chosen == "M1" and improved else
            "shorter_confirmation_distance" if chosen == "M1" else "M1_worse_AA_or_unresolved_rank",
        resolution_pp=resolutions[chosen], ranks=ranks,
        performance_gate=ranks[chosen]["rank_consistent_and_resolved"],
        false_differences_above_5_pct=sum(abs(row["signed_median_difference_pct"]) > 5 for row in aa),
        population_false_positive_rate_estimated=False)


def paired_rows(runs, grid, panels, protocol, stage):
    reference = min(grid, key=lambda row: row["median_s"])
    indexed = {config_key(row): row for row in grid}
    panel_index = {(row["stage"], row["block"], config_key(row)): row for row in panels}
    run_index = {}
    for row in runs:
        if row["stage"] != stage:
            continue
        identity = row["stage"], row["algorithm"], row["seed"]
        if identity in run_index:
            raise ValueError("duplicate real search identity cannot overwrite a prior batch")
        run_index[identity] = row
    seeds = protocol["online"]["seeds"] if stage == "comparison" else protocol["holdout"]["seeds"]
    pairs = []
    for seed in seeds:
        a, b = run_index.get((stage, "random", seed)), run_index.get((stage, "recheck", seed))
        if a is None or b is None:
            continue
        ca, cb = (a["returned_s"], a["returned_opt"]), (b["returned_s"], b["returned_opt"])
        pa, pb = panel_index.get((stage, a["block"], ca)), panel_index.get((stage, b["block"], cb))
        pref = panel_index.get((stage, a["block"], config_key(reference)))
        same = ca == cb and ca in indexed
        ref_bounds = gain_bounds(indexed.get(ca, {}), indexed.get(cb, {}), reference, same)
        panel_bounds = gain_bounds(pa or {}, pb or {}, pref or {}, same)
        wall_a, wall_b = a["search_driver_wall_s"], b["search_driver_wall_s"]
        valid = a["state"] == b["state"] == "complete" and pa is not None and pb is not None and \
            pref is not None and pa["complete"] and pb["complete"] and pref["complete"]
        pairs.append(dict(stage=stage, seed=seed, block=a["block"], valid=valid, same_config=same,
            baseline_config=dict(s=ca[0], opt=ca[1]), candidate_config=dict(s=cb[0], opt=cb[1]),
            gain_ref_pp=a["gap_ref_pct"] - b["gap_ref_pct"] if ca in indexed and cb in indexed else None,
            gain_ref_low_pp=ref_bounds[0], gain_ref_high_pp=ref_bounds[1],
            gain_panel_pp=100 * (pa["median_s"] - pb["median_s"]) / pref["median_s"] if valid else None,
            gain_panel_low_pp=panel_bounds[0], gain_panel_high_pp=panel_bounds[1],
            reference_panel_conflict=ranges_conflict(ref_bounds, panel_bounds,
                protocol["measurement"]["clock_health"]["resolution_pp"]),
            baseline_calls=a["process_runs"], candidate_calls=b["process_runs"],
            baseline_wall_s=wall_a, candidate_wall_s=wall_b,
            wall_saving_fraction=1 - wall_b / wall_a if finite_positive(wall_a) and finite_positive(wall_b) else None))
    return pairs


def decision(pairs, protocol, expected_count, project_cost_complete=True):
    rules = protocol["acceptance"]
    rho = protocol["measurement"]["clock_health"]["resolution_pp"]
    if protocol.get("state") != "approved" or rules.get("state") != "frozen" or not finite_positive(rho):
        return dict(decision="INCONCLUSIVE", reasons=["formal protocol and diagnostic resolution are not frozen"])
    if not project_cost_complete:
        return dict(decision="INCONCLUSIVE", reasons=["global actual cost ledger is missing, unfinished, or contains recovered unknown cost"])
    if len(pairs) != expected_count or any(not row["valid"] or row["gain_ref_pp"] is None or
            row["wall_saving_fraction"] is None or None in (row["gain_ref_low_pp"], row["gain_ref_high_pp"],
            row["gain_panel_low_pp"], row["gain_panel_high_pp"]) for row in pairs):
        return dict(decision="INCONCLUSIVE", reasons=["missing valid paired searches/panels or known actual cost"])
    if any(row["baseline_calls"] != protocol["online"]["budget"] or
            row["candidate_calls"] != protocol["online"]["budget"] for row in pairs):
        return dict(decision="INCONCLUSIVE", reasons=["incomplete equal-call-budget comparison"])
    if any(row.get("reference_panel_conflict") for row in pairs):
        return dict(decision="INCONCLUSIVE", reasons=["reference and simultaneous panel conflict beyond diagnostic resolution"])
    loss = rules["quality_loss_pp"]
    lows = [min(row["gain_ref_low_pp"], row["gain_panel_low_pp"]) - (0 if row["same_config"] else rho) for row in pairs]
    highs = [max(row["gain_ref_high_pp"], row["gain_panel_high_pp"]) + (0 if row["same_config"] else rho) for row in pairs]
    clear_loss = any(not at_least(value, -loss) for value in highs)
    severe = any(not at_least(value, -rules["severe_regression_pp"]) for value in highs)
    if clear_loss or severe:
        return dict(decision="REJECT", reasons=["observed quality risk exceeds the frozen limit"], severe_regression=severe)
    risk_safe = all(at_least(value, -loss) for value in lows)
    gains = [row["gain_ref_pp"] for row in pairs]
    saving = statistics.median(row["wall_saving_fraction"] for row in pairs)
    useful_quality = at_least(statistics.median(lows), rules["quality_gain_median_pp"]) and \
        sum(at_least(value, rules["quality_gain_seed_pp"]) for value in lows) >= rules["minimum_improving_seeds"]
    quality_supported = at_least(statistics.median(lows), rules["quality_gain_median_pp"])
    quality_cost = at_least(saving, -rules["quality_cost_increase_fraction"])
    efficiency = at_least(saving, rules["efficiency_wall_saving_fraction"])
    conditions = dict(risk_safe=risk_safe, useful_quality=useful_quality, quality_supported=quality_supported,
                      quality_cost=quality_cost, efficiency=efficiency)
    if not risk_safe:
        status, reasons = "INCONCLUSIVE", ["descriptive ranges cross the 2pp risk limit; they are not confidence intervals"]
    elif efficiency:
        status, reasons = "KEEP", ["quality-safe measured time saving route passed"]
    elif useful_quality and quality_supported and quality_cost:
        status, reasons = "KEEP", ["quality route passed for these measured blocks"]
    else:
        status, reasons = "REJECT", ["no useful gain under the frozen quality/cost decision table"]
    return dict(decision=status, reasons=reasons, conditions=conditions,
                median_gain_ref_pp=statistics.median(gains), median_wall_saving_fraction=saving)


def final_retention(selection, confirmation):
    return dict(selection=selection["decision"], confirmation=confirmation["decision"],
                retained=selection["decision"] == confirmation["decision"] == "KEEP",
                default_algorithm="recheck" if selection["decision"] == confirmation["decision"] == "KEEP" else "random")


def cost_table(batches, ledger_rows=None):
    """Count every actual driver attempt once; common panels have no per-algorithm copies."""
    attempts, context = {}, {}
    for batch in batches:
        roles = {task["job"]["id"]: task["job"]["role"] for task in batch["tasks"]}
        for row in batch["driver"]:
            if row["type"] != "task_end":
                continue
            identity = row["attempt_id"]
            if identity in attempts:
                raise ValueError("shared actual attempt would be counted twice")
            attempts[identity] = row
            context[identity] = batch["manifest"]["stage"], roles.get(row["task"], row["role"])
    unfinished, missing_jobs, starts, ends = [], [], {}, {}
    if ledger_rows is not None:
        starts, ends = {}, {}
        for row in ledger_rows:
            if row["type"] == "task_start":
                if row["attempt_id"] in starts:
                    raise ValueError("duplicate global ledger attempt")
                starts[row["attempt_id"]] = row
            elif row["type"] == "task_end":
                identity = row["attempt_id"]
                if identity not in starts or identity in ends or row["task"] != starts[identity]["task"]:
                    raise ValueError("global ledger completion has no matching unique start")
                ends[identity] = row
        for identity, row in attempts.items():
            actual = {key: value for key, value in row.items() if key not in ("type", "at")}
            recorded = {key: value for key, value in ends.get(identity, {}).items() if key not in ("type", "at")}
            if identity not in ends or actual != recorded:
                raise ValueError("batch cost differs from the same actual global ledger attempt")
        attempts = ends
        unfinished = [identity for identity in starts if identity not in ends]
        for batch in batches:
            for task in batch["tasks"]:
                task_rows = [row for row in batch["driver"] if row["type"] == "task_end" and row["task"] == task["job"]["id"]]
                recorded_starts = sum(row["type"] == "measurement_start" for row in task["records"])
                if recorded_starts and batch.get("path") is not None:
                    # A guarded task can finish in the global ledger before the
                    # batch driver appends its copy. Match the actual journal,
                    # not just the reusable task label, without writing raw.
                    journal = Path(batch["path"]).resolve() / (task["job"]["id"] + ".jsonl")
                    try:
                        expected_journal = str(journal.relative_to(ex.P1.resolve()))
                    except ValueError:
                        expected_journal = None
                    if expected_journal is not None:
                        matched = [row for identity, row in ends.items() if row["task"] == task["job"]["id"] and
                                   starts[identity].get("journal") == expected_journal]
                        if any(row["attempt_id"] not in {end["attempt_id"] for end in matched} for row in task_rows):
                            raise ValueError("batch cost task does not match its actual global journal")
                        task_rows = matched
                        for row in task_rows:
                            context[row["attempt_id"]] = batch["manifest"]["stage"], task["job"]["role"]
                if not task_rows:
                    if recorded_starts:
                        missing_jobs.append(dict(stage=batch["manifest"]["stage"], task=task["job"]["id"],
                                                 recorded_process_starts=recorded_starts))
                    continue
                if any(not row.get("n4096_calls_known", True) for row in task_rows):
                    continue
                if sum(row["n4096_calls"] for row in task_rows) != recorded_starts:
                    raise ValueError("actual task attempts do not match the target journal process starts")
    grouped = {}
    for identity, row in attempts.items():
        stage, role = context.get(identity, ("goal", row["role"]))
        target = grouped.setdefault((stage, role), dict(stage=stage, role=role, process_runs=0,
            process_runs_known=True, recorded_process_lower=0,
            full_driver_wall_s=0.0, conservative_resource_s=0.0, failed_tasks=0, tasks=0,
            domains_s=dict(monotonic=0.0, raw=0.0, realtime=0.0), unknown_attempts=[]))
        if type(row["n4096_calls"]) is not int or row["n4096_calls"] < 0:
            raise ValueError("invalid actual target process count")
        target["process_runs"] += row["n4096_calls"]
        known = row.get("n4096_calls_known", True) and row.get("driver_wall_s") is not None and \
            row.get("clock_elapsed_s") is not None and row.get("resource_bound_basis") is None
        if ledger_rows is not None and known:
            start, end = starts[identity]["clock_start_ns"], row["clock_end_ns"]
            if set(start) != {"monotonic", "raw", "realtime"} or start.keys() != end.keys() or \
                    any(type(value) is not int for value in [*start.values(), *end.values()]):
                raise ValueError("invalid global cost boundary domains or nanoseconds")
            spans = {name: (end[name] - value) / 1e9 for name, value in start.items()}
            if any(not math.isfinite(value) or value < 0 for value in spans.values()) or \
                    spans != row["clock_elapsed_s"] or spans["monotonic"] != row["driver_wall_s"] or \
                    max(spans.values()) != row["resource_wall_s"] or \
                    row.get("resource_s", row["resource_wall_s"]) != max(spans.values()):
                raise ValueError("actual task costs differ from the original multi-domain boundaries")
            if row["n4096_calls"] > starts[identity]["call_upper"]:
                raise ValueError("actual task calls exceed the reserved target-call upper bound")
        target["process_runs_known"] = target["process_runs_known"] and row.get("n4096_calls_known", True)
        target["recorded_process_lower"] += row.get("n4096_call_recorded_lower", row["n4096_calls"])
        if not known:
            target["unknown_attempts"].append(identity)
        for name, field in (("full_driver_wall_s", "driver_wall_s"), ("conservative_resource_s", "resource_wall_s")):
            value = row.get(field)
            if value is None:
                target[name] = None
            elif not math.isfinite(value) or value < 0:
                raise ValueError("invalid actual driver/resource cost")
            elif target[name] is not None:
                target[name] += value
        if row.get("clock_elapsed_s") is None:
            target["domains_s"] = dict.fromkeys(target["domains_s"], None)
        for domain, value in (row.get("clock_elapsed_s") or {}).items():
            if domain not in target["domains_s"] or not math.isfinite(value) or value < 0:
                raise ValueError("invalid cost time domain")
            if target["domains_s"][domain] is not None:
                target["domains_s"][domain] += value
        target["failed_tasks"] += row["returncode"] != 0 or row.get("reason") is not None
        target["tasks"] += 1
    rows = list(grouped.values())
    complete = ledger_rows is not None and not unfinished and not missing_jobs and all(not row["unknown_attempts"] and
        row["conservative_resource_s"] is not None for row in rows)
    recorded_calls = sum(row["process_runs"] for row in rows)
    totals = dict(actual_process_runs=recorded_calls if complete else None,
                  charged_process_upper=recorded_calls if not unfinished and not missing_jobs else None,
                  recorded_ledger_charged_calls=recorded_calls,
                  missing_job_raw_starts=sum(row["recorded_process_starts"] for row in missing_jobs))
    return dict(rows=rows, unfinished_attempts=unfinished, missing_jobs=missing_jobs, complete=complete, totals=totals)


def component_costs(batches, samples):
    """Target/compile subcosts describe the full driver bill; they are not added to it."""
    grouped = {}
    for row in samples:
        component = "internal_recheck" if row["role"] == "search" and row["phase"] == "recheck" else row["role"]
        target = grouped.setdefault((row["stage"], component), dict(stage=row["stage"], component=component,
            process_runs=0, valid_runs=0, failed_runs=0, kernel_recorded_s=0.0,
            process_recorded_s=0.0, unknown_kernel_runs=0, unknown_process_runs=0))
        target["process_runs"] += row["spawned"]
        target["valid_runs"] += row["valid"]
        target["failed_runs"] += not row["valid"]
        for field, total, missing in (("kernel_s", "kernel_recorded_s", "unknown_kernel_runs"),
                                      ("process_wall_s", "process_recorded_s", "unknown_process_runs")):
            if finite_positive(row.get(field)):
                target[total] += row[field]
            else:
                target[missing] += 1
    builds = []
    for batch in batches:
        for task in batch["tasks"]:
            rows = [row for row in task["records"] if row["type"] == "build"]
            if not rows:
                continue
            builds.append(dict(stage=batch["manifest"]["stage"], task=task["job"]["id"], role=task["job"]["role"],
                actual_compile_processes=sum(row["type"] == "build_start" for row in task["records"]),
                cached_build_checks=sum(row["cached"] for row in rows),
                compile_recorded_s=sum(row["compile_wall_s"] for row in rows),
                incomplete_builds=task["summary"].get("incomplete_builds") if task["summary"] else None))
    return list(grouped.values()), builds


def clock_table(directory, protocol):
    """Recompute completed diagnostic clocks; no timer is presumed absolutely accurate."""
    directory = Path(directory)
    identity = load_json(directory / "identity.json")
    if identity["source_sha256"] != protocol["target"]["sha256"] or \
            identity["compiler"] != protocol["target"]["compiler_identity"]:
        raise ValueError("clock diagnostic source/compiler differs from the frozen target")
    rows = []
    for path in sorted(directory.glob("*.stdout.txt")):
        texts = path.read_text().splitlines()
        records = [json.loads(line) for line in texts if line.startswith("{")]
        intervals = [row for row in records if "start_ns" in row]
        if not intervals:
            continue
        if len(intervals) != 1:
            raise ValueError("one completed clock task must contain exactly one interval")
        record = intervals[0]
        if record["clock_order"] != ["MONOTONIC", "RAW", "REALTIME", "PROCESS_CPU"] or \
                any(type(value) is not int for value in [*record["start_ns"], *record["end_ns"]]):
            raise ValueError("unknown clock reading order or nanosecond boundaries")
        spans = [(end - start) / 1e9 for start, end in zip(record["start_ns"], record["end_ns"])]
        if len(spans) != 4 or len(record["elapsed_s"]) != 4 or any(not finite_positive(value) for value in spans) or \
                any(not math.isclose(value, printed, rel_tol=0, abs_tol=5e-10)
                    for value, printed in zip(spans, record["elapsed_s"])):
            raise ValueError("clock diagnostic elapsed fields differ from raw nanoseconds")
        cpu = spans[3]
        row = dict(task=path.stem, role="clock_probe" if "mode" in record else "clock_matrix_diagnostic",
            raw_sha256=sha256(path), mode=record.get("mode", "matrix_kernel"),
            iterations=record.get("iterations"), requested_idle_seconds=record.get("requested_idle_seconds"),
            start_ns=record["start_ns"], end_ns=record["end_ns"],
            monotonic_s=spans[0], raw_s=spans[1], realtime_s=spans[2], process_cpu_s=cpu,
            raw_over_monotonic=spans[1] / spans[0], realtime_over_monotonic=spans[2] / spans[0],
            cpu_over_raw=cpu / spans[1], absolute_clock_accuracy_verified=False)
        query = next((value for value in records if value.get("adjtimex_readonly")), None)
        if query:
            unit = "ns" if query["status"] & 0x2000 else "us"
            if query["offset_unit"] != unit:
                raise ValueError("adjtimex offset unit differs from its STA_NANO flag")
            row["adjtimex"] = query
        if record.get("mode") == "overhead":
            row["mean_four_clock_tuple_ns_including_loop"] = spans[0] * 1e9 / record["iterations"]
        if "mode" not in record:
            printed = ex.at.TargetProgram.parse(path.read_text())
            float32 = struct.unpack("f", struct.pack("f", spans[0]))[0]
            if printed != float(f"{float32:.6f}"):
                raise ValueError("matrix float tdiff/six-decimal output differs from its MONOTONIC boundaries")
            row.update(kernel_output_s=printed, output_minus_boundary_s=printed - spans[0],
                       cpu_interval="kernel only; separate from whole-target CHILDREN CPU time")
        rows.append(row)
    return dict(identity_sha256=sha256(directory / "identity.json"), identity=identity, intervals=rows,
                populations_or_absolute_accuracy_inferred=False)


def write_csv(path, rows):
    if any(isinstance(value, float) and not math.isfinite(value) for row in rows for value in row.values()):
        raise ValueError("nonfinite derived scalar cannot enter a result table")
    fields = list(dict.fromkeys(name for row in rows for name in row))
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({name: json.dumps(value, ensure_ascii=False, allow_nan=False) if isinstance(value, (list, dict))
                         else value for name, value in row.items()} for row in rows)


def safe_destination(destination, batches):
    target = Path(destination).resolve()
    for batch in batches:
        raw = batch["path"].resolve()
        if target == raw or raw in target.parents:
            raise ValueError("derived output cannot overwrite or nest inside a raw batch")
    if any((parent / "plan.json").is_file() for parent in [target, *target.parents]):
        raise ValueError("derived output cannot enter another frozen raw batch")
    return target


def plot_results(directory, samples, grid, runs, curves, aa, pairs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    created = []

    def save(fig, name):
        fig.tight_layout()
        path = directory / name
        fig.savefig(path, dpi=170)
        plt.close(fig)
        created.append(dict(path=str(path), sha256=sha256(path)))

    if grid and all(row["median_s"] is not None for row in grid):
        blocks = sorted({row["s"] for row in grid})
        fig, ax = plt.subplots(figsize=(10, 4.8))
        for offset, opt in enumerate(("O0", "O1", "O2", "O3")):
            selected = [next(row for row in grid if row["s"] == s and row["opt"] == opt) for s in blocks]
            positions = [index + (offset - 1.5) * .19 for index in range(len(blocks))]
            ax.bar(positions, [row["median_s"] for row in selected], width=.18, label=opt)
            ax.errorbar(positions, [row["median_s"] for row in selected], fmt="none", color="black", capsize=2,
                yerr=[[row["median_s"] - row["min_s"] for row in selected],
                      [row["max_s"] - row["median_s"] for row in selected]])
        ax.set_xticks(range(len(blocks)), blocks)
        ax.set(xlabel="Block size s", ylabel="Kernel time (s, logarithmic scale)", yscale="log",
               title="20 configurations: median and observed range, three runs each")
        ax.legend(ncol=4)
        save(fig, "grid_goal2.png")

    main_runs = [row for row in runs if row["stage"] == "comparison" and row["algorithm"] in ("grid", "random", "greedy")]
    if main_runs:
        seeds = sorted({row["seed"] for row in main_runs})
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.7))
        for name, marker in (("grid", "s"), ("random", "o"), ("greedy", "^")):
            rows = sorted((row for row in main_runs if row["algorithm"] == name), key=lambda row: row["seed"])
            x = [seeds.index(row["seed"]) + 1 for row in rows]
            axes[0].plot(x, [row["gap_ref_pct"] for row in rows], marker=marker, label=name.capitalize())
            axes[1].plot(x, [row["search_driver_wall_s"] for row in rows], marker=marker, label=name.capitalize())
        axes[0].axhline(5, color="gray", linestyle="--", linewidth=1, label="5% target")
        axes[0].set(xlabel="Independent search block", ylabel="Returned configuration gap (%)",
                    title="Quality evaluated with one common reference table")
        axes[1].set(xlabel="Independent search block", ylabel="Actual search driver time (s)",
                    title="Search cost, including compilation and all probes")
        for ax in axes:
            ax.set_xticks(range(1, len(seeds) + 1))
            ax.legend()
            ax.grid(alpha=.2)
        save(fig, "algorithms_goal2.png")

    if aa:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.7))
        for ax, tier in zip(axes, ("F", "M")):
            for method in ("M0", "M1"):
                rows = [row for row in samples if row["role"] == "aa" and row["tier"] == tier and row["method"] == method]
                for label, marker in (("A", "o"), ("B", "x")):
                    selected = sorted((row for row in rows if row["label"] == label), key=lambda row: row["pair"])
                    ax.plot([row["pair"] for row in selected], [row["kernel_s"] for row in selected],
                            marker=marker, label=f"{method}-{label}")
            config = next(row for row in samples if row["role"] == "aa" and row["tier"] == tier)
            ax.set(title=f"Same binary: s{config['s']}/{config['opt']}", xlabel="Predefined A/A pair", ylabel="Kernel time (s)")
            ax.set_xticks([1, 2, 3])
            ax.legend(ncol=2)
            ax.grid(alpha=.2)
        save(fig, "aa_goal2.png")

    if pairs:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.7))
        x = list(range(1, len(pairs) + 1))
        axes[0].bar(x, [row["gain_ref_pp"] for row in pairs], color="#3c78a8")
        axes[0].axhline(0, color="black", linewidth=.8)
        axes[0].set(xlabel="Paired search block", ylabel="Random gap minus S3 gap (percentage points)",
                    title="Configuration choice: common reference table")
        axes[1].bar(x, [100 * row["wall_saving_fraction"] for row in pairs], color="#527d4d")
        axes[1].axhline(10, color="gray", linestyle="--", linewidth=1)
        axes[1].axhline(0, color="black", linewidth=.8)
        axes[1].set(xlabel="Paired search block", ylabel="Actual search time saving (%)",
                    title="One factor: six explorations and two candidate rechecks")
        for ax in axes:
            ax.set_xticks(x)
            ax.grid(axis="y", alpha=.2)
        save(fig, "recheck_goal2.png")

    if curves:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.7))
        colors = dict(grid="#377eb8", random="#4daf4a", greedy="#e41a1c", recheck="#984ea3")
        for name, color in colors.items():
            selected = [row for row in curves if row["stage"] == "comparison" and row["algorithm"] == name and
                        row["best_so_far_s"] is not None]
            for index, seed in enumerate(sorted({row["seed"] for row in selected})):
                rows = [row for row in selected if row["seed"] == seed]
                for ax, key in ((axes[0], "actual_calls"), (axes[1], "tuning_elapsed_s")):
                    ax.plot([row[key] for row in rows], [row["best_so_far_s"] for row in rows], color=color,
                            alpha=.5, marker=".", linestyle="--" if name == "recheck" else "-",
                            label="S3 updated estimate" if name == "recheck" and index == 0 else
                                  name.capitalize() if index == 0 else None)
                    rechecks = [row for row in rows if row["phase"] == "recheck"]
                    if rechecks:
                        ax.scatter([row[key] for row in rechecks], [row["best_so_far_s"] for row in rechecks],
                                   color=color, marker="^", s=22,
                                   label="S3 successful-finalist phase" if index == 0 else None)
        axes[0].set(xlabel="Actual target calls used", ylabel="Online best estimate (s)", yscale="log")
        axes[1].set(xlabel="Recorded tuning elapsed time (s)", ylabel="Online best estimate (s)", yscale="log")
        for ax in axes:
            ax.legend()
            ax.grid(alpha=.2)
        fig.suptitle("S3 first explores, then updates eligible finalists; its estimate may rise", fontsize=10)
        save(fig, "progress_goal2.png")
    return created


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--runs", action="append", type=Path, default=[])
    parser.add_argument("--diagnostic", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--clocks", type=Path)
    parser.add_argument("--plots", action="store_true")
    parser.add_argument("--image-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    protocol = load_json(args.protocol)
    directories = ([args.reference] if args.reference else []) + args.runs + ([args.diagnostic] if args.diagnostic else [])
    if len({path.resolve() for path in directories}) != len(directories):
        raise ValueError("duplicate batches cannot be counted as new evidence")
    batches = [read_batch(path, args.protocol, args.reference) for path in directories]
    raw_inputs = batches + ([dict(path=args.clocks)] if args.clocks else [])
    output = safe_destination(args.output_dir, raw_inputs)
    output.mkdir(parents=True, exist_ok=True)
    samples = samples_from_batches(batches)
    summary = dict(schema=2, protocol_sha256=sha256(args.protocol), analysis_sha256=sha256(__file__),
        batch_manifest_sha256={batch["path"].name: sha256(batch["path"] / "plan.json") for batch in batches})
    summary["tasks"] = [dict(stage=batch["manifest"]["stage"], id=task["job"]["id"], role=task["job"]["role"],
        state=task["state"], actual_process_starts=sum(row["type"] == "measurement_start" for row in task["records"]),
        valid_measurements=sum(row["task"] == task["job"]["id"] and row["stage"] == batch["manifest"]["stage"] and row["valid"]
                               for row in samples),
        interrupted_measurements=sum(row["type"] == "measurement" and row["status"] == "interrupted" for row in task["records"]))
        for batch in batches for task in batch["tasks"]]
    write_csv(output / "measurements.csv", samples)
    costs = cost_table(batches, read_records(args.ledger) if args.ledger else None)
    write_csv(output / "batch_costs.csv", costs["rows"])
    summary["costs"] = costs
    if args.clocks:
        summary["clocks"] = clock_table(args.clocks, protocol)
        write_csv(output / "clock_summary.csv", summary["clocks"]["intervals"])
    process_costs, build_costs = component_costs(batches, samples)
    write_csv(output / "process_costs.csv", process_costs)
    write_csv(output / "build_costs.csv", build_costs)
    aa, grid, runs, curves, pairs = [], [], [], [], []
    if args.diagnostic:
        aa = aa_table(samples, require_complete=False)
        summary["aa"], summary["arrangement"] = aa, choose_arrangement(aa, samples)
        write_csv(output / "aa_summary.csv", aa)
    if args.reference:
        grid, complete = reference_table(samples, protocol)
        summary["reference_complete"] = complete
        write_csv(output / "grid_summary.csv", grid)
        panels = panel_table(samples, batches)
        write_csv(output / "panel_summary.csv", panels)
        runs, curves = search_tables(batches, grid, panels, protocol)
        write_csv(output / "search_summary.csv", runs)
        write_csv(output / "online_curves.csv", curves)
        decisions = {}
        for stage, count in (("comparison", len(protocol["online"]["seeds"])),
                             ("confirmation", len(protocol["holdout"]["seeds"]))):
            stage_pairs = paired_rows(runs, grid, panels, protocol, stage) if complete else []
            write_csv(output / (stage + "_paired.csv"), stage_pairs)
            if stage == "comparison":
                pairs = stage_pairs
            decisions[stage] = decision(stage_pairs, protocol, count, costs["complete"] and args.ledger is not None)
        if decisions["comparison"]["decision"] != "KEEP" and not any(row["stage"] == "confirmation" and
                row["algorithm"] == "recheck" for row in runs):
            decisions["confirmation"] = dict(decision="NOT_REQUIRED", reasons=["S3 was not selected; baseline confirmation is reported separately"])
        summary["decisions"] = decisions
        summary["retention"] = final_retention(decisions["comparison"], decisions["confirmation"])
        baseline = [row for row in runs if row["stage"] == "confirmation" and row["algorithm"] == "random"]
        summary["baseline_confirmation"] = dict(expected_seeds=protocol["holdout"]["seeds"],
            observed_seeds=[row["seed"] for row in baseline],
            complete=sorted(row["seed"] for row in baseline if row["state"] == "complete") == sorted(protocol["holdout"]["seeds"]),
            quality_classes=[row["quality_class"] for row in baseline])
    if args.plots:
        image_dir = safe_destination(args.image_dir or output / "images", raw_inputs)
        summary["images"] = plot_results(image_dir, samples, grid, runs, curves, aa, pairs)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(output=str(output), **costs["totals"], costs_complete=costs["complete"]), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
