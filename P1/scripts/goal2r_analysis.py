"""Read the new Goal 2R batches; historical analysis stays at its matching commit."""

import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

import experiment_v2 as ex
import host_clock_probe as host
from identity_quality import paired_gain, goal2r_decision, goal2r_final_retention, confirmation_additions


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                         for k, v in row.items()} for row in rows)


def describe(values):
    return dict(valid_runs=len(values), samples=values, median_s=statistics.median(values) if values else None,
                min_s=min(values) if values else None, max_s=max(values) if values else None,
                mad_s=statistics.median(abs(v - statistics.median(values)) for v in values) if values else None)


def block_id(stage, job):
    if stage == "reference":
        return f"round-{job['round']}" if job.get("round") else None
    if stage == "starts":
        return job["id"]
    if stage in ("comparison", "confirmation"):
        prefix = "additional-seed" if job.get("round", 0) > 3 else "seed"
        return f"{prefix}-{job['seed']}"
    return None


def clock_checks(directory, protocol_sha, ledger_starts, ledger_ends):
    path = directory / "block_checks.jsonl"
    records = ex.read_records(path) if path.exists() else []
    states, table = {}, []
    for row in records:
        if row.get("type") != "clock_block_check":
            continue
        key = row["block_id"], row["phase"]
        if key in states or row["phase"] not in ("before", "after"):
            raise ValueError("duplicate or unknown block clock endpoint")
        raw = (ex.P1 / row["raw_path"]).resolve()
        raw.relative_to(ex.P1.resolve())
        if ex.sha256(raw) != row["sha256"] or row.get("protocol_sha256") != protocol_sha:
            raise ValueError("block clock source differs from its frozen check")
        data = json.loads(raw.read_text())
        start, end = ledger_starts.get(row["attempt_id"]), ledger_ends.get(row["attempt_id"])
        if start is None or end is None or row.get("boot_id") != start.get("boot_id"):
            raise ValueError("clock check lacks its same-boot physical driver attempt")
        valid = data.get("complete") is True and data.get("lifecycle_valid") is True and len(data.get("intervals", [])) == 1
        bounds, widths, endpoints = None, None, None
        try:
            for interval in data.get("intervals", []):
                for reading in (interval["first"], interval["last"]):
                    lower, upper = reading["before_ns"]["RAW"], reading["after_ns"]["RAW"]
                    if type(lower) is not int or type(upper) is not int or type(reading["host_tick"]) is not int or \
                            not start["clock_start_ns"]["raw"] <= lower <= upper <= end["clock_end_ns"]["raw"]:
                        raise ValueError("QPC endpoint is outside its own integer RAW driver boundaries")
                    if reading["frequency_hz"] != data["host_frequency_hz"] or reading["host_pid"] != data["host_pid"] or \
                            reading.get("host_managed_thread_id") != data.get("host_managed_thread_id") or data.get("host_managed_thread_id") is None:
                        raise ValueError("QPC response identity changed")
                calculated = host.interval(interval["first"], interval["last"], data["host_frequency_hz"])
                bounds = calculated["linux_interval_bounds"]["RAW"]["linux_to_host_ratio_bounds"]
                widths = calculated["linux_interval_bounds"]["RAW"]["bracket_width_fraction"]
                endpoints = calculated["endpoint_bracket_s"]
                valid = valid and calculated["usable_brackets"] and calculated["raw_relative_screen_pass"]
        except (ValueError, KeyError, TypeError):
            valid = False
        if bool(row["valid"]) != bool(valid):
            raise ValueError("saved clock-check decision differs from its raw bracket calculation")
        states[key] = dict(valid=bool(valid), boot_id=row["boot_id"],
                           begin_ns=start["clock_start_ns"]["raw"], end_ns=end["clock_end_ns"]["raw"])
        table.append(dict(directory=directory.name, block_id=key[0], phase=key[1], valid=bool(valid),
                          raw_qpc_bounds=bounds, raw_bracket_width_fraction=widths,
                          endpoint_s=endpoints, raw_path=row["raw_path"], sha256=row["sha256"]))
    blocks = {}
    for key, _ in states:
        before, after = states.get((key, "before")), states.get((key, "after"))
        blocks[key] = dict(valid=bool(before and after and before["valid"] and after["valid"]),
                           raw_begin_ns=before["end_ns"] if before else None,
                           raw_end_ns=after["begin_ns"] if after else None,
                           boot_id=before["boot_id"] if before else None)
        if before and after and before["boot_id"] != after["boot_id"]:
            raise ValueError("experiment block crosses boot identities")
    return blocks, table


