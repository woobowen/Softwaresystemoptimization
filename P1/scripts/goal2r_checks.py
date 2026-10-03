#!/usr/bin/env python3
"""Run the predeclared Goal 2R numerical and clock checks, serially."""

import argparse
import json
from pathlib import Path
import statistics
import sys

import experiment_v2 as ex
import host_clock_probe as host
import validate_target as validation

P1 = ex.P1
OUT = P1 / "evidence/measurement/goal2r"
CACHE = P1 / ".cache/goal2r"
SOURCE = P1 / "src/matrix_multiplication.c"
FRAMEWORK = P1 / "src/autotuner.py"
PLAN = P1 / "evidence/measurement/goal2r_timing_plan.json"


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def target_command(config, journal, mode, source=SOURCE, cache=None, action="run"):
    return ["taskset", "-c", "0", sys.executable, "-B", str(FRAMEWORK), action,
            "--target", str(source), "--cache-dir", str(cache or P1 / ".cache/build_goal2r"),
            "--s", str(config["s"]), "--opt", config["opt"], "--repeats", "1",
            "--timeout", "1200", "--compile-timeout", "60", "--mode", mode,
            "--output", str(journal)]


def run(command, name, role, *, journal=None, calls=0, mode="correctness", limit=1200):
    result = ex.controlled(command, OUT, name, role, call_upper=calls, journal=journal,
                           time_limit=limit, mode=mode)
    print(json.dumps(dict(task=name, returncode=result["returncode"],
                         calls=result["n4096_calls"], driver_raw_s=result["driver_raw_s"])), flush=True)
    return result


def numeric(label=""):
    original = (P1 / "src/matrix_multiplication.original.c").read_text()
    text = SOURCE.read_text()
    if validation.kernel(text) != validation.kernel(original):
        raise ValueError("matrix computation differs from the teacher's kernel")
    if text.count("    return 0;") != 1:
        raise ValueError("unexpected final return marker")
    adapted = text.replace("    return 0;", "    return verify();", 1)
    adapted = adapted.replace("int main(int argc, const char *argv[]){",
                              validation.REFERENCE + "\nint main(int argc, const char *argv[]){", 1)
    if validation.kernel(adapted) != validation.kernel(original):
        raise ValueError("numerical checker changed the computation")
    suffix = "-" + label if label else ""
    variant = CACHE / ("verify_4096_default" + suffix + ".c")
    variant.parent.mkdir(parents=True, exist_ok=True)
    variant.write_text(adapted)
    write_new(OUT / ("numeric_adapter" + suffix + ".json"), dict(source_sha256=ex.sha256(SOURCE),
        variant_sha256=ex.sha256(variant), original_sha256=ex.sha256(P1 / "src/matrix_multiplication.original.c"),
        kernel_sha256=ex.at.digest(validation.kernel(text).encode()), initialization="original, no srand",
        reference="unblocked independent long-double dot products; 8 edges and 16 fixed pseudorandom points",
        point_seed=20260930, atol=1e-12, rtol=1e-11,
        configs=[dict(s=24, opt="O0"), dict(s=128, opt="O3")]))
    for config in (dict(s=24, opt="O0"), dict(s=128, opt="O3")):
        name = f"numeric-s{config['s']}-{config['opt']}" + suffix
        journal = OUT / (name + ".jsonl")
        command = target_command(config, journal, "correctness", variant, CACHE / "numeric-build")
        command += ["--cflag=-Wl,--no-as-needed", "--cflag=-lm"]
        run(command, name, "goal2r_numeric", journal=journal, calls=1)
        measurements = [r for r in ex.read_records(journal) if r["type"] == "measurement"]
        if len(measurements) != 1 or measurements[0]["status"] != "ok" or \
                "count=24" not in measurements[0]["stdout"] or "failures=0" not in measurements[0]["stdout"]:
            raise ValueError("n4096 independent numerical check failed")
        print(measurements[0]["stdout"], flush=True)


def prebuild():
    for opt in ex.at.OPTS:
        name = f"prebuild-{opt}"
        journal = OUT / (name + ".jsonl")
        command = target_command(dict(s=128, opt=opt), journal, "diagnostic", action="build")
        command += ["--opts", opt]
        run(command,
            name, "goal2r_prebuild", journal=journal, mode="diagnostic", limit=120)


