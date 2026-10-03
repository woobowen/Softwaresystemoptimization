#!/usr/bin/env python3
"""Independently read the saved Goal 2R inputs; never launch or alter experiments."""

import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import time
import csv

P1 = Path(__file__).resolve().parents[1]
RAW = "CLOCK_MONOTONIC_RAW"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def close(left, right, tolerance=1e-10):
    assert math.isfinite(left) and math.isfinite(right) and abs(left - right) <= tolerance, (left, right)


def table(name):
    with (P1 / "results/goal2r_summary" / (name + ".csv")).open(newline="") as stream:
        return list(csv.DictReader(stream))


def journal(path, protocol, expected_source=None):
    rows = records(path)
    assert rows[0]["type"] == "header" and rows[-1]["type"] == "summary", path
    metadata = rows[0]["metadata"]
    assert rows[0]["fingerprint"] == fingerprint(metadata), path
    assert metadata["framework_sha256"] == protocol["framework"]["sha256"]
    assert metadata["target"]["n"] == 4096 and metadata["primary_clock"] == RAW
    assert metadata["target"]["compiler"] == protocol["target"]["compiler_identity"]
    if expected_source:
        assert metadata["target"]["source_sha256"] == expected_source
    starts = {(r["trial_id"], r["repeat"]): r for r in rows if r["type"] == "measurement_start"}
    measured = [r for r in rows if r["type"] == "measurement"]
    assert len(starts) == sum(r["type"] == "measurement_start" for r in rows) == len(measured)
    assert len(measured) == rows[-1]["process_runs"]
    assert len({(r["pid"], r["clock_start_ns"][RAW]) for r in measured}) == len(measured)
    builds = {r["trial_id"]: r for r in rows if r["type"] == "build"}
    for row in measured:
        start, build = starts[row["trial_id"], row["repeat"]], builds[row["trial_id"]]
        assert all(start[k] == row[k] for k in ("command", "config", "pid", "started_at", "spawned"))
        assert row["spawned"] and row["returncode"] == 0 and row["status"] == row["timing_status"] == "ok"
        assert row["command"] == [build["binary"], str(row["config"]["s"])]
        assert row["binary_sha256"] == build["binary_sha256"] and row["build_key"] == build["build_key"]
        identity = {k: metadata["target"][k] for k in ("source", "source_sha256", "compiler")}
        identity["flags"] = [*metadata["target"]["flags"], "-" + row["config"]["opt"]]
        assert build["build_key"] == fingerprint(identity) and build["flags"] == identity["flags"]
        assert build["source_sha256"] == metadata["target"]["source_sha256"] and build["status"] == "ok"
        lines = row["stdout"].splitlines()
        close(float(lines[0]), row["kernel_s"])
        pairs = dict(line.split("=", 1) for line in lines[1:] if "=" in line and not line.startswith("verify"))
        assert int(pairs["kernel_start_ns"]) == row["kernel_start_ns"]
        assert int(pairs["kernel_end_ns"]) == row["kernel_end_ns"]
        close(float(pairs["checksum"]), row["checksum"])
        a, b = row["clock_start_ns"][RAW], row["clock_end_ns"][RAW]
        assert type(a) is int and type(b) is int and a <= row["kernel_start_ns"] < row["kernel_end_ns"] <= b
        close((b - a) / 1e9, row["process_raw_s"])
        close(row["process_raw_s"], row["clock_deltas_s"][RAW])
        close((row["kernel_end_ns"] - row["kernel_start_ns"]) / 1e9, row["kernel_s"], .500001e-6)
        assert row["process_raw_s"] > 0 and row["kernel_s"] > 0
    sessions = [r for r in rows if r["type"] == "session_end"]
    assert len(sessions) == 1 and sessions[0]["raw_end_ns"] > sessions[0]["raw_start_ns"]
    close((sessions[0]["raw_end_ns"] - sessions[0]["raw_start_ns"]) / 1e9, sessions[0]["raw_s"])
    return rows, measured, metadata