def addition_manifest(base, directory, protocol):
    path = directory / f"panel-b{base['block']}-additional.json"
    if not path.exists():
        return []
    saved = ex.load_json(path)
    for key in ("block", "seed", "protocol_sha256", "dependencies_sha256", "reference_manifest_sha256",
                "reference_config", "configs"):
        if saved.get(key) != base[key]:
            raise ValueError("additional panel changed locked returns, reference, or source identity")
    if saved.get("additional_to_sha256") != ex.sha256(directory / f"panel-b{base['block']}.json"):
        raise ValueError("additional panel lacks its original panel binding")
    if saved.get("selected_seed") != base["seed"] or saved.get("round_start") != 4 or saved.get("rounds") != [4, 5]:
        raise ValueError("additional panel changed its selected seed or round numbers")
    expected = []
    for round_id in (4, 5):
        order = sorted((c["s"], c["opt"]) for c in base["configs"])
        random.Random(protocol["return_confirmation"]["order_seed"] + 100 * base["block"] + round_id).shuffle(order)
        for s, opt in order:
            expected.append(dict(id=f"panel-b{base['block']}-r{round_id}-s{s}-{opt}", action="run",
                role="shared_confirmation", block=base["block"], seed=base["seed"], round=round_id,
                repeats=1, config=dict(s=s, opt=opt)))
    if saved["jobs"] != expected:
        raise ValueError("additional panel is not the two predeclared complete rounds")
    fingerprint = dict(saved)
    fingerprint.pop("fingerprint", None)
    if saved.get("fingerprint") != ex.at.fingerprint(fingerprint):
        raise ValueError("additional panel fingerprint changed")
    return saved["jobs"]


