#!/usr/bin/env python3
"""Re-evaluate historical choices by one immutable reference, without changing old scores."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

P1 = Path(__file__).resolve().parents[1]
INPUTS = {
    "grid_summary.csv": "8f3bfbb506370076afe3a15f08cd1bcff8f5e23e34f05a5ec6e9e5702f6761ec",
    "search_summary.csv": "9bbc2490e77476f40278f16eead5b053a0cc67b828b86e14346d1de548e31fbc",
}


def paired_gain(rounds, same_config=False):
    """Describe aligned panel rounds; these extrema are not confidence limits."""
    if len(rounds) not in (3, 5) or [r.get("round") for r in rounds] != list(range(1, len(rounds) + 1)):
        raise ValueError("a paired panel needs three rounds, or all five after the planned addition")
    values = []
    for row in rounds:
        times = [row.get(key) for key in ("random_s", "recheck_s", "anchor_s")]
        if any(not isinstance(value, (int, float)) or isinstance(value, bool) or
               not math.isfinite(value) or value <= 0 for value in times):
            raise ValueError("every panel observation and anchor must have a positive valid time")
        values.append(0.0 if same_config else 100 * (times[0] - times[1]) / times[2])
    return dict(gain_panel_rounds_pp=values, gain_panel_pp=statistics.median(values),
                gain_panel_low_pp=min(values), gain_panel_high_pp=max(values),
                confirmation_rounds=len(values))


def reaches(value, boundary):
    return value >= boundary or math.isclose(value, boundary, rel_tol=0, abs_tol=1e-12)


def goal2r_decision(pairs, expected_count, budget=8, data_complete=True, timing_valid=True):
    """Apply the frozen Goal 2R order to finite, observed paired evidence."""
    result = dict(decision="INCONCLUSIVE", reasons=[], evaluation_complete=False,
                  cost_clock="CLOCK_MONOTONIC_RAW", ranges_are_confidence_intervals=False)
    if not data_complete or not timing_valid:
        result["reasons"] = ["missing correctness, timing, identity, or complete cost evidence"]
        return result
    if type(expected_count) is not int or expected_count < 1 or len(pairs) != expected_count or \
            len({row.get("seed") for row in pairs}) != expected_count:
        result["reasons"] = ["missing or duplicated required paired seeds"]
        return result
    lows, highs, gains, savings = [], [], [], []
    for row in pairs:
        samples = row.get("gain_panel_rounds_pp", [])
        costs = [row.get("baseline_cost_s"), row.get("candidate_cost_s")]
        if row.get("valid") is not True or row.get("baseline_calls") != budget or \
                row.get("candidate_calls") != budget or len(samples) not in (3, 5) or \
                any(not isinstance(value, (int, float)) or isinstance(value, bool) or
                    not math.isfinite(value) for value in samples) or \
                any(not isinstance(value, (int, float)) or isinstance(value, bool) or
                    not math.isfinite(value) or value <= 0 for value in costs):
            result["reasons"] = ["incomplete valid panels, equal actual-call budgets, or driver cost"]
            return result
        if type(row.get("same_config")) is not bool or \
                row["same_config"] and any(value != 0 for value in samples):
            raise ValueError("same configuration has zero selection gain, with its raw observations retained")
        if "baseline_config" in row and "candidate_config" in row and \
                row["same_config"] != (row["baseline_config"] == row["candidate_config"]):
            raise ValueError("paired identity differs from its recorded configuration equality")
        lows.append(min(samples))
        highs.append(max(samples))
        gains.append(statistics.median(samples))
        savings.append(1 - costs[1] / costs[0])
    saving = statistics.median(savings)
    result.update(evaluation_complete=True, gain_lows_pp=lows, gain_highs_pp=highs,
                  median_gain_panel_pp=statistics.median(gains),
                  median_gain_low_pp=statistics.median(lows),
                  paired_cost_savings_fraction=savings, median_cost_saving_fraction=saving)
    if any(not reaches(value, -2) for value in highs):
        result.update(decision="REJECT", reasons=["observed gain upper bound is below -2pp"],
                      severe_regression=any(not reaches(value, -10) for value in highs))
        return result
    risk_safe = all(reaches(value, -2) for value in lows)
    quality_low = reaches(statistics.median(lows), 2) and sum(reaches(value, 5) for value in lows) >= 2
    quality_high = reaches(statistics.median(highs), 2) and sum(reaches(value, 5) for value in highs) >= 2
    quality_cost = reaches(saving, -.10)
    result["conditions"] = dict(risk_safe=risk_safe, efficiency=reaches(saving, .10),
                               quality_lower_supported=quality_low,
                               quality_upper_possible=quality_high, quality_cost=quality_cost)
    if not risk_safe:
        result["reasons"] = ["observed gains cross the -2pp risk threshold"]
    elif reaches(saving, .10):
        result.update(decision="KEEP", route="efficiency", reasons=["observed risk and median driver saving meet the efficiency route"])
    elif quality_low and quality_cost:
        result.update(decision="KEEP", route="quality", reasons=["observed risk, gain lower bounds, and driver costs meet the quality route"])
    elif quality_high and quality_cost:
        result["reasons"] = ["observed gains cross the quality benefit thresholds"]
    else:
        result.update(decision="REJECT", reasons=["complete observed evidence supports neither meaningful benefit route"])
    return result


def confirmation_additions(pairs):
    """Select at most two whole panels, before reading any extra rounds."""
    decision = goal2r_decision(pairs, len(pairs))
    if decision["decision"] != "INCONCLUSIVE" or not decision["evaluation_complete"]:
        return []
    eligible = []
    quality_possible = decision["conditions"]["quality_upper_possible"] and decision["conditions"]["quality_cost"]
    for row in pairs:
        if row["same_config"] or len(row["gain_panel_rounds_pp"]) != 3:
            continue
        low, high = min(row["gain_panel_rounds_pp"]), max(row["gain_panel_rounds_pp"])
        risk_crossing = not reaches(low, -2) and reaches(high, -2)
        quality_crossing = quality_possible and any(not reaches(low, bound) and reaches(high, bound) for bound in (2, 5))
        if risk_crossing or quality_crossing:
            eligible.append((0 if risk_crossing else 1, -(high - low), row["seed"]))
    return [seed for _, _, seed in sorted(eligible)[:2]]


def goal2r_final_retention(selection, confirmation):
    main, held = selection.get("decision"), confirmation.get("decision")
    retained = main == held == "KEEP" and selection.get("evaluation_complete") is True and \
        confirmation.get("evaluation_complete") is True
    final = "KEEP" if retained else "INCONCLUSIVE" if main == "KEEP" and held in (
        None, "NOT_EXECUTED", "INCONCLUSIVE") else "REJECT" if "REJECT" in (main, held) else "INCONCLUSIVE"
    return dict(selection=main, confirmation=held, decision=final, retained=retained,
                comparison_baseline="random", recommended_strategy="recheck" if retained else "base_algorithms",
                cli_default_algorithm="grid")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=P1 / "results/summary")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    for name, expected in INPUTS.items():
        if hashlib.sha256((args.input_dir / name).read_bytes()).hexdigest() != expected:
            raise ValueError("historical input identity changed: " + name)
    with (args.input_dir / "grid_summary.csv").open(newline="") as stream:
        grid = list(csv.DictReader(stream))
    reference = {(int(row["s"]), row["opt"]): float(row["median_s"]) for row in grid}
    expected_space = {(s, opt) for s in (8, 16, 24, 64, 128) for opt in ("O0", "O1", "O2", "O3")}
    if set(reference) != expected_space or len(grid) != 20 or any(
        int(row["valid_runs"]) != 3 or int(row["failed_runs"]) != 0 for row in grid
    ) or any(not math.isfinite(value) or value <= 0 for value in reference.values()):
        raise ValueError("incomplete or invalid historical reference")
    best = min(reference.values())
    with (args.input_dir / "search_summary.csv").open(newline="") as stream:
        searches = list(csv.DictReader(stream))
    output = []
    for row in searches:
        if row["state"] != "complete" or row["confirmation_state"] != "complete":
            raise ValueError("historical search/confirmation is incomplete")
        config = int(row["returned_s"]), row["returned_opt"]
        value = reference[config]
        output.append(dict(stage=row["stage"], algorithm=row["algorithm"], seed=int(row["seed"]),
            s=config[0], opt=config[1], reference_s=value, gap_ref_pct=100 * (value / best - 1),
            observed_reference_within_5pct=value <= 1.05 * best,
            online_score_s=float(row["online_score_s"]),
            separate_confirmation_s=float(row["confirmed_s"]),
            search_process_runs=int(row["search_process_runs"]),
            confirmation_process_runs=int(row["confirmation_process_runs"]),
            search_driver_monotonic_s=float(row["search_full_driver_wall_s"]),
            confirmation_driver_monotonic_s=float(row["confirmation_full_driver_wall_s"]),
            total_driver_monotonic_s=float(row["total_wall_s"]), journal=row["journal"]))
    directory = args.output_dir.resolve()
    if directory.exists():
        raise ValueError("derived output exists; use a new directory")
    if directory == args.input_dir.resolve() or any(
        directory == (P1 / "results" / name).resolve() or (P1 / "results" / name).resolve() in directory.parents
        for name in ("reference_v1", "selection_v1", "holdout_v1", "conflict_selection_v1")
    ):
        raise ValueError("derived output must stay outside raw/input directories")
    directory.mkdir(parents=True)
    with (directory / "search_choices.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    provenance = dict(historical_checkpoint="3ac0c4688b964c873379d012cbcf09afb7ed0937",
        input_sha256=INPUTS, n=4096, kernel_clock="CLOCK_MONOTONIC", reference_min_s=best,
        quality_rule="one T_ref(c) for each configuration identity; independent confirmation is separate",
        limitation="observational reference only; 5% membership is not a reliable near-optimality proof",
        old_raw_protocol_scores_and_decisions_changed=False, searches=output)
    (directory / "summary.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(searches=len(output), reference_configs=len(reference), output=str(directory))))


if __name__ == "__main__":
    main()