def timing():
    plan = ex.load_json(PLAN)
    probe = P1 / plan["probe"]["path"]
    if ex.sha256(probe) != plan["probe"]["sha256"]:
        raise ValueError("predeclared clock workload identity changed")
    diagnostic_results, aa_results = [], []
    spent = 0.0
    def remaining():
        left = plan["resource_limits"]["controlled_seconds_cap"] - spent
        if left <= 0:
            raise ValueError("initial clock diagnostics consumed their controlled-time cap")
        return left
    for block_index, block in enumerate(plan["initial_blocks"]):
        workloads, matrix_journal = [], None
        for item in block["intervals"]:
            if item["kind"] == "matrix_n4096":
                matrix_journal = OUT / (item["id"] + ".jsonl")
                command = target_command(item["config"], matrix_journal, "diagnostic")
            else:
                kind = "idle" if item["kind"] == "idle" else "work"
                command = ["taskset", "-c", "0", str(probe), kind,
                           str(item.get("iterations", 0)), str(item.get("requested_seconds", 0))]
            workloads.append(dict(mode=item["id"], command=command, timeout_s=1200))
        input_path = OUT / (block["id"] + "-input.json")
        write_new(input_path, workloads)
        name = block["id"]
        record = run([sys.executable, "-B", str(P1 / "scripts/host_clock_probe.py"),
                      "--intervals", str(input_path)], name, "goal2r_clock_diagnostic",
                     journal=matrix_journal, calls=1, mode="diagnostic", limit=remaining())
        spent += record["driver_raw_s"]
        raw_path = OUT / (name + ".stdout.txt")
        data = ex.load_json(raw_path)
        if not data.get("complete") or not data.get("lifecycle_valid"):
            raise ValueError("host bridge did not complete its owned lifecycle")
        for observed in data["intervals"]:
            recalculated = host.interval(observed["first"], observed["last"], data["host_frequency_hz"])
            if not recalculated["usable_brackets"] or not recalculated["raw_relative_screen_pass"]:
                raise ValueError("RAW/QPC interval needs diagnosis before performance experiments")
            diagnostic_results.append(dict(id=observed["mode"], source=str(raw_path.relative_to(P1)),
                sha256=ex.sha256(raw_path), host_pid=data["host_pid"],
                host_managed_thread_id=data["host_managed_thread_id"], frequency_hz=data["host_frequency_hz"],
                **recalculated))
        for item in plan["aa_processes"][block_index * 4:(block_index + 1) * 4]:
            journal = OUT / (item["id"] + ".jsonl")
            record = run(target_command(item["config"], journal, "benchmark"), item["id"],
                         "goal2r_clock_aa", journal=journal, calls=1,
                         mode="diagnostic", limit=remaining())
            spent += record["driver_raw_s"]
            sample = next(r for r in ex.read_records(journal) if r["type"] == "measurement")
            if sample["status"] != "ok" or sample["timing_status"] != "ok":
                raise ValueError("A/A physical target has invalid mathematical or primary timing output")
            aa_results.append(dict(**item, source=str(journal.relative_to(P1)), sha256=ex.sha256(journal),
                pid=sample["pid"], kernel_s=sample["kernel_s"], kernel_start_ns=sample["kernel_start_ns"],
                kernel_end_ns=sample["kernel_end_ns"], process_raw_s=sample["process_raw_s"],
                process_auxiliary_s=sample["clock_deltas_s"], driver_raw_s=record["driver_raw_s"]))
    pairs = []
    for tier in ("F", "M"):
        for pair in (1, 2):
            selected = {r["label"]: r for r in aa_results if r["tier"] == tier and r["pair"] == pair}
            a, b = selected["A"]["kernel_s"], selected["B"]["kernel_s"]
            pairs.append(dict(tier=tier, pair=pair, a_s=a, b_s=b,
                              signed_difference_pct=100 * (a - b) / statistics.median([a, b]),
                              different_processes=selected["A"]["pid"] != selected["B"]["pid"]))
    write_new(OUT / "timing_result.json", dict(primary_supported=len(diagnostic_results) == 6 and len(aa_results) == 8,
        primary_clock="CLOCK_MONOTONIC_RAW", cost_clock="CLOCK_MONOTONIC_RAW", unit="ns before subtraction; seconds after",
        boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        timing_plan_sha256=ex.sha256(PLAN), host_source_sha256=ex.sha256(P1 / "scripts/host_clock_probe.py"),
        kernel_scope="six-loop multiply only; exact integer boundaries in target stdout",
        qpc_matrix_scope="outer aligned core CLI interval including process, cache/framework and initialization; not kernel-only",
        process_scope="Linux parent before spawn to after communicate",
        search_scope="actual outer driver launch through completed journal; formal blocks checked separately",
        intervals=diagnostic_results, aa_samples=aa_results, aa_pairs=pairs,
        diagnostic_calls=10, diagnostic_controlled_raw_s=spent,
        limitations=["QPC and RAW may share hardware; consistency during checked intervals, not independent absolute calibration",
                     "Auxiliary clock adjustments do not identify the cause from a snapshot",
                     "A/A ranges describe these eight processes; no universal future noise padding or clock-failure inference",
                     "Before/after checks cover predeclared blocks; no proof of every instant between endpoints"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("small", "sanitizer", "numeric", "prebuild", "timing"))
    parser.add_argument("--numeric-label", choices=("", "repair1"), default="", help="separate corrected checker records from the failed build")
    args = parser.parse_args()
    action = args.action
    OUT.mkdir(parents=True, exist_ok=True)
    with ex.performance_lock():
        if action in ("small", "sanitizer"):
            run(["taskset", "-c", "0", sys.executable, "-B", str(P1 / "scripts/validate_target.py"),
                 "--suite", action, "--output", str(OUT / (action + ".jsonl"))],
                action, "goal2r_numerical_small", mode="correctness", limit=300)
        else:
            {"numeric": lambda: numeric(args.numeric_label), "prebuild": prebuild, "timing": timing}[action]()


if __name__ == "__main__":
    main()