def trace(rows, metadata):
    """Replay only the recorded successful feedback, without importing the tuner."""
    configs = [(s, o) for s in metadata["blocks"] for o in metadata["opts"]]
    trials = [r for r in rows if r["type"] == "trial"]
    order = list(configs)
    algorithm = metadata["algorithm"]
    rng = random.Random(metadata["seed"])
    if algorithm in ("random", "recheck"):
        rng.shuffle(order)
    current = tuple(metadata["greedy_start"][k] for k in ("s", "opt")) if "greedy_start" in metadata else rng.choice(configs)
    scores, samples, finalists, rechecked = {}, defaultdict(list), [], []
    measured = {(r["trial_id"], r["repeat"]): r["kernel_s"] for r in rows if r["type"] == "measurement"}
    for index, row in enumerate(trials):
        config = row["config"]["s"], row["config"]["opt"]
        if algorithm in ("grid", "random"):
            proposed = order[index]
        elif algorithm == "recheck":
            proposed = order[index] if index < 6 else finalists[index - 6]
        else:
            while current in scores:
                si, oi = metadata["blocks"].index(current[0]), metadata["opts"].index(current[1])
                neighbors = [c for c in configs if c != current and
                    ((c[1] == current[1] and abs(metadata["blocks"].index(c[0]) - si) <= 1) or
                     (c[0] == current[0] and abs(metadata["opts"].index(c[1]) - oi) <= 1))]
                pending = [c for c in neighbors if c not in scores]
                if pending:
                    break
                winner = min([current, *neighbors], key=scores.__getitem__)
                assert scores[winner] < scores[current], "trace continued after local optimum"
                current = winner
            proposed = pending[0] if current in scores else current
        assert config == proposed and row["trial_id"] == index
        fresh = statistics.median(measured[index, r] for r in range(metadata["repeats"]))
        samples[config].append(fresh)
        scores[config] = statistics.median(samples[config])
        close(row["score"], scores[config])
        if algorithm == "recheck" and index == 5:
            finalists = sorted(order[:6], key=scores.__getitem__)[:2]
        if algorithm == "recheck" and index >= 6:
            rechecked.append(config)
        candidates = [c for c in order if c in scores and (not rechecked or c in rechecked)]
        # Ordinary algorithms keep the first observed tie; recheck uses random visit order.
        winner = min(candidates if algorithm == "recheck" else list(scores), key=scores.__getitem__)
        assert row["best_so_far"]["config"] == dict(s=winner[0], opt=winner[1])
        close(row["best_so_far"]["score"], scores[winner])
    assert rows[-1]["best"] == trials[-1]["best_so_far"]
    if algorithm == "recheck":
        assert len(trials) == 8 and len(scores) == 6 and len(rechecked) == 2
        assert rows[-1]["distinct_configs"] == 6 and rows[-1]["recheck_trials"] == 2


