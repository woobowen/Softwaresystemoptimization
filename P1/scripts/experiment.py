#!/usr/bin/env python3
"""Plan and resume serial experiments through the common autotuner CLI."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import time


P1 = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def invalid_json_number(value):
    raise ValueError(f"non-finite JSON number: {value}")


def finite_json_float(value):
    number = float(value)
    if not math.isfinite(number):
        invalid_json_number(value)
    return number


def load_json(path):
    return json.loads(Path(path).read_text(), parse_constant=invalid_json_number, parse_float=finite_json_float)


def read_records(path):
    """Allow an interrupted last record, but never ignore corrupt middle rows."""
    data = Path(path).read_bytes()
    records = []
    lines = data.splitlines(keepends=True)
    for index, line in enumerate(lines):
        try:
            record = json.loads(line, parse_constant=invalid_json_number, parse_float=finite_json_float)
        except json.JSONDecodeError:
            if index == len(lines) - 1 and not line.endswith(b"\n"):
                break
            raise ValueError(f"corrupt journal: {path}, line {index + 1}")
        if not isinstance(record, dict):
            raise ValueError(f"journal row is not an object: {path}")
        records.append(record)
    return records


def plan(protocol_path, stage, algorithms=None, conflict_request=None):
    protocol = load_json(protocol_path)
    space = protocol["space"]
    configs = [(s, opt) for s in space["blocks"] for opt in space["opts"]]
    if len(configs) != 20 or tuple(space["blocks"]) != (8, 16, 24, 64, 128) or \
            tuple(space["opts"]) != ("O0", "O1", "O2", "O3"):
        raise ValueError("the formal space must contain the teacher's 20 configurations")
    warmup = protocol["measurement"]["warmup"]
    jobs = [] if warmup is None or stage.startswith("conflict_") else [dict(id="warmup-" + stage, action="run", role="warmup",
                 s=warmup["s"], opt=warmup["opt"], repeats=warmup["repeats"], seed=0)]
    if stage.startswith("conflict_"):
        if conflict_request is None:
            raise ValueError("conflict planning requires the derived --conflict-request")
        request = load_json(conflict_request)
        source_stage = stage.removeprefix("conflict_")
        rules = protocol["reference"]["conflict"]
        limit = rules["max_" + source_stage + "_events"]
        if request["protocol_sha256"] != sha256(protocol_path) or request["source_stage"] != source_stage:
            raise ValueError("conflict request belongs to another protocol or stage")
        if len(request["events"]) > limit:
            raise ValueError("conflict request exceeds the predeclared event cap")
        returned = [(e["returned_config"]["s"], e["returned_config"]["opt"]) for e in request["events"]]
        if returned != sorted(set(returned), key=configs.index):
            raise ValueError("conflict events must follow the teacher's canonical space order")
        for event_index, event in enumerate(request["events"]):
            pair = {"returned": event["returned_config"], "reference": event["reference_config"]}
            if any((c["s"], c["opt"]) not in configs for c in pair.values()):
                raise ValueError("conflict configuration is outside the formal space")
            for repeat in range(rules["repeats_per_config"]):
                if pair["returned"] == pair["reference"]:
                    pair["both"] = pair["returned"]
                    order = ("both",)
                else:
                    order = ("returned", "reference") if repeat % 2 == 0 else ("reference", "returned")
                for member in order:
                    jobs.append(dict(id=f"{stage}-e{event_index + 1}-r{repeat + 1}-{member}",
                        action="run", role="reference_conflict", **pair[member], repeats=1,
                        seed=rules["order_seed"] + event_index, event=event_index + 1,
                        member=member, round=repeat + 1))
    elif stage == "reference":
        for round_index in range(protocol["reference"]["rounds"]):
            order = configs.copy()
            seed = protocol["reference"]["order_seed"] + round_index
            random.Random(seed).shuffle(order)
            for s, opt in order:
                jobs.append(dict(id=f"ref-r{round_index + 1}-s{s}-{opt}",
                                 action="run", role="reference", s=s, opt=opt, repeats=1,
                                 seed=seed, round=round_index + 1))
    else:
        online = protocol["online"]
        if stage == "holdout" and algorithms is None:
            raise ValueError("holdout needs the selection decision's explicit --algorithms subset")
        names = list(algorithms or online["algorithms"])
        if len(names) != len(set(names)) or not set(names) <= set(online["algorithms"]):
            raise ValueError("invalid or duplicate algorithm selection")
        if stage == "selection" and names != online["algorithms"]:
            raise ValueError("selection requires all five planned algorithms")
        if stage == "holdout" and "random" not in names:
            raise ValueError("holdout must include the matching random baseline")
        if stage == "holdout" and not set(names) <= {"random", "stratified", "patience"}:
            raise ValueError("holdout only includes Random and selection KEEP candidates")
        seeds = online["seeds"] if stage == "selection" else protocol["holdout"]["seeds"]
        for index, seed in enumerate(seeds):
            offset = ((2 if stage == "selection" else 1) * index) % len(names)
            order = names[offset:] + names[:offset]
            for algorithm in order:
                task_id = f"{stage}-{algorithm}-seed{seed}"
                jobs.append(dict(id=task_id, action="search", role="search", algorithm=algorithm,
                                 budget=online["budget"], repeats=online["repeats"], seed=seed))
                jobs.append(dict(id="confirm-" + task_id, action="run", role="return_confirmation", depends_on=task_id,
                                 repeats=protocol["return_confirmation"]["repeats"], seed=seed))
    framework = P1 / protocol["framework"]["path"]
    target = P1 / protocol["target"]["path"]
    result = dict(schema=1, stage=stage, measurement_root=str(P1.resolve()),
                protocol=str(Path(protocol_path).resolve().relative_to(P1)),
                protocol_sha256=sha256(protocol_path), framework_sha256=sha256(framework),
                target_sha256=sha256(target), driver_sha256=sha256(Path(__file__)), jobs=jobs)
    if conflict_request is not None:
        result["conflict_request"] = dict(path=str(Path(conflict_request).resolve().relative_to(P1)),
                                          sha256=sha256(conflict_request))
    return result


def resolved_config(job, directory):
    if "depends_on" not in job:
        return dict(s=job["s"], opt=job["opt"]) if job["action"] == "run" else None
    parent_path = directory / (job["depends_on"] + ".jsonl")
    if not parent_path.exists():
        return None
    summaries = [r for r in read_records(parent_path) if r["type"] == "summary"]
    if not summaries or not summaries[-1].get("best"):
        return None
    return summaries[-1]["best"]["config"]


def task_status(job, directory, manifest, historical_only=False):
    path = directory / (job["id"] + ".jsonl")
    if not path.exists():
        if "depends_on" in job and resolved_config(job, directory) is None:
            return "blocked"
        return "pending"
    rows = read_records(path)
    if not rows or rows[0].get("type") != "header":
        raise ValueError(f"missing journal header: {path}")
    protocol = load_json(P1 / manifest["protocol"])
    if sha256(P1 / manifest["protocol"]) != manifest["protocol_sha256"]:
        raise ValueError("protocol changed after the experiment was planned")
    if any(manifest[name + "_sha256"] != protocol[name]["sha256"] for name in ("target", "framework")):
        raise ValueError("plan source identities differ from the frozen protocol")
    config = resolved_config(job, directory) if job["action"] == "run" else None
    if job["action"] == "run" and config is None:
        raise ValueError(f"parent search has no valid returned configuration: {job['id']}")
    patience = protocol["strategy_options"]["patience"]
    original_root = Path(manifest["measurement_root"]) if historical_only else P1
    if historical_only and (sha256(P1 / protocol["target"]["path"]) != manifest["target_sha256"] or
                            sha256(P1 / protocol["framework"]["path"]) != manifest["framework_sha256"]):
        raise ValueError("historical analysis sources differ from the recorded target/framework")
    expected = dict(schema=1, framework_sha256=manifest["framework_sha256"],
        target=dict(source=str((original_root / protocol["target"]["path"]).resolve()),
            source_sha256=manifest["target_sha256"], n=protocol["target"]["n"],
            compiler=protocol["target"]["compiler_identity"],
            flags=protocol["target"]["common_flags"],
            compile_timeout=float(protocol["measurement"]["compile_timeout_s"]),
            require_checksum=protocol["target"]["require_checksum"],
            kernel_clock=protocol["measurement"]["clock_health"]["timer"]),
        blocks=protocol["space"]["blocks"] if config is None else [config["s"]],
        opts=protocol["space"]["opts"] if config is None else [config["opt"]],
        action=job["action"], algorithm=job.get("algorithm", "grid"), seed=job["seed"],
        budget=job.get("budget", 1), min_trials=patience["min_trials"], patience=patience["patience"],
        min_relative_improvement=float(patience["min_relative_improvement"]), repeats=job["repeats"],
        timeout=float(protocol["measurement"]["timeout_s"]),
        runtime_affinity=protocol["measurement"]["cpu_affinity"],
        protocol_sha256=manifest["protocol_sha256"],
        cache_dir=str((original_root / protocol["measurement"]["cache_dir"]).resolve()))
    expected_hash = hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(",", ":"),
                                             allow_nan=False).encode()).hexdigest()
    if rows[0].get("metadata") != expected or rows[0].get("fingerprint") != expected_hash:
        raise ValueError(f"journal settings/fingerprint differ from the frozen task: {path}")
    summaries = [r for r in rows if r["type"] == "summary"]
    if not summaries:
        return "partial"
    tolerance = protocol["measurement"]["clock_health"]["kernel_over_process_tolerance_s"]
    for measurement in (r for r in rows if r["type"] == "measurement" and r["status"] == "ok"):
        if measurement["kernel_s"] > measurement["process_wall_s"] + tolerance:
            return "clock_error"
    return "failed" if summaries[-1]["failed_trials"] else "complete"


def command(job, directory, protocol, protocol_path):
    target = P1 / protocol["target"]["path"]
    framework = P1 / protocol["framework"]["path"]
    cpu_list = ",".join(map(str, protocol["measurement"]["cpu_affinity"]))
    argv = ["taskset", "--cpu-list", cpu_list, sys.executable, str(framework), job["action"],
            "--target", str(target), "--compiler", protocol["target"]["compiler"],
            "--blocks", ",".join(map(str, protocol["space"]["blocks"])),
            "--opts", ",".join(protocol["space"]["opts"]),
            "--cache-dir", str((P1 / protocol["measurement"]["cache_dir"]).resolve()),
            "--protocol", str(protocol_path), "--output", str(directory / (job["id"] + ".jsonl")),
            "--repeats", str(job["repeats"]), "--seed", str(job["seed"]),
            "--timeout", str(protocol["measurement"]["timeout_s"]),
            "--compile-timeout", str(protocol["measurement"]["compile_timeout_s"])]
    patience = protocol["strategy_options"]["patience"]
    argv += ["--min-trials", str(patience["min_trials"]), "--patience", str(patience["patience"]),
             "--min-relative-improvement", str(patience["min_relative_improvement"])]
    if job["action"] == "search":
        argv += ["--algorithm", job["algorithm"], "--budget", str(job["budget"])]
    else:
        config = resolved_config(job, directory)
        if config is None:
            raise ValueError(f"parent search has no valid returned configuration: {job['id']}")
        argv += ["--s", str(config["s"]), "--opt", config["opt"]]
    if (directory / (job["id"] + ".jsonl")).exists():
        argv.append("--resume")
    return argv


def check_frozen(protocol, protocol_path, manifest):
    if protocol["state"] != "approved" or not protocol["approval"].get("evidence"):
        raise ValueError("formal experiments require the independently approved protocol")
    if sha256(protocol_path) != manifest["protocol_sha256"]:
        raise ValueError("protocol changed after the experiment was planned")
    if sha256(Path(__file__)) != manifest["driver_sha256"]:
        raise ValueError("the experiment driver changed after the experiment was planned")
    if manifest["measurement_root"] != str(P1.resolve()):
        raise ValueError("execute/resume must use the original measurement directory")
    if "conflict_request" in manifest and \
            sha256(P1 / manifest["conflict_request"]["path"]) != manifest["conflict_request"]["sha256"]:
        raise ValueError("the conflict request changed after it was planned")
    for name in ("target", "framework"):
        current = sha256(P1 / protocol[name]["path"])
        if current != manifest[name + "_sha256"] or current != protocol[name]["sha256"]:
            raise ValueError(f"{name} changed after protocol freeze")
    expected_flags = ["-std=c11", "-Wall", "-Wextra"]
    if protocol["target"]["common_flags"] != expected_flags:
        raise ValueError("runner supports the frozen common flags without extra optimization")
    if protocol["measurement"]["timeout_s"] < 1200:
        raise ValueError("timeout is shorter than the agreed pretest minimum")
    if protocol["measurement"]["clock_health"]["status"] != "resolved":
        raise ValueError("clock inconsistency remains unresolved")
    if protocol["measurement"]["clock_health"]["timer"] != "CLOCK_MONOTONIC" or \
            protocol["target"]["n"] != 4096:
        raise ValueError("the formal clock and matrix size differ from the agreed target")
    if not protocol["pretest_basis"]["completed"]:
        raise ValueError("the new target's pretest is incomplete")
    if protocol["target"]["compiler_identity"] is None or protocol["measurement"]["warmup"] is None:
        raise ValueError("compiler identity or warmup rule has not been frozen")
    identity = protocol["target"]["compiler_identity"]
    compiler = shutil.which(protocol["target"]["compiler"])
    if compiler is None or str(Path(compiler).resolve()) != identity["path"] or \
            sha256(identity["path"]) != identity["sha256"]:
        raise ValueError("the compiler executable differs from the frozen identity")
    if not (P1 / protocol["approval"]["evidence"]).is_file():
        raise ValueError("the independent approval evidence is missing")
    if protocol["measurement"]["clock_health"]["kernel_over_process_tolerance_s"] != 0.005:
        raise ValueError("clock guard differs from the framework's 0.005-second rule")
    for value in (protocol["reference"]["noise_relative_range"],
                  protocol["reference"]["conflict"]["relative_difference"]):
        if value is None or not math.isfinite(value) or not 0 < value < 1:
            raise ValueError("reference noise/conflict thresholds have not been frozen")
    for name in ("epsilon_pct", "quality_gain_pp", "quality_gain_s", "quality_loss_pp", "wall_increase_fraction", "wall_saving_s"):
        value = protocol["acceptance"].get(name)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(f"acceptance criterion must be finite and nonnegative: {name}")
    delta = protocol["strategy_options"]["patience"]["min_relative_improvement"]
    if delta is None or not math.isfinite(delta) or not 0 <= delta < 1:
        raise ValueError("patience improvement threshold has not been frozen")
    for name in ("max_process_runs", "max_wall_s"):
        value = protocol["resources"][name]
        if value is None or not math.isfinite(value) or value <= 0:
            raise ValueError(f"unfrozen resource budget: {name}")


def driver_attempts(events):
    starts, ends = {}, {}
    for row in events:
        if row["type"] == "task_start":
            key = row["attempt_id"]
            if key in starts:
                raise ValueError("duplicate driver attempt ID")
            starts[key] = row
        elif row["type"] in ("task_end", "task_recovery"):
            key = row["attempt_id"]
            if key not in starts or key in ends or row["task"] != starts[key]["task"]:
                raise ValueError("driver completion does not match one unique start")
            ends[key] = row
    return starts, ends


@contextmanager
def experiment_lock():
    path = P1 / ".cache" / "experiment.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("another experiment runner is active") from exc
        yield


def append_event(stream, kind, **fields):
    data = dict(type=kind, at=datetime.now(timezone.utc).isoformat(), **fields)
    stream.write(json.dumps(data, allow_nan=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())
    return data


def stop_child(child):
    try:
        child.send_signal(signal.SIGTERM)
    except ProcessLookupError:
        pass
    child.wait()


def recorded_usage(protocol, protocol_hash):
    runs, wall = 0, 0.0
    for relative in protocol["resources"]["formal_batches"]:
        directory = P1 / relative
        if not (directory / "plan.json").exists():
            continue
        batch = load_json(directory / "plan.json")
        if batch["protocol_sha256"] != protocol_hash:
            raise ValueError(f"formal batch has a different protocol: {directory}")
        has_journal = False
        for job in batch["jobs"]:
            path = directory / (job["id"] + ".jsonl")
            if path.exists():
                has_journal = True
                runs += sum(r["type"] == "measurement_start" for r in read_records(path))
        ledger = directory / "driver.jsonl"
        if ledger.exists():
            events = read_records(ledger)
            data = ledger.read_bytes()
            if len(events) < len(data.splitlines()):
                raise ValueError("the driver ledger has a torn tail; diagnose it with recover before resuming")
            starts, ends = driver_attempts(events)
            if has_journal and not starts:
                raise ValueError("measurement journals exist without driver starts; actual driver cost is unknown")
            if starts.keys() != ends.keys():
                raise ValueError("an unfinished driver needs the recover command after checking its subprocesses")
            for row in ends.values():
                cost = row["driver_wall_s"] if row["type"] == "task_end" else row["resource_wall_upper_s"]
                if cost is None or not math.isfinite(cost) or cost < 0:
                    raise ValueError("invalid driver cost in the resource ledger")
                wall += cost
                if row["type"] == "task_recovery":
                    runs += row["unrecorded_process_run_upper"]
        elif has_journal:
            raise ValueError("the measurement batch is missing its driver cost ledger")
    return runs, wall


def recover(directory, manifest, evidence_path):
    """Account for a hard exit without inventing actual driver time."""
    protocol = load_json(P1 / manifest["protocol"])
    check_frozen(protocol, P1 / manifest["protocol"], manifest)
    if str(directory.relative_to(P1)) not in protocol["resources"]["formal_batches"]:
        raise ValueError("recovery directory is not a registered formal batch")
    with experiment_lock():
        ledger_path = directory / "driver.jsonl"
        events = read_records(ledger_path)
        starts, ends = driver_attempts(events)
        pending = [row for key, row in starts.items() if key not in ends]
        if len(pending) != 1:
            raise ValueError("recovery requires exactly one known unfinished driver attempt")
        start = pending[0]
        if evidence_path is None:
            raise ValueError("hard-exit recovery requires --recovery-evidence after inspecting surviving processes")
        evidence_path = evidence_path.resolve()
        evidence_path.relative_to(P1)
        evidence = load_json(evidence_path)
        if evidence.get("protocol_sha256") != manifest["protocol_sha256"] or \
                evidence.get("task") != start["task"] or evidence.get("attempt_id") != start["attempt_id"] or \
                evidence.get("verified_no_live_processes") is not True or not evidence.get("inspection"):
            raise ValueError("recovery evidence does not identify this attempt and its process inspection")
        inspection_path = (P1 / evidence["inspection"]).resolve()
        inspection_path.relative_to(P1)
        if not inspection_path.is_file():
            raise ValueError("the recovery process-inspection record is missing")
        if start["boot_id"] != Path("/proc/sys/kernel/random/boot_id").read_text().strip():
            raise ValueError("host rebooted; the resource wall upper bound cannot be recovered automatically")
        path = directory / (start["task"] + ".jsonl")
        rows = read_records(path) if path.exists() else []
        new_rows = rows[start["existing_records"]:]
        framework_pids = [r["pid"] for r in events if r["type"] == "task_process" and
                          r["attempt_id"] == start["attempt_id"]]
        for pid in framework_pids:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                continue
            raise ValueError(f"recorded framework PID {pid} is still present; do not resume yet")
        for index, row in enumerate(new_rows):
            if row["type"] not in ("measurement_start", "build_start"):
                continue
            later = new_rows[index + 1:]
            finished = any(r["type"] == "measurement" and r.get("trial_id") == row.get("trial_id") and
                           r.get("repeat") == row.get("repeat") for r in later) if row["type"] == "measurement_start" else \
                any(r["type"] == "build" and r.get("compile", {}).get("pid") == row["pid"] for r in later)
            if not finished:
                try:
                    os.killpg(row["pid"], 0)
                except ProcessLookupError:
                    continue
                raise ValueError(f"recorded subprocess group {row['pid']} is still present; do not resume yet")
        lower = sum(r.get("process_wall_s") or 0 for r in new_rows if r["type"] == "measurement")
        lower += sum(r.get("compile_wall_s") or 0 for r in new_rows if r["type"] == "build")
        upper = time.monotonic() - start["monotonic_s"]
        if upper < lower or not math.isfinite(upper):
            raise ValueError("recovered clock span is shorter than recorded subprocess costs")
        data = ledger_path.read_bytes()
        offset = sum(len(line) for line in data.splitlines(keepends=True)[:len(events)])
        fragment = data[offset:]
        if fragment:
            with ledger_path.open("r+b") as stream:
                stream.truncate(offset)
        elif data and not data.endswith(b"\n"):
            with ledger_path.open("ab") as stream:
                stream.write(b"\n")
        with ledger_path.open("a") as stream:
            if fragment:
                append_event(stream, "driver_tail_recovery", discarded_fragment_hex=fragment.hex(), offset=offset)
            record = append_event(stream, "task_recovery", task=start["task"], attempt_id=start["attempt_id"],
                driver_wall_s=None, driver_wall_recorded_lower_bound_s=lower, resource_wall_upper_s=upper,
                unrecorded_process_run_upper=0 if any(r["type"] == "summary" for r in rows) else 1,
                diagnostic=str(evidence_path.resolve().relative_to(P1)), diagnostic_sha256=sha256(evidence_path),
                inspection_sha256=sha256(inspection_path),
                bound_basis="same-boot monotonic span including downtime; not actual tuning time")
        print(json.dumps(record))


def execute(directory, manifest, max_jobs):
    protocol_path = P1 / manifest["protocol"]
    protocol = load_json(protocol_path)
    check_frozen(protocol, protocol_path, manifest)
    if str(directory.relative_to(P1)) not in protocol["resources"]["formal_batches"]:
        raise ValueError("output directory is not a registered formal batch")
    completed_now = 0
    with experiment_lock():
        with (directory / "driver.jsonl").open("a", encoding="utf-8") as ledger:
            data = (directory / "driver.jsonl").read_bytes()
            if data and not data.endswith(b"\n") and len(read_records(directory / "driver.jsonl")) == len(data.splitlines()):
                ledger.write("\n")
                ledger.flush()
                os.fsync(ledger.fileno())
                append_event(ledger, "driver_newline_recovery", original_size=len(data))
            recorded_usage(protocol, manifest["protocol_sha256"])
            def event(kind, **fields):
                return append_event(ledger, kind, **fields)
            for job in manifest["jobs"]:
                state = task_status(job, directory, manifest)
                if state == "complete":
                    continue
                if state in ("failed", "clock_error"):
                    raise ValueError(f"failed task requires diagnosis, not automatic reruns: {job['id']}")
                if state == "blocked":
                    raise ValueError(f"dependency has no returned configuration: {job['id']}")
                if max_jobs is not None and completed_now >= max_jobs:
                    break
                used_runs, used_wall = recorded_usage(protocol, manifest["protocol_sha256"])
                path = directory / (job["id"] + ".jsonl")
                prior_runs = sum(r["type"] == "measurement_start" for r in read_records(path)) if path.exists() else 0
                job_runs = max(0, job["repeats"] * job.get("budget", 1) - prior_runs)
                if used_runs + job_runs > protocol["resources"]["max_process_runs"] or \
                        used_wall >= protocol["resources"]["max_wall_s"]:
                    raise ValueError("the frozen measurement resource limit has been reached")
                argv = command(job, directory, protocol, protocol_path)
                print(json.dumps(dict(task=job["id"], state=state, command=argv)), flush=True)
                start = time.monotonic()
                attempt_id = sum(r["type"] == "task_start" for r in read_records(directory / "driver.jsonl"))
                existing_records = len(read_records(path)) if path.exists() else 0
                event("task_start", task=job["id"], command=argv, attempt_id=attempt_id,
                      driver_sha256=manifest["driver_sha256"], protocol_sha256=manifest["protocol_sha256"],
                      monotonic_s=start, boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                      existing_records=existing_records)
                with (directory / (job["id"] + ".stdout.txt")).open("a") as out, \
                        (directory / (job["id"] + ".stderr.txt")).open("a") as err:
                    try:
                        child = subprocess.Popen(argv, stdout=out, stderr=err)
                    except OSError as exc:
                        event("task_end", task=job["id"], attempt_id=attempt_id, returncode=None,
                              driver_wall_s=time.monotonic() - start, interrupted=False, spawn_error=str(exc))
                        raise
                    try:
                        event("task_process", task=job["id"], attempt_id=attempt_id, pid=child.pid)
                        code = child.wait(timeout=protocol["resources"]["max_wall_s"] - used_wall)
                    except subprocess.TimeoutExpired:
                        stop_child(child)
                        event("task_end", task=job["id"], attempt_id=attempt_id, returncode=130,
                              driver_wall_s=time.monotonic() - start, interrupted=True,
                              resource_exhausted=True)
                        raise ValueError("the frozen wall-time limit stopped the active task")
                    except KeyboardInterrupt:
                        stop_child(child)
                        event("task_end", task=job["id"], attempt_id=attempt_id, returncode=130,
                              driver_wall_s=time.monotonic() - start, interrupted=True)
                        raise
                    except BaseException:
                        stop_child(child)
                        raise
                event("task_end", task=job["id"], attempt_id=attempt_id, returncode=code,
                      driver_wall_s=time.monotonic() - start, interrupted=False)
                if code or task_status(job, directory, manifest) != "complete":
                    raise ValueError(f"task failed or incomplete: {job['id']}; inspect its logs")
                completed_now += 1
                print(json.dumps(dict(task=job["id"], state="complete")), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "status", "execute", "resume", "recover"))
    parser.add_argument("--protocol", type=Path, default=P1 / "evidence" / "protocol_v1.json")
    parser.add_argument("--stage", choices=("reference", "selection", "holdout", "conflict_selection", "conflict_holdout"),
                        default="selection")
    parser.add_argument("--algorithms", help="comma-separated holdout algorithms; random is required")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-jobs", type=int)
    parser.add_argument("--recovery-evidence", type=Path,
                        help="JSON identifying the hard-exit attempt and a preserved process-inspection record")
    parser.add_argument("--conflict-request", type=Path, help="derived conflict request, never an edited score table")
    args = parser.parse_args(argv)
    try:
        if args.max_jobs is not None and args.max_jobs < 0:
            raise ValueError("max-jobs must be nonnegative")
        directory = args.output_dir.resolve()
        manifest_path = directory / "plan.json"
        if args.action == "plan":
            manifest = plan(args.protocol, args.stage,
                            args.algorithms.split(",") if args.algorithms else None, args.conflict_request)
            directory.mkdir(parents=True, exist_ok=True)
            if manifest_path.exists() and load_json(manifest_path) != manifest:
                raise ValueError("existing plan differs; preserve it and use a new batch directory")
            if not manifest_path.exists():
                manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
            print(json.dumps(dict(plan=str(manifest_path), stage=args.stage, tasks=len(manifest["jobs"]))))
        else:
            manifest = load_json(manifest_path)
            if args.action == "status":
                states = [dict(task=job["id"], state=task_status(job, directory, manifest))
                          for job in manifest["jobs"]]
                print(json.dumps(dict(stage=manifest["stage"], tasks=states), indent=2))
            elif args.action == "recover":
                recover(directory, manifest, args.recovery_evidence)
            else:
                def interrupt(signum, frame):
                    raise KeyboardInterrupt
                previous = signal.signal(signal.SIGTERM, interrupt)
                try:
                    execute(directory, manifest, args.max_jobs)
                finally:
                    signal.signal(signal.SIGTERM, previous)
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        print("interrupted; use resume after checking recorded subprocesses", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