def read_batches(directories, protocol, protocol_path, reference, ledger_starts, ledger_ends):
    batches, measurements, curves, searches, checks = [], [], [], [], []
    for directory in directories:
        directory = directory.resolve()
        manifest = ex.load_json(directory / "plan.json")
        ex.freeze_check(protocol, manifest, protocol_path)
        local_protocol = dict(protocol, measurement_root=manifest["measurement_root"])
        healthy, raw_checks = clock_checks(directory, protocol["protocol_sha256"], ledger_starts, ledger_ends)
        checks.extend(raw_checks)
        driver = [r for r in ex.read_records(directory / "driver.jsonl") if r["type"] == "task_end"]
        if len({r["attempt_id"] for r in driver}) != len(driver):
            raise ValueError("duplicate driver attempt would charge the same work twice")
        costs = {}
        for row in driver:
            charged = ledger_ends.get(row["attempt_id"])
            if charged is None or any(value != charged.get(key) for key, value in row.items() if key not in ("type", "at")):
                raise ValueError("batch cost has no identical physical ledger attempt")
            spans = row["clock_elapsed_s"]
            if row.get("driver_raw_s") != spans["raw"] or spans["raw"] <= 0:
                raise ValueError("new search cost lacks a positive explicit RAW driver interval")
            costs[row["task"]] = costs.get(row["task"], 0) + spans["raw"]
        jobs, panels = [], []
        for job in manifest["jobs"]:
            if job["action"] != "panel":
                jobs.append(job)
            elif (directory / (job["id"] + ".json")).exists():
                panel_jobs = ex.panel(job, directory, reference, local_protocol, historical=True)
                base = ex.load_json(directory / (job["id"] + ".json"))
                panels.append(base)
                jobs.extend(panel_jobs)
                jobs.extend(addition_manifest(base, directory, protocol))
        if len({job["id"] for job in jobs}) != len(jobs):
            raise ValueError("duplicate actual task cannot become a second observation")
        for job in jobs:
            path = directory / (job["id"] + ".jsonl")
            state = ex.validate_task(job, directory, local_protocol, historical=True)
            records = ex.read_records(path) if path.exists() else []
            summary = records[-1] if records and records[-1]["type"] == "summary" else None
            scope = healthy.get(block_id(manifest["stage"], job)) if block_id(manifest["stage"], job) else None
            valid = state == "complete" and (scope["valid"] if scope else block_id(manifest["stage"], job) is None)
            attempts = [r for r in driver if r["task"] == job["id"]]
            if summary and sum(r["n4096_calls"] for r in attempts) != summary["process_runs"]:
                raise ValueError("search/process call count lacks its actual driver charge")
            if scope and scope["valid"]:
                for attempt in attempts:
                    begin = ledger_starts[attempt["attempt_id"]]
                    if begin["boot_id"] != scope["boot_id"] or not scope["raw_begin_ns"] <= begin["clock_start_ns"]["raw"] <= \
                            attempt["clock_end_ns"]["raw"] <= scope["raw_end_ns"]:
                        raise ValueError("target driver is outside its predeclared QPC block boundaries")
            for row in records:
                if row["type"] == "measurement":
                    measurements.append(dict(stage=manifest["stage"], task=job["id"], role=job["role"],
                        block=job.get("block"), seed=job.get("seed"), round=job.get("round"), algorithm=job.get("algorithm"),
                        **row["config"], valid=valid and row["status"] == "ok", status=row["status"],
                        kernel_s=row.get("kernel_s"), process_raw_s=(row.get("clock_deltas_s") or {}).get("CLOCK_MONOTONIC_RAW"),
                        binary_sha256=row.get("binary_sha256"), journal=str(path.relative_to(ex.P1))))
                elif row["type"] == "trial" and job["action"] == "search":
                    curves.append(dict(stage=manifest["stage"], seed=job["seed"], algorithm=job["algorithm"],
                        step=row["trial_id"] + 1, phase=row.get("phase", "explore"),
                        actual_calls=sum(r["type"] == "measurement_start" and r["trial_id"] <= row["trial_id"] for r in records),
                        observed_score_s=row["score"], fresh_score_s=row.get("fresh_score", row["score"]),
                        best_so_far_s=row["best_so_far"]["score"] if row["best_so_far"] else None,
                        tuning_raw_elapsed_s=row["tuning_raw_elapsed_s"]))
            if job["action"] == "search":
                best = summary.get("best") if summary else None
                searches.append(dict(stage=manifest["stage"], block=job.get("block"), seed=job["seed"],
                    algorithm=job["algorithm"], state=state, valid=valid,
                    returned_s=best["config"]["s"] if best else None, returned_opt=best["config"]["opt"] if best else None,
                    online_score_s=best["score"] if best else None, process_runs=summary["process_runs"] if summary else None,
                    distinct_configs=summary["distinct_configs"] if summary else None,
                    internal_rechecks=summary.get("recheck_trials", 0) if summary else None,
                    search_driver_raw_s=costs.get(job["id"]), journal=str(path.relative_to(ex.P1))))
        batches.append(dict(path=directory, manifest=manifest, panels=panels, healthy=healthy))
    return batches, measurements, searches, curves, checks