def qpc(path, start, end):
    data = load(path)
    assert data["complete"] and data["lifecycle_valid"] and data["bridge_exit_code"] == 0
    assert len(data["handshake"]) == 5 and data["host_frequency_hz"] > 0
    readings = data["readings"]
    assert [r["sequence"] for r in readings] == list(range(len(readings)))
    for r in readings:
        assert r["is_high_resolution"] and r["frequency_hz"] == data["host_frequency_hz"]
        assert r["host_pid"] == data["host_pid"] and r["host_managed_thread_id"] == data["host_managed_thread_id"]
        assert r["request"] == f"sample:{r['sequence']}"
        assert r["response"] == f"sample:{r['sequence']}:{r['host_tick']}:{r['frequency_hz']}:True:{r['host_pid']}:{r['host_managed_thread_id']}"
        assert start["clock_start_ns"]["raw"] <= r["before_ns"]["RAW"] <= r["after_ns"]["RAW"] <= end["clock_end_ns"]["raw"]
    result = []
    for interval in data["intervals"]:
        a, b, frequency = interval["first"], interval["last"], data["host_frequency_hz"]
        assert a in readings and b in readings and interval["returncode"] == 0
        ticks = b["host_tick"] - a["host_tick"]
        low = (b["before_ns"]["RAW"] - a["after_ns"]["RAW"]) / 1e9
        high = (b["after_ns"]["RAW"] - a["before_ns"]["RAW"]) / 1e9
        ratio = [low / ((ticks + 2) / frequency), high / ((ticks - 2) / frequency)]
        widths = [(r["after_ns"]["RAW"] - r["before_ns"]["RAW"]) / 1e9 for r in (a, b)]
        width_fraction = (high - low) / (ticks / frequency)
        assert low > 0 and ticks > 2 and max(widths) <= .02 and width_fraction <= .002
        assert .995 <= ratio[0] <= ratio[1] <= 1.005
        saved = interval["linux_interval_bounds"]["RAW"]
        for computed, observed in zip(ratio, saved["linux_to_host_ratio_bounds"]):
            close(computed, observed)
        close(width_fraction, saved["bracket_width_fraction"])
        result.append(dict(path=str(path.relative_to(P1)), ratio=ratio, endpoint_s=widths, width_fraction=width_fraction))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.resolve().relative_to((P1 / "evidence/finalization").resolve())
    begin = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    protocol_path = P1 / "evidence/protocol_goal2r.json"
    protocol, protocol_sha = load(protocol_path), sha(protocol_path)
    for binding in [protocol["framework"], protocol["target"], *protocol["execution"].values()]:
        assert sha(P1 / binding["path"]) == binding["sha256"], binding["path"]
    ledger_path = P1 / "evidence/measurement/resource_ledger.jsonl"
    ledger = records(ledger_path)
    starts = {r["attempt_id"]: r for r in ledger if r["type"] == "task_start"}
    ends = {r["attempt_id"]: r for r in ledger if r["type"] == "task_end"}
    assert len(starts) == sum(r["type"] == "task_start" for r in ledger) == len(ends)
    assert starts.keys() == ends.keys()
    for key, row in ends.items():
        assert row.get("n4096_calls_known", True) and row["resource_s"] > 0
        if "raw" in starts[key]["clock_start_ns"] and row.get("resource_clock") == RAW:
            close((row["clock_end_ns"]["raw"] - starts[key]["clock_start_ns"]["raw"]) / 1e9, row["resource_s"])
    by_journal = {r.get("journal"): (r, ends[r["attempt_id"]]) for r in starts.values() if r.get("journal")}
    observed, searches, panels, checks = [], [], [], []
    for stage in ("reference", "comparison", "starts", "confirmation"):
        directory = P1 / "results" / ("goal2r_" + stage)
        plan = load(directory / "plan.json")
        assert plan["protocol_sha256"] == protocol_sha
        for key, expected in (("target_sha256", protocol["target"]["sha256"]),
                              ("framework_sha256", protocol["framework"]["sha256"]),
                              ("driver_sha256", protocol["execution"]["driver"]["sha256"])):
            assert plan[key] == expected
        if stage == "reference":
            canonical = [(s, o) for s in protocol["space"]["blocks"] for o in protocol["space"]["opts"]]
            for round_id in (1, 2, 3):
                order = list(canonical)
                random.Random(protocol["reference"]["order_seed"] + round_id - 1).shuffle(order)
                assert [(j["config"]["s"], j["config"]["opt"]) for j in plan["jobs"] if j["role"] == "reference" and j["round"] == round_id] == order
        if stage == "comparison":
            assert [[j["algorithm"] for j in plan["jobs"] if j.get("block") == b and j["action"] == "search"] for b in range(1, 7)] == protocol["online"]["orders"]
        jobs = []
        for job in plan["jobs"]:
            if job["action"] != "panel":
                jobs.append(job)
            else:
                panel = load(directory / (job["id"] + ".json"))
                assert panel["reference_config"] == dict(s=128, opt="O3")
                assert panel["protocol_sha256"] == protocol_sha
                assert panel["reference_manifest_sha256"] == sha(P1 / "results/goal2r_reference/plan.json")
                assert panel["fingerprint"] == fingerprint({k:v for k,v in panel.items() if k != "fingerprint"})
                required = {(128, "O3")}
                dependency_ends = []
                for dep in job["depends_on"]:
                    path = directory / (dep + ".jsonl")
                    assert panel["dependencies_sha256"][dep] == sha(path)
                    result = records(path)[-1]
                    if "-random-" in dep or "-recheck-" in dep:
                        required.add((result["best"]["config"]["s"], result["best"]["config"]["opt"]))
                    dependency_ends.append(by_journal[str(path.relative_to(P1))][1]["clock_end_ns"]["raw"])
                assert {(c["s"], c["opt"]) for c in panel["configs"]} == required
                expected_order = []
                for round_id in (1, 2, 3):
                    order = sorted(required)
                    random.Random(protocol["return_confirmation"]["order_seed"] + 100 * job["block"] + round_id).shuffle(order)
                    expected_order.extend((round_id, s, opt) for s, opt in order)
                assert [(j["round"], j["config"]["s"], j["config"]["opt"]) for j in panel["jobs"]] == expected_order
                for j in panel["jobs"]:
                    a, _ = by_journal[str((directory / (j["id"] + ".jsonl")).relative_to(P1))]
                    assert a["clock_start_ns"]["raw"] > max(dependency_ends)
                panels.append(dict(stage=stage, seed=job["seed"], calls=len(panel["jobs"]), identities=len(required)))
                jobs.extend(panel["jobs"])
        local_driver = records(directory / "driver.jsonl")
        assert len(local_driver) == len({r["attempt_id"] for r in local_driver}) == len(jobs)
        for row in local_driver:
            assert all(v == ends[row["attempt_id"]].get(k) for k, v in row.items() if k not in ("type", "at"))
        block_states = {}
        for check in records(directory / "block_checks.jsonl"):
            a, b = starts[check["attempt_id"]], ends[check["attempt_id"]]
            assert check["protocol_sha256"] == protocol_sha and check["boot_id"] == a["boot_id"]
            path = P1 / check["raw_path"]
            assert sha(path) == check["sha256"] and check["valid"] is True
            checks.extend(qpc(path, a, b))
            assert (check["block_id"], check["phase"]) not in block_states and check["phase"] in ("before", "after")
            block_states[check["block_id"], check["phase"]] = (a, b)
        for job in jobs:
            path = directory / (job["id"] + ".jsonl")
            rows, measured, metadata = journal(path, protocol, protocol["target"]["sha256"])
            assert metadata["protocol_sha256"] == protocol_sha and metadata["action"] == job["action"]
            assert metadata["algorithm"] == job.get("algorithm", "grid") and metadata["seed"] == job.get("seed", 0)
            assert metadata["budget"] == job.get("budget", 1) and metadata["repeats"] == job["repeats"]
            assert metadata["runtime_affinity"] == [0] and metadata["target"]["flags"] == protocol["target"]["common_flags"]
            assert metadata["target"]["source"] == str(Path(plan["measurement_root"]) / protocol["target"]["path"])
            assert metadata["blocks"] == ([job["config"]["s"]] if "config" in job else protocol["space"]["blocks"])
            assert metadata["opts"] == ([job["config"]["opt"]] if "config" in job else protocol["space"]["opts"])
            a, b = by_journal[str(path.relative_to(P1))]
            assert b["returncode"] == 0 and b["reason"] is None and b["n4096_calls"] == len(measured)
            assert a["journal"] == str(path.relative_to(P1)) and "--output" in a["command"]
            assert a["command"][a["command"].index("--output") + 1] == str(path)
            for option, value in (("--target", metadata["target"]["source"]), ("--seed", metadata["seed"]),
                                  ("--mode", "benchmark"), ("--cache-dir", metadata["cache_dir"]),
                                  ("--repeats", metadata["repeats"]), ("--timeout", protocol["measurement"]["timeout_s"])):
                assert a["command"][a["command"].index(option) + 1] == str(value)
            if job["action"] == "search":
                assert a["command"][a["command"].index("--algorithm") + 1] == job["algorithm"]
                assert a["command"][a["command"].index("--budget") + 1] == str(job["budget"])
            else:
                assert a["command"][a["command"].index("--s") + 1] == str(job["config"]["s"])
                assert a["command"][a["command"].index("--opt") + 1] == job["config"]["opt"]
            output = load(P1 / b["stdout"])
            assert output == dict(rows[-1], output=str(path))
            block = f"round-{job['round']}" if stage == "reference" and job.get("round") else \
                    job["id"] if stage == "starts" else f"seed-{job['seed']}" if stage != "reference" else None
            if block:
                before, after = block_states[block, "before"], block_states[block, "after"]
                assert before[0]["boot_id"] == a["boot_id"] == after[0]["boot_id"]
                assert before[1]["clock_end_ns"]["raw"] <= a["clock_start_ns"]["raw"] <= b["clock_end_ns"]["raw"] <= after[0]["clock_start_ns"]["raw"]
            for r in measured:
                assert a["clock_start_ns"]["raw"] <= r["clock_start_ns"][RAW] < r["clock_end_ns"][RAW] <= b["clock_end_ns"]["raw"]
                observed.append(dict(stage=stage, task=job["id"], role=job["role"], round=job.get("round"),
                                     seed=job.get("seed"), config=(r["config"]["s"], r["config"]["opt"]), seconds=r["kernel_s"]))
            if job["action"] == "search":
                trace(rows, metadata)
                searches.append(dict(stage=stage, job=job, rows=rows, metadata=metadata, driver=b))
    counts = Counter((r["stage"], r["role"]) for r in observed)
    assert counts == Counter({("reference", "reference"):60, ("reference", "warmup"):1,
        ("reference", "anchor"):3, ("comparison", "search"):189, ("comparison", "shared_confirmation"):48,
        ("starts", "start_panel"):28, ("confirmation", "search"):24, ("confirmation", "shared_confirmation"):15})
    assert len(observed) == 368 and len(searches) == 31
    grid = []
    for saved in table("grid_summary"):
        config = int(saved["s"]), saved["opt"]
        samples = [r["seconds"] for r in observed if r["role"] == "reference" and r["config"] == config]
        assert len(samples) == 3 and samples == json.loads(saved["samples"])
        median = statistics.median(samples)
        mad = statistics.median(abs(v - median) for v in samples)
        close(median, float(saved["median_s"])); close(mad, float(saved["mad_s"]))
        close(min(samples), float(saved["min_s"])); close(max(samples), float(saved["max_s"]))
        assert json.loads(saved["rounds"]) == [1, 2, 3] and int(saved["valid_runs"]) == 3 and int(saved["failed_runs"]) == 0
        grid.append(dict(s=config[0], opt=config[1], samples=samples, median_s=median, mad_s=mad))
    assert len(grid) == 20
    reference = {(r["s"], r["opt"]):r["median_s"] for r in grid}
    best = min(reference.values())
    saved_searches = table("search_summary")
    curves = table("online_curves")
    for search, saved in zip(searches, saved_searches):
        job, result = search["job"], search["rows"][-1]
        assert saved["journal"] == str((P1 / "results" / ("goal2r_" + search["stage"]) / (job["id"] + ".jsonl")).relative_to(P1))
        config = result["best"]["config"]["s"], result["best"]["config"]["opt"]
        assert config == (int(saved["returned_s"]), saved["returned_opt"]) and saved["valid"] == "True" and saved["state"] == "complete"
        close(result["best"]["score"], float(saved["online_score_s"]))
        close(search["driver"]["driver_raw_s"], float(saved["search_driver_raw_s"]))
        close(100 * (reference[config] / best - 1), float(saved["gap_ref_pct"]))
        assert int(saved["process_runs"]) == result["process_runs"] and int(saved["distinct_configs"]) == result["distinct_configs"]
        for row in [r for r in search["rows"] if r["type"] == "trial"]:
            matches = [c for c in curves if c["stage"] == search["stage"] and int(c["seed"]) == job["seed"] and c["algorithm"] == job["algorithm"] and int(c["step"]) == row["trial_id"] + 1]
            # Fixed start searches use the same seed; their curves are distinguished by order.
            match = matches.pop(0)
            curves.remove(match)
            close(float(match["best_so_far_s"]), row["best_so_far"]["score"])
            close(float(match["tuning_raw_elapsed_s"]), row["tuning_raw_elapsed_s"])
            assert int(match["actual_calls"]) == row["trial_id"] + 1
    assert not curves
    pairs = []
    for saved in table("comparison_paired"):
        seed = int(saved["seed"])
        selections = [next(s for s in searches if s["stage"] == "comparison" and s["job"]["seed"] == seed and s["job"]["algorithm"] == alg) for alg in ("random", "recheck")]
        selected = [(s["rows"][-1]["best"]["config"]["s"], s["rows"][-1]["best"]["config"]["opt"]) for s in selections]
        gains = []
        for round_id in (1, 2, 3):
            times = [next(r["seconds"] for r in observed if r["stage"] == "comparison" and r["role"] == "shared_confirmation" and r["seed"] == seed and r["round"] == round_id and r["config"] == c) for c in [*selected, (128, "O3")]]
            gains.append(0.0 if selected[0] == selected[1] else 100 * (times[0] - times[1]) / times[2])
        for a, b in zip(gains, json.loads(saved["gain_panel_rounds_pp"])):
            close(a, b)
        saving = 1 - selections[1]["driver"]["driver_raw_s"] / selections[0]["driver"]["driver_raw_s"]
        close(saving, float(saved["cost_saving_fraction"]))
        close(statistics.median(gains), float(saved["gain_panel_pp"]))
        close(min(gains), float(saved["gain_panel_low_pp"])); close(max(gains), float(saved["gain_panel_high_pp"]))
        pairs.append(dict(seed=seed, gains_pp=gains, cost_saving_fraction=saving))
    rejected = [i + 1 for i, p in enumerate(pairs) if max(p["gains_pp"]) < -2]
    severe = [i + 1 for i, p in enumerate(pairs) if max(p["gains_pp"]) < -10]
    assert rejected == [1, 4, 6] and severe == [4, 6]
    summary = load(P1 / "results/goal2r_summary/summary.json")
    close(statistics.median(p["cost_saving_fraction"] for p in pairs), summary["decisions"]["comparison"]["median_cost_saving_fraction"])
    assert summary["decisions"]["comparison"]["decision"] == "REJECT" and summary["decisions"]["confirmation"]["decision"] == "NOT_REQUIRED"
    assert summary["retention"]["retained"] is False and summary["baseline_confirmation"]["complete"] is True
    assert not table("confirmation_paired") and summary["additional_confirmation"]["selected_seeds"] == []
    extras = []
    for a in starts.values():
        b = ends[a["attempt_id"]]
        if a["role"] in ("goal2r_clock_aa", "goal2r_clock_diagnostic", "goal2r_numeric", "goal2r_final_target") and b["n4096_calls"]:
            _, measured, _ = journal(P1 / a["journal"], protocol)
            assert len(measured) == b["n4096_calls"] == 1
            extras.append(dict(role=a["role"], journal=a["journal"], kernel_s=measured[0]["kernel_s"]))
            if a["role"] == "goal2r_clock_diagnostic":
                checks.extend(qpc(P1 / b["stdout"], a, b))
    for check in records(P1 / "evidence/reproduction/goal2r/block_checks.jsonl"):
        assert sha(P1 / check["raw_path"]) == check["sha256"] and check["valid"] is True
        checks.extend(qpc(P1 / check["raw_path"], starts[check["attempt_id"]], ends[check["attempt_id"]]))
    assert len(extras) == 13 and len(checks) == 40
    costs = load(P1 / "evidence/measurement/goal2r_costs.json")
    prefix = ledger_path.read_bytes().splitlines(keepends=True)[:costs["ledger"]["old_prefix_rows"]]
    assert hashlib.sha256(b"".join(prefix)).hexdigest() == costs["ledger"]["old_prefix_sha256"]
    old_ends = [r for r in ledger[:len(prefix)] if r["type"] == "task_end"]
    assert sum(r["n4096_calls"] for r in old_ends) == 48 and sum(r["n4096_calls"] for r in ends.values()) == 429
    close(sum(r["resource_s"] for r in old_ends), 3713.432874365)
    assert sum(Decimal(str(r["resource_s"])) for r in ends.values()) == Decimal(costs["primary_resource_s"]["cumulative"])
    actor_cost = Decimal(0)
    for actor in costs["separate_actor_costs"]:
        path = P1 / actor["path"]
        assert sha(path) == actor["sha256"]
        values = records(path)
        excluded = actor["unknown_or_annotation_rows_excluded_from_known_sum"]
        known = Decimal(0)
        for index, row in enumerate(values, 1):
            assert row.get("n4096_calls", 0) == 0
            if index in excluded:
                continue
            duration = row.get("controlled_s", row.get("resource_raw_s"))
            assert duration is not None
            known += Decimal(str(duration))
            a = row.get("raw_start_ns", row.get("start_raw_ns"))
            b = row.get("raw_end_ns", row.get("end_raw_ns"))
            if a is not None and b is not None:
                close((b - a) / 1e9, duration)
        assert known == Decimal(actor["known_actual_raw_s"])
        actor_cost += known
    assert actor_cost == Decimal(costs["separate_known_actor_raw_s"])
    assert actor_cost + Decimal(costs["primary_resource_s"]["cumulative"]) == Decimal(costs["known_recorded_cumulative_s"])
    snapshot = P1 / "evidence/measurement/goal2r/final-results-resource-ledger.jsonl"
    assert sha(snapshot) == summary["costs"]["ledger_sha256"]
    snap_ends = [r for r in records(snapshot) if r["type"] == "task_end"]
    assert sum(r["n4096_calls"] for r in snap_ends) == summary["costs"]["n4096_calls"] == 428
    close(sum(r["resource_s"] for r in snap_ends), summary["costs"]["resource_s"])
    receipt = load(P1 / "evidence/finalization/previous-publication-receipt.json")
    additions = Decimal(str(receipt["publication_controlled_raw_s"])) + Decimal(receipt["final_metadata_raw_s"])
    additions += Decimal(receipt["final_command_evidence_read"]["raw_s"]) + Decimal(receipt["final_closure_metadata"]["raw_s"])
    assert Decimal(costs["known_recorded_cumulative_s"]) + additions == Decimal(receipt["cumulative_known_s"])
    assert sum(Decimal(str(r["upper_s"])) for r in costs["unknown_allowances"]) == Decimal(receipt["unknown_upper_s"]) == 144
    assert Decimal(receipt["cumulative_known_s"]) + 144 == Decimal(receipt["cumulative_conservative_upper_s"])
    result = dict(status="no_unresolved_data_findings", inputs_unchanged=True, matrix_runs_started=0,
        protocol_sha256=protocol_sha, source_sha256=protocol["target"]["sha256"], ledger_attempts=len(ends),
        formal_measurements=len(observed), formal_roles={f"{a}/{b}":v for (a,b),v in counts.items()},
        searches=len(searches), grid=grid, panels=panels, paired=pairs,
        median_cost_saving_pct=100 * statistics.median(p["cost_saving_fraction"] for p in pairs),
        rejected_blocks=rejected, severe_blocks=severe, additional_n4096=extras, historical_calls=48,
        cumulative_old_calls=429, qpc_intervals=len(checks), formal_block_checks=32, fresh_block_checks=2,
        maximum_qpc_endpoint_s=max(max(r["endpoint_s"]) for r in checks),
        maximum_qpc_width_fraction=max(r["width_fraction"] for r in checks),
        raw_qpc_ratio_extrema=[min(r["ratio"][0] for r in checks), max(r["ratio"][1] for r in checks)],
        costs=dict(summary_calls=428, summary_s=summary["costs"]["resource_s"], prepublication_calls=429,
                   prepublication_known_s=costs["known_recorded_cumulative_s"], previous_final_known_s=receipt["cumulative_known_s"],
                   unknown_budget_upper_s=receipt["unknown_upper_s"], previous_conservative_s=receipt["cumulative_conservative_upper_s"]),
        limitations=["Saved measurements audited; no historical experiments rerun", "Finite before/after samples do not calibrate every instant", "Observed min/max is not a confidence interval"])
    finish = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    result["audit_execution"] = dict(clock=RAW, start_ns=begin, end_ns=finish, raw_s=(finish-begin)/1e9,
                                     scope="read/computation only; JSON serialization/write excluded")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k:result[k] for k in ("status", "formal_measurements", "searches", "cumulative_old_calls", "median_cost_saving_pct", "qpc_intervals", "audit_execution")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