def project_costs(path):
    data = path.read_bytes()
    rows = [json.loads(line) for line in data.decode().splitlines()]
    starts = {r["attempt_id"]: r for r in rows if r["type"] == "task_start"}
    ends = {r["attempt_id"]: r for r in rows if r["type"] == "task_end"}
    if len(starts) != sum(r["type"] == "task_start" for r in rows) or len(ends) != sum(r["type"] == "task_end" for r in rows):
        raise ValueError("duplicate physical cost attempt")
    complete = starts.keys() == ends.keys() and all(r.get("n4096_calls_known", True) for r in ends.values())
    for key, end in ends.items():
        ex.resource_span(starts[key], end)
    roles = []
    for role in sorted({r["role"] for r in ends.values()}):
        grouped = [r for r in ends.values() if r["role"] == role]
        roles.append(dict(role=role, tasks=len(grouped), n4096_calls=sum(r["n4096_calls"] for r in grouped),
                          failures=sum(r.get("returncode") != 0 or bool(r.get("reason")) for r in grouped),
                          resource_s=sum(r["resource_s"] for r in grouped)))
    if complete:
        checked_calls, checked_cost = ex.usage(path)
        if checked_calls != sum(r["n4096_calls"] for r in ends.values()) or checked_cost != sum(r["resource_s"] for r in ends.values()):
            raise ValueError("global physical journal count differs from project cost aggregation")
    return dict(complete=complete, n4096_calls=sum(r["n4096_calls"] for r in ends.values()),
                resource_s=sum(r["resource_s"] for r in ends.values()), role_costs=roles,
                pending_attempts=sorted(starts.keys() - ends.keys()),
                aggregate_is_complete_cost=complete,
                ledger_sha256=hashlib.sha256(data).hexdigest()), starts, ends


def comparisons(searches, measurements, reference, stage, seeds):
    indexed = {(r["seed"], r["algorithm"]): r for r in searches if r["stage"] == stage}
    pairs = []
    for seed in seeds:
        baseline, candidate = indexed.get((seed, "random")), indexed.get((seed, "recheck"))
        if baseline is None or candidate is None:
            continue
        configs = [dict(s=r["returned_s"], opt=r["returned_opt"]) for r in (baseline, candidate)]
        rows = [r for r in measurements if r["stage"] == stage and r["seed"] == seed and r["role"] == "shared_confirmation"]
        rounds = sorted({r["round"] for r in rows})
        values, valid = [], baseline["valid"] and candidate["valid"]
        for round_id in rounds:
            times = []
            for config in [*configs, reference]:
                found = [r for r in rows if r["round"] == round_id and (r["s"], r["opt"]) == (config["s"], config["opt"])]
                valid = bool(valid and len(found) == 1 and found[0]["valid"])
                times.append(found[0]["kernel_s"] if len(found) == 1 and found[0]["valid"] else None)
            values.append(dict(round=round_id, random_s=times[0], recheck_s=times[1], anchor_s=times[2]))
        pair = dict(stage=stage, seed=seed, block=baseline["block"], valid=bool(valid), same_config=configs[0] == configs[1],
            baseline_config=configs[0], candidate_config=configs[1], baseline_calls=baseline["process_runs"],
            candidate_calls=candidate["process_runs"], baseline_cost_s=baseline["search_driver_raw_s"],
            candidate_cost_s=candidate["search_driver_raw_s"], rounds=values)
        try:
            pair.update(paired_gain(values, pair["same_config"]))
        except ValueError:
            pair.update(valid=False, gain_panel_rounds_pp=[], gain_panel_pp=None, gain_panel_low_pp=None, gain_panel_high_pp=None)
        if all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in (pair["baseline_cost_s"], pair["candidate_cost_s"])):
            pair["cost_saving_fraction"] = 1 - pair["candidate_cost_s"] / pair["baseline_cost_s"]
        pairs.append(pair)
    return pairs


def plots(directory, grid, searches, curves, pairs, decisions):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw=dict(width_ratios=[1, 1.2]))
    matrix = [[next(r["median_s"] for r in grid if r["s"] == s and r["opt"] == opt) for opt in ex.at.OPTS] for s in ex.at.BLOCKS]
    heat = axes[0].imshow(matrix, cmap="YlOrRd", aspect="auto")
    axes[0].set_xticks(range(4), ex.at.OPTS); axes[0].set_yticks(range(5), ex.at.BLOCKS)
    axes[0].set_xlabel("GCC optimization"); axes[0].set_ylabel("Block size s")
    axes[0].set_title("20 configurations: three-round median (RAW seconds)")
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            axes[0].text(j, i, f"{value:.3f}", ha="center", va="center")
    fig.colorbar(heat, ax=axes[0], label="Kernel seconds")
    for i, row in enumerate(grid):
        axes[1].errorbar(row["median_s"], i, xerr=[[row["median_s"] - row["min_s"]], [row["max_s"] - row["median_s"]]], fmt="o", color="tab:blue")
    axes[1].set_yticks(range(20), [f"s{r['s']}/{r['opt']}" for r in grid]); axes[1].invert_yaxis()
    axes[1].set_xlabel("Kernel RAW seconds; bars = observed min / max")
    axes[1].set_title("All samples retained; ranges are not confidence intervals")
    fig.tight_layout(); fig.savefig(directory / "grid_median.png", dpi=160); plt.close(fig)
    colors = dict(grid="tab:blue", random="tab:orange", greedy="tab:green")
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for algorithm, color in colors.items():
        rows = [r for r in searches if r["stage"] == "comparison" and r["algorithm"] == algorithm]
        x = [r["seed"] for r in rows]
        axes[0, 0].plot(x, [r["gap_ref_pct"] for r in rows], "o-", label=algorithm, color=color)
        axes[0, 1].plot(x, [r["search_driver_raw_s"] for r in rows], "o-", label=algorithm, color=color)
        for row in rows:
            trace = [r for r in curves if r["stage"] == "comparison" and r["seed"] == row["seed"] and r["algorithm"] == algorithm]
            axes[1, 0].plot([r["actual_calls"] for r in trace], [r["best_so_far_s"] for r in trace], color=color, alpha=.45)
            axes[1, 1].plot([r["tuning_raw_elapsed_s"] for r in trace], [r["best_so_far_s"] for r in trace], color=color, alpha=.45)
    for ax in axes[0]:
        ax.set_xticks(x); ax.tick_params(axis="x", rotation=25); ax.set_xlabel("Predeclared main seed"); ax.legend()
    axes[0, 0].set_ylabel("Common reference gap (%)"); axes[0, 1].set_ylabel("Actual search driver RAW seconds")
    axes[1, 0].set_xlabel("Actual target calls"); axes[1, 1].set_xlabel("Actual online RAW elapsed seconds")
    for ax in axes[1]: ax.set_ylabel("Online best kernel RAW seconds")
    fig.suptitle("Grid / Random / Greedy: six independent searches each; online data unchanged")
    fig.tight_layout(); fig.savefig(directory / "online_search.png", dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for index, pair in enumerate(pairs):
        values = pair["gain_panel_rounds_pp"]
        axes[0].scatter([index] * len(values), values, color="tab:purple", alpha=.7)
        axes[0].plot([index, index], [min(values), max(values)], color="tab:purple")
        axes[1].bar(index, 100 * pair["cost_saving_fraction"], color="tab:blue")
    for ax in axes:
        ax.set_xticks(range(len(pairs)), [r["seed"] for r in pairs]); ax.tick_params(axis="x", rotation=25)
        ax.set_xlabel("Matching seed"); ax.grid(axis="y", alpha=.2)
    axes[0].axhline(-2, color="red", linestyle="--", label="Risk threshold -2pp")
    axes[0].set_ylabel("Round gain 100*(Random-S3)/anchor (pp)"); axes[0].legend()
    axes[1].axhline(10, color="green", linestyle="--", label="Useful cost saving 10%")
    axes[1].set_ylabel("Actual driver cost saving (%)"); axes[1].legend()
    fig.suptitle("S3 6+2 vs Random 8; main decision: " + decisions["comparison"]["decision"])
    fig.tight_layout(); fig.savefig(directory / "saved-search-results.png", dpi=160); plt.close(fig)
    return [name for name in ("grid_median.png", "online_search.png", "saved-search-results.png")]


def run(args):
    protocol = ex.load_json(args.protocol)
    if protocol.get("method") != "goal2r" or args.reference is None or args.ledger is None:
        raise ValueError("Goal 2R analysis requires the new protocol, independent reference and closed ledger")
    protocol.update(protocol_sha256=ex.sha256(args.protocol),
                    protocol_path=str(args.protocol.resolve().relative_to(ex.P1)), measurement_root=str(ex.P1))
    directories = [args.reference, *args.runs]
    if len({p.resolve() for p in directories}) != len(directories):
        raise ValueError("one raw batch cannot count twice")
    output = args.output_dir.resolve()
    if output.exists() or any(p.resolve() == output or p.resolve() in output.parents for p in directories):
        raise ValueError("derived output must be a fresh directory outside original raw")
    cost, ledger_starts, ledger_ends = project_costs(args.ledger)
    batches, samples, searches, curves, checks = read_batches(directories, protocol, args.protocol, args.reference, ledger_starts, ledger_ends)
    binaries = {}
    for row in samples:
        if row["valid"] and binaries.setdefault(row["opt"], row["binary_sha256"]) != row["binary_sha256"]:
            raise ValueError("the same frozen compiler/source/optimization used different binaries")
    identities = [(r["stage"], r["seed"], r["algorithm"]) for r in searches if r["stage"] != "starts"]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate search identity cannot overwrite another real search")
    grid = []
    for s in protocol["space"]["blocks"]:
        for opt in protocol["space"]["opts"]:
            rows = [r for r in samples if r["role"] == "reference" and (r["s"], r["opt"]) == (s, opt)]
            good = [r for r in rows if r["valid"]]
            grid.append(dict(s=s, opt=opt, failed_runs=len(rows) - len(good), rounds=[r["round"] for r in good],
                             **describe([r["kernel_s"] for r in good])))
    complete = all(r["valid_runs"] == 3 and sorted(r["rounds"]) == [1, 2, 3] and r["failed_runs"] == 0 for r in grid)
    best = min(grid, key=lambda r: (r["median_s"], protocol["space"]["blocks"].index(r["s"]),
                                   protocol["space"]["opts"].index(r["opt"]))) if complete else None
    indexed = {(r["s"], r["opt"]): r for r in grid}
    for row in grid: row["gap_ref_pct"] = 100 * (row["median_s"] / best["median_s"] - 1) if complete else None
    for row in searches:
        cell = indexed.get((row["returned_s"], row["returned_opt"]))
        row.update(reference_s=cell["median_s"] if complete and cell else None,
                   gap_ref_pct=cell["gap_ref_pct"] if complete and cell else None,
                   point_within_5pct=cell["gap_ref_pct"] <= 5 if complete and cell else None)
    reference = dict(s=best["s"], opt=best["opt"]) if best else dict(s=None, opt=None)
    pairs, decisions = {}, {}
    for stage, seeds in (("comparison", protocol["online"]["seeds"]), ("confirmation", protocol["holdout"]["seeds"])):
        pairs[stage] = comparisons(searches, samples, reference, stage, seeds)
        decisions[stage] = goal2r_decision(pairs[stage], len(seeds), data_complete=complete and cost["complete"] and
                                         protocol.get("state") == "approved" and protocol["acceptance"].get("state") == "frozen")
        if not any(r["stage"] == stage and r["algorithm"] == "recheck" and r["process_runs"] for r in searches):
            decisions[stage].update(decision="NOT_EXECUTED", evaluation_complete=False)
    if decisions["comparison"]["evaluation_complete"] and decisions["comparison"]["decision"] != "KEEP" and decisions["confirmation"]["decision"] == "NOT_EXECUTED":
        decisions["confirmation"].update(decision="NOT_REQUIRED", reasons=["complete main data did not select S3; baseline holdout still required"])
    # Later failed additions must not change the original three-round request.
    base_pairs = comparisons(searches, [r for r in samples if r.get("round") in (1, 2, 3)],
                             reference, "comparison", protocol["online"]["seeds"])
    base_decision = goal2r_decision(base_pairs, len(protocol["online"]["seeds"]),
        data_complete=complete and protocol.get("state") == "approved" and
                      protocol["acceptance"].get("state") == "frozen")
    additions = confirmation_additions(base_pairs) if base_decision["evaluation_complete"] else []
    actual_additions = [r["seed"] for r in pairs["comparison"] if r.get("confirmation_rounds") == 5]
    if actual_additions and actual_additions != [seed for seed in protocol["online"]["seeds"] if seed in additions]:
        raise ValueError("extra panels differ from the frozen crossing/width/seed selection rule")
    comparison_batches = [b for b in batches if b["manifest"]["stage"] == "comparison"]
    request = dict(pairs=base_pairs, seeds=additions, protocol_sha256=protocol["protocol_sha256"],
                   comparison_manifest_sha256=ex.sha256(comparison_batches[0]["path"] / "plan.json") if comparison_batches else None)
    request_text = json.dumps(request, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    request_sha = hashlib.sha256(request_text.encode()).hexdigest()
    for batch in comparison_batches:
        for panel in batch["panels"]:
            extra = batch["path"] / f"panel-b{panel['block']}-additional.json"
            if extra.exists() and ex.load_json(extra).get("request_sha256") != request_sha:
                raise ValueError("additional panel request does not reproduce from the original three-round raw data")
    baseline = [r for r in searches if r["stage"] == "confirmation" and r["algorithm"] == "random"]
    baseline_complete = len(baseline) == len(protocol["holdout"]["seeds"])
    for row in baseline:
        panel_rows = [p for p in samples if p["stage"] == "confirmation" and p["seed"] == row["seed"] and p["role"] == "shared_confirmation"]
        required_configs = {(row["returned_s"], row["returned_opt"]), (reference["s"], reference["opt"])}
        actual = {(p["round"], p["s"], p["opt"]) for p in panel_rows if p["valid"]}
        expected = {(r, s, opt) for r in (1, 2, 3) for s, opt in required_configs}
        baseline_complete = baseline_complete and row["valid"] and expected <= actual and len(panel_rows) == len(actual)
    baseline_complete = bool(baseline_complete and sorted(r["seed"] for r in baseline) == sorted(protocol["holdout"]["seeds"]))
    summary = dict(schema=1, method="goal2r", protocol_sha256=protocol["protocol_sha256"], analysis_sha256=ex.sha256(__file__),
        reference_complete=complete, reference_best=best, measurements=len(samples), search_tasks=len(searches),
        costs=cost, decisions=decisions, retention=goal2r_final_retention(decisions["comparison"], decisions["confirmation"]),
        additional_confirmation=dict(selected_seeds=additions, completed_seeds=actual_additions,
                                     complete=set(additions) == set(actual_additions)),
        baseline_confirmation=dict(complete=baseline_complete, seeds=[r["seed"] for r in baseline]),
        batch_manifest_sha256={b["path"].name: ex.sha256(b["path"] / "plan.json") for b in batches},
        limitation="Finite observed ranges, six main seeds and three holdout seeds; no population confidence or absolute clock calibration")
    output.mkdir(parents=True)
    (output / "additional_request.json").write_text(request_text)
    for name, rows in (("measurements", samples), ("grid_summary", grid), ("search_summary", searches),
                       ("online_curves", curves), ("block_clock_checks", checks), ("batch_costs", cost["role_costs"]),
                       ("comparison_paired", pairs["comparison"]), ("confirmation_paired", pairs["confirmation"])):
        write_csv(output / (name + ".csv"), rows)
    if args.plots and complete and len(pairs["comparison"]) == 6 and all(r["valid"] for r in pairs["comparison"]):
        summary["images"] = plots(args.image_dir or output / "images", grid, searches, curves, pairs["comparison"], decisions)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(output=str(output), reference_complete=complete, decisions=decisions,
                          n4096_calls=cost["n4096_calls"], resource_s=cost["resource_s"]), ensure_ascii=False))
    return 0
