#!/usr/bin/env python3
"""Serial Goal 2 jobs, common return panels, and one cumulative resource ledger."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import random
import signal
import statistics
import subprocess
import sys
import time
import uuid

from experiment import load_json, read_records, sha256

P1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P1 / "src"))
import autotuner as at

CLOCKS = {"monotonic": time.CLOCK_MONOTONIC,
          "raw": time.CLOCK_MONOTONIC_RAW, "realtime": time.CLOCK_REALTIME}
LEDGER = P1 / "evidence/measurement/resource_ledger.jsonl"
MAX_CALLS, MAX_SECONDS = 520, 16 * 3600


def clocks():
    return {name: time.clock_gettime_ns(clock) for name, clock in CLOCKS.items()}


def elapsed(start, end):
    values = {name: (end[name] - start[name]) / 1e9 for name in CLOCKS}
    if any(not math.isfinite(x) or x < 0 for x in values.values()):
        raise ValueError("a resource clock went backwards; inspect the saved boundaries")
    return values


def append(path, kind, **fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = dict(type=kind, at=at.now(), **fields)
    with path.open("a", encoding="utf-8") as out:
        out.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        out.flush()
        os.fsync(out.fileno())
    return row


@contextmanager
def performance_lock(path=None):
    path = Path(path) if path else P1 / ".cache/performance.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("another P1 performance/test owner holds the lock") from error
        yield


def usage(ledger=LEDGER):
    rows = read_records(ledger) if Path(ledger).exists() else []
    starts, ends = {}, {}
    for row in rows:
        if row["type"] == "task_start":
            if row["attempt_id"] in starts:
                raise ValueError("duplicate resource attempt")
            starts[row["attempt_id"]] = row
        elif row["type"] == "task_end":
            key = row["attempt_id"]
            if key not in starts or key in ends:
                raise ValueError("resource end has no unique start")
            if row["task"] != starts[key]["task"]:
                raise ValueError("resource task identity changed")
            ends[key] = row
    if starts.keys() != ends.keys():
        raise ValueError("unfinished resource attempt: inspect owned PIDs and recover explicitly")
    for key,row in ends.items():
        resource_span(starts[key],row)
    journals={s["journal"] for s in starts.values() if s.get("journal")}
    for journal in journals:
        members=[key for key,s in starts.items() if s.get("journal")==journal]
        recorded=sum(r["type"]=="measurement_start" for r in read_records(P1/journal))
        charged=sum(ends[key]["n4096_calls"] for key in members)
        known=all(ends[key].get("n4096_calls_known",True) for key in members)
        if known and recorded!=charged or not known and recorded>charged:
            raise ValueError("resource target calls differ from physical journal starts")
    calls = sum(row["n4096_calls"] for row in ends.values())
    cost = sum(row["resource_s"] for row in ends.values())
    if any(type(row["n4096_calls"]) is not int or row["n4096_calls"] < 0 or
           not math.isfinite(row["resource_s"]) or row["resource_s"] < 0 for row in ends.values()):
        raise ValueError("invalid cumulative resource cost")
    return calls, cost


def resource_span(start, end):
    begin,finish=start["clock_start_ns"],end["clock_end_ns"]
    if set(begin)!=set(CLOCKS) or set(finish)!=set(CLOCKS) or \
            any(type(v) is not int for v in [*begin.values(),*finish.values()]):
        raise ValueError("resource boundaries must be three integer nanosecond domains")
    spans=elapsed(begin,finish)
    if end["resource_s"]!=max(spans.values()) or end.get("resource_wall_s")!=max(spans.values()):
        raise ValueError("charged resource duration differs from its raw boundaries")
    if end.get("n4096_calls_known",True):
        if end.get("clock_elapsed_s")!=spans or end.get("driver_wall_s")!=spans["monotonic"]:
            raise ValueError("known driver clock fields differ from raw boundaries")
    elif end.get("driver_wall_s") is not None or end.get("clock_elapsed_s") is not None or \
            end.get("resource_bound_basis")!="same-boot multi-domain span including downtime":
        raise ValueError("unknown recovered cost must retain its explicit conservative bound")
    return spans


def recover_resource(evidence_path, ledger=LEDGER):
    """Same-boot upper-bound recovery; never invent the lost driver duration."""
    evidence=load_json(evidence_path)
    rows=read_records(ledger)
    ended={r["attempt_id"] for r in rows if r["type"]=="task_end"}
    pending=[r for r in rows if r["type"]=="task_start" and r["attempt_id"] not in ended]
    if len(pending)!=1:
        raise ValueError("recovery requires one unfinished resource attempt")
    start=pending[0]
    inspection=(P1/evidence.get("inspection","")).resolve()
    inspection.relative_to(P1)
    if evidence.get("attempt_id")!=start["attempt_id"] or evidence.get("verified_no_live_processes") is not True or not inspection.is_file():
        raise ValueError("matching explicit process-inspection evidence is required")
    if start["boot_id"]!=Path("/proc/sys/kernel/random/boot_id").read_text().strip():
        raise ValueError("cross-boot resource duration is unknown; cannot recover automatically")
    journal=P1/start["journal"] if start.get("journal") else None
    journal_rows=read_records(journal) if journal and journal.exists() else []
    pids=[r["pid"] for r in rows if r["type"]=="task_process" and r["attempt_id"]==start["attempt_id"]]
    pids.extend(r["pid"] for r in journal_rows if r["type"] in ("measurement_start","build_start"))
    for pid in pids:
        try:
            os.kill(pid,0)
        except ProcessLookupError:
            continue
        raise ValueError("recorded PID is present; no automatic killing during recovery")
    after=clocks()
    spans=elapsed(start["clock_start_ns"],after)
    recorded=sum(r["type"]=="measurement_start" for r in journal_rows)-start["prior_measurement_starts"]
    complete=any(r["type"]=="summary" for r in journal_rows)
    calls=min(start["call_upper"],max(0,recorded)+(0 if complete else 1)) if journal else start["call_upper"]
    return append(ledger,"task_end",task=start["task"],role=start["role"],attempt_id=start["attempt_id"],
        returncode=None,reason="hard-exit recovery; actual cost unknown",n4096_calls=calls,
        driver_wall_s=None,clock_elapsed_s=None,clock_end_ns=after,
        n4096_calls_known=False,n4096_call_recorded_lower=max(0,recorded),
        resource_s=max(spans.values()),resource_wall_s=max(spans.values()),
        resource_bound_basis="same-boot multi-domain span including downtime",
        inspection_sha256=sha256(inspection),evidence_sha256=sha256(evidence_path))


def stop(child):
    if child.poll() is None:
        try:
            os.killpg(child.pid,signal.SIGTERM)
        except ProcessLookupError:
            child.wait()
            return
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()


def cleanup_recorded_children(journal):
    """Only stop our uncompleted, command-verified subprocess group leaders."""
    if journal is None or not Path(journal).exists():
        return
    rows = read_records(journal)
    completed = {r.get("pid") for r in rows if r["type"] == "measurement"}
    completed.update(r.get("compile", {}).get("pid") for r in rows if r["type"] == "build")
    for row in rows:
        if row["type"] not in ("measurement_start", "build_start") or row["pid"] in completed:
            continue
        pid = row["pid"]
        try:
            cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
            command = [part.decode() for part in cmdline if part]
            if command != row["command"] or os.getpgid(pid) != pid:
                raise ValueError(f"recorded PID {pid} no longer has our exact command/group; do not kill it")
            os.killpg(pid, signal.SIGKILL)
            for attempt in range(20):
                try:
                    state=Path(f"/proc/{pid}/stat").read_text().split(")",1)[1].split()[0]
                except FileNotFoundError:
                    break
                if state=="Z":
                    break
                time.sleep(.05)
            else:
                raise ValueError("owned subprocess remained active after SIGKILL")
        except FileNotFoundError:
            pass
        except ProcessLookupError:
            pass


def matrix_clock_baselines(rows,boot_id):
    starts={r["attempt_id"]:r for r in rows if r["type"]=="task_start"}
    return [r["clock_elapsed_s"]["raw"]/r["driver_wall_s"] for r in rows
        if r["type"]=="task_end" and (r.get("driver_wall_s") or 0)>=10 and
        r.get("n4096_calls",0)>0 and r.get("clock_elapsed_s") and
        r.get("returncode")==0 and r.get("reason") is None and
        r.get("n4096_calls_known",True) and
        starts[r["attempt_id"]]["boot_id"]==boot_id]


def measurement_key(row):
    return row["run_id"], row["trial_id"], row["repeat"], row["pid"]


def attempt_measurements(rows, offset, count, complete=False):
    all_starts=[r for r in rows if r["type"]=="measurement_start"]
    if len({measurement_key(r) for r in all_starts})!=len(all_starts):
        raise ValueError("duplicate physical target process start")
    starts=all_starts[offset:offset+count]
    keys={measurement_key(r) for r in starts}
    results=[r for r in rows if r["type"]=="measurement" and measurement_key(r) in keys]
    if len(starts)!=count or len(keys)!=len(starts) or len({measurement_key(r) for r in results})!=len(results):
        raise ValueError("attempt has missing or duplicate target process identities")
    if complete and len(results)!=count:
        raise ValueError("completed attempt is missing target process clock boundaries")
    return results


def process_clock_span(row):
    names=["CLOCK_MONOTONIC","CLOCK_MONOTONIC_RAW","CLOCK_REALTIME"]
    if row.get("status")!="ok" or row.get("returncode")!=0 or row.get("clock_unit")!="ns" or \
            row.get("clock_read_order")!=names or row.get("process_wall_clock")!="CLOCK_MONOTONIC":
        raise ValueError("complete process clock check requires valid target units/domain")
    begin,end=row["clock_start_ns"],row["clock_end_ns"]
    if set(begin)!=set(names) or set(end)!=set(names) or any(type(v) is not int for v in [*begin.values(),*end.values()]):
        raise ValueError("target clock boundaries must be three integer nanosecond domains")
    spans=elapsed(dict(zip(CLOCKS,(begin[n] for n in names))),dict(zip(CLOCKS,(end[n] for n in names))))
    if min(spans.values())<=0 or row["clock_deltas_s"]!={n:spans[k] for n,k in zip(names,CLOCKS)} or \
            row["process_wall_s"]!=spans["monotonic"]:
        raise ValueError("target clock deltas differ from raw boundaries")
    return spans


def complete_clock_check(source, identity, spans, baselines):
    if set(spans)!=set(CLOCKS) or any(not math.isfinite(v) or v<=0 for v in spans.values()) or \
            any(not math.isfinite(r["q"]) or r["q"]<=0 for r in baselines):
        raise ValueError("complete interval must have positive clock durations")
    q=spans["raw"]/spans["monotonic"]
    # Keep first and previous explicitly, even when they refer to the same run.
    refs=baselines[:1]+baselines[-1:] if baselines else []
    return dict(source=source,identity=identity,clock_elapsed_s=spans,q=q,baselines=refs,
                conflict=any(abs(q/ref["q"]-1)>.02 for ref in refs))


class CompleteClockGuard:
    """Compare whole intervals by source; prefix samples never gate formal runs."""
    def __init__(self, previous, boot_id, journal, offset):
        self.boot_id,self.journal,self.offset=boot_id,Path(journal),offset
        self.process_baselines,self.driver_baselines=[],[]
        self.checks,self.seen=[],set()
        self.error=None
        starts={r["attempt_id"]:r for r in previous if r["type"]=="task_start"}
        for end in (r for r in previous if r["type"]=="task_end"):
            start=starts[end["attempt_id"]]
            if start["boot_id"]!=boot_id or end.get("returncode")!=0 or end.get("reason") is not None or \
                    not end.get("n4096_calls_known",True) or not end.get("n4096_calls") or end.get("clock_conflict"):
                continue
            driver_spans=resource_span(start,end)
            if (end.get("driver_wall_s") or 0)>=10 and end.get("clock_elapsed_s"):
                self.driver_baselines.append(dict(identity=end["attempt_id"],q=driver_spans["raw"]/driver_spans["monotonic"]))
            if start.get("journal"):
                rows=read_records(P1/start["journal"])
                for row in attempt_measurements(rows,start["prior_measurement_starts"],end["n4096_calls"],complete=True):
                    spans=process_clock_span(row)
                    if spans["monotonic"]>=10:
                        self.process_baselines.append(dict(identity=list(measurement_key(row)),attempt_id=end["attempt_id"],
                            q=spans["raw"]/spans["monotonic"]))

    def inspect(self, rows, attempt):
        count=sum(r["type"]=="measurement_start" for r in rows)-self.offset
        for row in attempt_measurements(rows,self.offset,count):
            key=measurement_key(row)
            if key in self.seen:
                continue
            check=complete_clock_check("target_process",list(key),process_clock_span(row),self.process_baselines)
            self.checks.append(check)
            self.seen.add(key)
            if check["conflict"]:
                self.error="complete target process RAW/MONOTONIC changed >2% relative to first or previous"
                return False
            if check["clock_elapsed_s"]["monotonic"]>=10:
                self.process_baselines.append(dict(identity=list(key),attempt_id=attempt,q=check["q"]))
        return True

    def poll(self, attempt):
        if not self.journal.exists():
            return True
        # A running writer may have only flushed part of its final JSON line.
        lines=self.journal.read_bytes().splitlines(keepends=True)
        rows=[json.loads(line) for line in lines if line.endswith(b"\n")]
        return self.inspect(rows,attempt)

    def finish(self, rows, attempt, spans, calls):
        try:
            self.inspect(rows,attempt)
            attempt_measurements(rows,self.offset,calls,complete=True)
            driver=complete_clock_check("driver",attempt,spans,self.driver_baselines)
            if driver["conflict"] and self.error is None:
                self.error="complete driver RAW/MONOTONIC changed >2% relative to first or previous"
            complete=len(self.checks)==calls
            if not complete and self.error is None:
                self.error="complete clock checks do not cover all actual target calls"
        except (ValueError,KeyError,TypeError) as error:
            self.error=str(error)
            driver=None
            complete=False
        conflict=any(c["conflict"] for c in self.checks) or bool(driver and driver["conflict"])
        return dict(clock_conflict=conflict,clock_guard=dict(schema=1,mode="complete_target_and_driver",
            threshold_fraction=.02,boot_id=self.boot_id,process_checks=self.checks,driver_check=driver,
            complete=complete,error=self.error))


def validate_complete_clock_record(record, ledger_rows, journal_rows, journal_path):
    matches=[(i,r) for i,r in enumerate(ledger_rows) if r["type"]=="task_end" and r["attempt_id"]==record["attempt_id"]]
    if len(matches)!=1:
        raise ValueError("formal clock record lacks its unique primary resource end")
    index,end=matches[0]
    fields=lambda r:{k:v for k,v in r.items() if k not in ("type","at")}
    if fields(end)!=fields(record) or end.get("returncode")!=0 or end.get("reason") is not None or \
            end.get("n4096_calls_known") is not True:
        raise ValueError("formal batch clock record differs from its valid primary end")
    starts=[r for r in ledger_rows[:index] if r["type"]=="task_start" and r["attempt_id"]==end["attempt_id"]]
    if len(starts)!=1 or starts[0]["task"]!=end["task"] or \
            starts[0].get("journal")!=str(Path(journal_path).resolve().relative_to(P1)):
        raise ValueError("formal resource start does not identify this task journal")
    start=starts[0]
    spans=resource_span(start,end)
    count=start["prior_measurement_starts"]+end["n4096_calls"]
    keys={measurement_key(r) for r in [r for r in journal_rows if r["type"]=="measurement_start"][:count]}
    prefix=[r for r in journal_rows if r["type"] not in ("measurement_start","measurement") or measurement_key(r) in keys]
    guard=CompleteClockGuard(ledger_rows[:index],start["boot_id"],journal_path,start["prior_measurement_starts"])
    expected=guard.finish(prefix,end["attempt_id"],spans,end["n4096_calls"])
    if end.get("clock_conflict") is not False or expected["clock_conflict"] or \
            expected["clock_guard"]["complete"] is not True or expected["clock_guard"]["error"] is not None or \
            end.get("clock_guard")!=expected["clock_guard"]:
        raise ValueError("formal clock fields lack exact raw source/identity/check coverage")
    return True


def controlled(command, directory, task, role, call_upper=0, journal=None,
               direct_calls=None, ledger=LEDGER, time_limit=None, diagnostic_observer=None,
               complete_clock_guard=False):
    """Caller holds the performance lock. Unknown starts block future work."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    used_calls, used_s = usage(ledger)
    if used_calls + call_upper > MAX_CALLS or used_s >= MAX_SECONDS:
        raise ValueError("Goal 2 resource cap reached before starting this task")
    remaining = MAX_SECONDS - used_s
    if time_limit is not None:
        remaining = min(remaining, time_limit)
    stdout, stderr = directory / (task + ".stdout.txt"), directory / (task + ".stderr.txt")
    if journal is None and (stdout.exists() or stderr.exists()):
        raise ValueError("direct-task output exists; inspect it instead of appending a rerun")
    prior = read_records(journal) if journal and Path(journal).exists() else []
    prior_count = sum(r["type"] == "measurement_start" for r in prior)
    attempt = uuid.uuid4().hex
    before = clocks()
    previous_rows = read_records(ledger) if Path(ledger).exists() else []
    boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    clock_baselines=matrix_clock_baselines(previous_rows,boot_id)
    argv = list(map(str, command))
    if diagnostic_observer is not None:
        diagnostic_observer.validate(task, argv, call_upper, journal)
    if complete_clock_guard and (journal is None or diagnostic_observer is not None):
        raise ValueError("formal complete-clock guard needs a target journal and no diagnostic observer")
    guard=CompleteClockGuard(previous_rows,boot_id,journal,prior_count) if complete_clock_guard else None
    append(ledger, "task_start", task=task, role=role, command=argv,
           attempt_id=attempt, clock_start_ns=before, call_upper=call_upper,
           journal=str(Path(journal).resolve().relative_to(P1)) if journal else None,
           prior_measurement_starts=prior_count,
           boot_id=boot_id)
    child, code, reason = None, None, None
    try:
        if diagnostic_observer is not None:
            diagnostic_observer.sample("start", before, clock_baselines)
        with stdout.open("a") as out, stderr.open("a") as err:
            child = subprocess.Popen(argv, stdout=out, stderr=err, start_new_session=True)
            append(ledger, "task_process", task=task, attempt_id=attempt, pid=child.pid)
            while child.poll() is None:
                current = clocks()
                spans = elapsed(before, current)
                if diagnostic_observer is not None:
                    diagnostic_observer.sample("interval", current, clock_baselines)
                if guard is not None and not guard.poll(attempt):
                    reason=guard.error
                    stop(child)
                    cleanup_recorded_children(journal)
                    break
                if guard is None and diagnostic_observer is None and call_upper>0 and spans["monotonic"] >= 10 and clock_baselines and any(
                        abs((spans["raw"] / spans["monotonic"]) / baseline - 1) > .02
                        for baseline in (clock_baselines[0], clock_baselines[-1])):
                    reason = "RAW/MONOTONIC changed >2% relative to first or previous long interval"
                    stop(child)
                    cleanup_recorded_children(journal)
                    break
                if max(spans.values()) >= remaining:
                    reason = "resource_or_task_timeout"
                    stop(child)
                    cleanup_recorded_children(journal)
                    break
                time.sleep(0.25)
            code = child.wait()
            if code:
                cleanup_recorded_children(journal)
                try:
                    os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
    except BaseException as error:
        reason = type(error).__name__ + ": " + str(error)
        if child is not None:
            stop(child)
            cleanup_recorded_children(journal)
            code = child.returncode
        raise
    finally:
        after = clocks()
        try:
            spans = elapsed(before, after)
        except ValueError:
            append(ledger, "clock_error", task=task, attempt_id=attempt,
                   clock_end_ns=after, actual_cost_unknown=True)
            raise
        rows = read_records(journal) if journal and Path(journal).exists() else []
        calls = sum(r["type"] == "measurement_start" for r in rows) - prior_count if journal else (
            direct_calls if child is not None and direct_calls is not None else 0)
        # A task with no target journal has an explicit known direct-process count.
        if calls > call_upper:
            reason = "actual calls exceeded the reserved upper bound"
        observation = {}
        if guard is not None:
            observation=guard.finish(rows,attempt,spans,calls)
            if guard.error:
                reason=reason or guard.error
        if diagnostic_observer is not None:
            try:
                observation = diagnostic_observer.finish(after, rows, stdout, code, clock_baselines)
            except Exception as error:
                reason = "diagnostic observation failed: " + str(error)
        record = append(ledger, "task_end", task=task, role=role, attempt_id=attempt,
            returncode=code, reason=reason, n4096_calls=calls,n4096_calls_known=True,
            driver_wall_s=spans["monotonic"], clock_elapsed_s=spans,
            clock_end_ns=after, resource_s=max(spans.values()), resource_wall_s=max(spans.values()),
            clock_ratio_baselines=clock_baselines[:1]+clock_baselines[-1:] if clock_baselines else [],
            stdout=str(stdout.resolve().relative_to(P1)), stderr=str(stderr.resolve().relative_to(P1)),
            **observation)
    if reason or code:
        raise ValueError(f"task {task} failed ({reason or code}); inspect its raw output")
    return record


def common_metadata(protocol, job, root=P1):
    target, measurement = protocol["target"], protocol["measurement"]
    config = job.get("config")
    expected = dict(schema=1, framework_sha256=protocol["framework"]["sha256"],
        target=dict(source=str((root / target["path"]).resolve()),
            source_sha256=target["sha256"], n=target["n"], compiler=target["compiler_identity"],
            flags=target["common_flags"], compile_timeout=float(measurement["compile_timeout_s"]),
            require_checksum=True, kernel_clock="CLOCK_MONOTONIC"),
        blocks=protocol["space"]["blocks"] if config is None else [config["s"]],
        opts=protocol["space"]["opts"] if config is None else [config["opt"]],
        action=job["action"], algorithm=job.get("algorithm", "grid"), seed=job.get("seed", 0),
        budget=job.get("budget", 1), min_trials=5, patience=3, min_relative_improvement=0.0,
        repeats=job.get("repeats", 1), timeout=float(measurement["timeout_s"]),
        runtime_affinity=measurement["cpu_affinity"], protocol_sha256=protocol["protocol_sha256"],
        cache_dir=str((root / measurement["cache_dir"]).resolve()))
    if job.get("algorithm") == "recheck":
        expected.update(schema=2, recheck=dict(exploration_trials=min(20,job["budget"]-2),
            finalist_limit=2, rechecks_per_finalist=1, return_rule="successful_finalists_only",
            score="median_of_online_samples", tie_rule="random_visit_order"))
    if job.get("start"):
        expected.update(schema=2, greedy_start=job["start"])
    return expected


def validate_task(job, directory, protocol, historical=False):
    path = Path(directory) / (job["id"] + ".jsonl")
    if not path.exists():
        return "pending"
    rows = read_records(path)
    root = Path(protocol["measurement_root"]) if historical else P1
    expected = common_metadata(protocol, job, root)
    if not rows or rows[0].get("metadata") != expected or rows[0].get("fingerprint") != at.fingerprint(expected):
        raise ValueError(f"task settings/identity mismatch: {path}")
    summary = next((r for r in reversed(rows) if r["type"] == "summary"), None)
    if not summary:
        return "partial"
    validate_trace(rows, expected, job)
    for row in (r for r in rows if r["type"] == "measurement"):
        if row["status"] != "ok" or row["returncode"] != 0 or at.TargetProgram.parse(row["stdout"]) != row["kernel_s"]:
            raise ValueError(f"invalid measurement hidden by summary: {path}")
        if row.get("process_wall_clock") != "CLOCK_MONOTONIC" or row["kernel_s"] > row["process_wall_s"] + .005:
            raise ValueError(f"invalid same-domain time guard: {path}")
    if protocol["measurement"].get("clock_health",{}).get("guard")=="completed_per_target_process_and_driver_first_and_previous_same_boot":
        ledger=Path(directory)/"driver.jsonl"
        attempts=[r for r in read_records(ledger) if r["type"]=="task_end" and r["task"]==job["id"]] if ledger.exists() else []
        if not attempts or sum(r["n4096_calls"] for r in attempts)!=summary["process_runs"]:
            raise ValueError("formal summary lacks its complete clock/resource attempt coverage")
        for record in attempts:
            guard=record.get("clock_guard",{})
            if record.get("clock_conflict") is not False or record.get("returncode")!=0 or record.get("reason") is not None or \
                    guard.get("schema")!=1 or guard.get("mode")!="complete_target_and_driver" or \
                    guard.get("complete") is not True or guard.get("error") is not None:
                raise ValueError("formal summary belongs to a failed or incomplete clock check")
            validate_complete_clock_record(record,read_records(LEDGER),rows,path)
    return "failed" if summary["failed_trials"] else "complete"


def validate_trace(rows, metadata, job):
    """Rebuild feedback, candidate eligibility, and counters from real completions."""
    if any(row.get("run_id") != rows[0]["run_id"] for row in rows):
        raise ValueError("journal mixes different run identities")
    space = at.ConfigSpace(metadata["blocks"], metadata["opts"])
    strategy = at.SearchStrategy(metadata["algorithm"], space, metadata["seed"],
        budget=metadata["budget"], start=at.Config(**job["start"]) if job.get("start") else None)
    starts, process_starts, completions, builds = {}, {}, {}, {}
    best, trials = None, []
    for row in rows:
        kind = row["type"]
        if kind == "trial_start":
            t = row["trial_id"]
            proposed=strategy.suggest()
            if t in starts or t != len(starts) or proposed is None or row["config"] != at.asdict(proposed):
                raise ValueError("trial does not follow the frozen algorithm trajectory")
            starts[t] = row
        elif kind == "build":
            t, config = row["trial_id"], row["config"]
            flags = [*metadata["target"]["flags"], "-"+config["opt"]]
            identity = dict(metadata["target"], flags=flags)
            if t not in starts or config != starts[t]["config"] or row["flags"] != flags or \
                    row["source_sha256"] != metadata["target"]["source_sha256"] or \
                    row["compiler"] != metadata["target"]["compiler"] or row["build_key"] != at.fingerprint(identity):
                raise ValueError("build identity differs from frozen source/compiler/flags")
            builds[t] = row
        elif kind in ("measurement_start", "measurement"):
            key = row["trial_id"], row["repeat"]
            if key[0] not in starts or row["config"] != starts[key[0]]["config"] or \
                    type(key[1]) is not int or not 0 <= key[1] < metadata["repeats"]:
                raise ValueError("measurement has no matching trial and repeat")
            if kind == "measurement_start":
                if key in process_starts or key in completions or not row["spawned"]:
                    raise ValueError("duplicate measurement start")
                process_starts[key] = row
            else:
                if key in completions or row["spawned"] != (key in process_starts):
                    raise ValueError("duplicate or unpaired measurement completion")
                if key in process_starts and (row["command"] != process_starts[key]["command"] or
                        row.get("pid") != process_starts[key].get("pid")) and row["status"] != "interrupted":
                    raise ValueError("measurement command/PID differs from its start")
                if row["status"] == "ok":
                    b = builds[key[0]]
                    if row["command"] != [b["binary"],str(row["config"]["s"])] or \
                            row["binary_sha256"] != b["binary_sha256"] or row["build_key"] != b["build_key"]:
                        raise ValueError("measurement does not use its recorded build")
                    if at.TargetProgram.parse(row["stdout"]) != row["kernel_s"] or \
                            at.TargetProgram.checksum(row["stdout"]) != row["checksum"] or \
                            row["returncode"] != 0 or row["checksum"] is None:
                        raise ValueError("parsed output differs from raw target output")
                    clock_names=["CLOCK_MONOTONIC","CLOCK_MONOTONIC_RAW","CLOCK_REALTIME"]
                    if row.get("kernel_clock") != metadata["target"]["kernel_clock"] or \
                            row.get("kernel_unit") != "s" or \
                            row.get("process_wall_clock") != "CLOCK_MONOTONIC" or row.get("clock_unit") != "ns" or \
                            row.get("clock_read_order") != clock_names or \
                            row.get("boundary_read_order") != dict(start=[*clock_names,"RUSAGE_CHILDREN"],
                                end=["RUSAGE_CHILDREN",*clock_names]):
                        raise ValueError("unknown target time units/domain")
                    for boundary in ("clock_start_ns","clock_end_ns"):
                        values=row.get(boundary,{})
                        if set(values)!=set(clock_names) or any(type(v) is not int for v in values.values()):
                            raise ValueError("clock boundaries must be three exact integer nanosecond domains")
                    deltas = {n:(row["clock_end_ns"][n]-v)/1e9 for n,v in row["clock_start_ns"].items()}
                    if deltas != row["clock_deltas_s"] or any(v < 0 or not math.isfinite(v) for v in deltas.values()) or \
                            row["process_wall_s"] != deltas["CLOCK_MONOTONIC"] or \
                            row["kernel_s"] > row["process_wall_s"]+.005:
                        raise ValueError("clock fields or same-domain guard are invalid")
                completions[key] = row
        elif kind == "trial":
            t = row["trial_id"]
            if t != len(trials) or t not in starts or row["config"] != starts[t]["config"]:
                raise ValueError("duplicate/out-of-order trial completion")
            samples = [completions[(t,r)]["kernel_s"] for r in range(metadata["repeats"])
                if (t,r) in completions and completions[(t,r)]["status"] == "ok"]
            fresh = statistics.median(samples) if len(samples)==metadata["repeats"] else None
            if row["samples"] != samples or row["status"] != ("ok" if fresh is not None else "failed"):
                raise ValueError("trial score samples/validity differ from raw completions")
            c = at.Config(**row["config"])
            if strategy.name == "recheck":
                phase = "recheck" if c in strategy.first_scores else "explore"
                strategy.observe(c,fresh)
                if row["fresh_score"] != fresh or row["score"] != strategy.scores[c] or row["phase"] != phase or \
                        row["config_samples"] != strategy.config_samples[c] or \
                        row["return_eligible"] != (c in strategy.rechecked and strategy.scores[c] is not None) or \
                        row["finalists"] != ([at.asdict(c) for c in strategy.finalists] if strategy.finalists is not None else None):
                    raise ValueError("recheck feedback/eligibility was not derived from online samples")
                best = strategy.best()
            else:
                if row["score"] != fresh:
                    raise ValueError("base score differs from online samples")
                strategy.observe(c,fresh)
                if fresh is not None and (best is None or fresh < best["score"]):
                    best = dict(config=row["config"],score=fresh)
            if row["best_so_far"] != best:
                raise ValueError("online best was changed or backfilled")
            trials.append(row)
    if process_starts.keys() != {key for key,row in completions.items() if row["spawned"]}:
        raise ValueError("finished journal hides an unfinished target process")
    summary = rows[-1]
    if summary["type"] != "summary" or len(trials)>metadata["budget"]:
        raise ValueError("summary missing or search exceeded its budget")
    final_best = strategy.best(require_review=True) if strategy.name == "recheck" else best
    counts = dict(proposals=len(starts),attempted_trials=len(trials),
        completed_configs=sum(r["status"]=="ok" for r in trials),
        distinct_configs=len({at.Config(**r["config"]) for r in trials}),
        process_runs=sum(r["spawned"] for r in completions.values()),
        failed_trials=sum(r["status"]!="ok" for r in trials),
        failed_runs=sum(r["status"]!="ok" for r in completions.values()),
        interrupted_runs=sum(r["status"]=="interrupted" for r in completions.values()),
        compile_processes=sum(r["type"]=="build_start" for r in rows),best=final_best)
    if any(summary[key]!=value for key,value in counts.items()):
        raise ValueError("summary identity/counters/best differ from actual online events")
    if len(trials) < metadata["budget"] and strategy.suggest() is not None:
        raise ValueError("summary stopped before its algorithm or budget allowed")


def command(job, directory, protocol, protocol_path):
    argv = ["taskset", "-c", ",".join(map(str, protocol["measurement"]["cpu_affinity"])),
        sys.executable, "-B", str(P1 / protocol["framework"]["path"]), job["action"],
        "--target", str(P1 / protocol["target"]["path"]), "--compiler", protocol["target"]["compiler"],
        "--cache-dir", str(P1 / protocol["measurement"]["cache_dir"]),
        "--protocol", str(protocol_path), "--output", str(Path(directory) / (job["id"] + ".jsonl")),
        "--repeats", str(job.get("repeats", 1)), "--seed", str(job.get("seed", 0)),
        "--timeout", str(protocol["measurement"]["timeout_s"]),
        "--compile-timeout", str(protocol["measurement"]["compile_timeout_s"])]
    if job["action"] == "search":
        argv += ["--algorithm", job["algorithm"], "--budget", str(job["budget"])]
        if job.get("start"):
            argv += ["--start-s", str(job["start"]["s"]), "--start-opt", job["start"]["opt"]]
    else:
        argv += ["--s", str(job["config"]["s"]), "--opt", job["config"]["opt"]]
    if (Path(directory) / (job["id"] + ".jsonl")).exists():
        argv.append("--resume")
    return argv


def freeze_check(protocol, manifest, protocol_path, execute=False):
    if sha256(protocol_path) != manifest["protocol_sha256"]:
        raise ValueError("protocol changed after planning")
    if sha256(__file__)!=manifest["driver_sha256"]:
        raise ValueError("driver source differs from the frozen batch")
    if protocol["target"]["n"]!=4096 or protocol["target"]["common_flags"]!=list(at.COMMON_FLAGS) or \
            protocol["space"]!=dict(blocks=list(at.BLOCKS),opts=list(at.OPTS)) or \
            protocol["measurement"]["cpu_affinity"]!=[0] or \
            protocol["measurement"]["score_clock"]!="CLOCK_MONOTONIC" or \
            protocol["measurement"]["process_clock"]!="CLOCK_MONOTONIC":
        raise ValueError("formal target/space/flags/clock/affinity differs from this assignment")
    expected = plan(protocol,manifest["stage"],manifest.get("algorithms"))
    if any(manifest.get(key)!=expected[key] for key in ("schema","protocol","target_sha256","framework_sha256","driver_sha256")):
        raise ValueError("batch manifest identity differs from the exact frozen plan")
    if manifest["jobs"] != expected["jobs"]:
        raise ValueError("planned jobs differ from the frozen protocol")
    if manifest["stage"]!="diagnostic" and (protocol["measurement"]["clock_health"]["guard"]!=
            "completed_per_target_process_and_driver_first_and_previous_same_boot" or
            protocol["measurement"]["clock_health"]["raw_monotonic_ratio_change_fraction"]!=.02):
        raise ValueError("formal complete-clock guard differs from the reviewed mode/threshold")
    for key in ("target", "framework"):
        if sha256(P1 / protocol[key]["path"]) != protocol[key]["sha256"]:
            raise ValueError(f"{key} changed after freeze; historical analysis needs the matching checkout")
    if execute:
        if protocol["state"] != "approved" or not all((P1 / protocol["approval"][key]).is_file()
                for key in ("code_evidence", "method_evidence")):
            raise ValueError("both independent gate records are required")
        if sha256(__file__) != manifest["driver_sha256"]:
            raise ValueError("driver changed after planning")
        if str(P1) != manifest["measurement_root"]:
            raise ValueError("execute/resume requires the original measurement directory")
        compiler = protocol["target"]["compiler_identity"]
        if sha256(compiler["path"]) != compiler["sha256"]:
            raise ValueError("frozen compiler identity changed")


def plan(protocol, stage, algorithms=None):
    jobs = []
    def run(name, role, config, **fields):
        jobs.append(dict(id=name, action="run", role=role, config={k:config[k] for k in ("s","opt")}, repeats=1, seed=0, **fields))
    if stage == "diagnostic":
        jobs = protocol["diagnostic_jobs"]
    elif stage == "reference":
        run("warmup-reference", "warmup", protocol["measurement"]["warmup"])
        configs = [dict(s=s, opt=o) for s in protocol["space"]["blocks"] for o in protocol["space"]["opts"]]
        for round_id in range(1, 4):
            order = configs.copy()
            random.Random(protocol["reference"]["order_seed"] + round_id - 1).shuffle(order)
            run(f"anchor-r{round_id}-00", "anchor", protocol["reference"]["anchor"], round=round_id)
            for index, config in enumerate(order):
                run(f"ref-r{round_id}-{index+1:02d}", "reference", config, round=round_id)
                if index+1 in protocol["reference"]["anchor_after_positions"]:
                    run(f"anchor-r{round_id}-{index+1:02d}", "anchor", protocol["reference"]["anchor"], round=round_id)
    elif stage in ("comparison", "confirmation"):
        names = list(algorithms or protocol["online"]["algorithms"])
        if stage=="comparison" and names!=protocol["online"]["algorithms"] or stage=="confirmation" and (
                "random" not in names or not set(names)<= {"random","recheck"} or len(names)!=len(set(names))):
            raise ValueError("invalid algorithm subset for this frozen stage")
        seeds = protocol["online"]["seeds"] if stage == "comparison" else protocol["holdout"]["seeds"]
        run("warmup-" + stage, "warmup", protocol["measurement"]["warmup"])
        for block, seed in enumerate(seeds, 1):
            order = protocol["online"]["orders"][block - 1] if stage == "comparison" else (
                names if block % 2 else list(reversed(names)))
            for name in order:
                jobs.append(dict(id=f"b{block}-{name}-seed{seed}", action="search", role="search",
                    block=block, algorithm=name, seed=seed, budget=protocol["online"]["budget"], repeats=1))
            jobs.append(dict(id=f"panel-b{block}", action="panel", role="shared_confirmation", block=block, seed=seed,
                depends_on=[f"b{block}-{name}-seed{seed}" for name in order]))
    elif stage == "starts":
        for index, config in enumerate(protocol["greedy_start_panel"]["starts"], 1):
            jobs.append(dict(id=f"start-{index}", action="search", role="start_panel", block=index,
                algorithm="greedy", seed=0, budget=protocol["online"]["budget"], repeats=1, start=config))
    else:
        raise ValueError("unknown Goal 2 stage")
    return dict(schema=2, stage=stage, protocol=protocol["protocol_path"],
        protocol_sha256=protocol["protocol_sha256"], target_sha256=protocol["target"]["sha256"],
        framework_sha256=protocol["framework"]["sha256"], driver_sha256=sha256(__file__),
        measurement_root=str(P1), algorithms=list(algorithms) if algorithms else None, jobs=jobs)


def reference_best(reference, protocol):
    manifest = load_json(Path(reference) / "plan.json")
    freeze_check(protocol, manifest, P1 / manifest["protocol"])
    protocol = dict(protocol,measurement_root=manifest["measurement_root"])
    values = {}
    for job in manifest["jobs"]:
        if job["role"] != "reference":
            continue
        if validate_task(job, reference, protocol, historical=True) != "complete":
            raise ValueError("common panel requires a complete independent reference")
        rows = read_records(Path(reference) / (job["id"] + ".jsonl"))
        c = job["config"]
        values.setdefault((c["s"], c["opt"]), []).extend(r["kernel_s"] for r in rows if r["type"] == "measurement")
    if len(values) != 20 or any(len(v) != 3 for v in values.values()):
        raise ValueError("reference coverage is incomplete")
    winner = min(values, key=lambda c:(statistics.median(values[c]),
        protocol["space"]["blocks"].index(c[0]),protocol["space"]["opts"].index(c[1])))
    return dict(s=winner[0], opt=winner[1])


def panel(job, directory, reference, protocol, historical=False):
    dependencies, configs = {}, []
    manifest=load_json(Path(directory)/"plan.json")
    for task in job["depends_on"]:
        frozen_job=next(x for x in manifest["jobs"] if x["id"]==task)
        if validate_task(frozen_job,directory,protocol,historical)!="complete":
            raise ValueError("panel dependency is not a verified completed search")
        path = Path(directory) / (task + ".jsonl")
        rows = read_records(path)
        summary = next((r for r in reversed(rows) if r["type"] == "summary"), None)
        if not summary or not summary["best"] or summary["failed_trials"]:
            raise ValueError("all block searches must finish and lock valid returns before confirmation")
        dependencies[task] = sha256(path)
        configs.append(summary["best"]["config"])
    fixed = reference_best(reference, protocol)
    configs.append(fixed)
    unique = sorted({(c["s"], c["opt"]) for c in configs})
    jobs = []
    for round_id in range(1, protocol["return_confirmation"]["repeats"] + 1):
        order = unique.copy()
        random.Random(protocol["return_confirmation"]["order_seed"] + 100*job["block"] + round_id).shuffle(order)
        for s, opt in order:
            jobs.append(dict(id=f"{job['id']}-r{round_id}-s{s}-{opt}", action="run", role="shared_confirmation",
                block=job["block"], seed=job["seed"], round=round_id, repeats=1, config=dict(s=s, opt=opt)))
    result = dict(schema=2, block=job["block"], seed=job["seed"],
        protocol_sha256=protocol["protocol_sha256"], dependencies_sha256=dependencies,
        reference_manifest_sha256=sha256(Path(reference) / "plan.json"),
        reference_config=fixed, configs=[dict(s=s, opt=o) for s, o in unique], jobs=jobs)
    result["fingerprint"] = at.fingerprint(result)
    path = Path(directory) / (job["id"] + ".json")
    if path.exists():
        if load_json(path) != result:
            raise ValueError("locked common panel or search returns changed")
    else:
        if historical:
            raise ValueError("historical analysis requires an existing locked panel; raw remains read-only")
        path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return jobs


def execute(directory, manifest, protocol, protocol_path, reference=None, max_jobs=None):
    freeze_check(protocol, manifest, protocol_path, execute=True)
    with performance_lock():
        completed = 0
        for entry in manifest["jobs"]:
            jobs = panel(entry, directory, reference, protocol) if entry["action"] == "panel" else [entry]
            for job in jobs:
                state = validate_task(job, directory, protocol)
                if state == "complete":
                    continue
                if state == "failed":
                    raise ValueError("failed jobs require diagnosis; no automatic rerun")
                if max_jobs is not None and completed >= max_jobs:
                    return
                path = Path(directory) / (job["id"] + ".jsonl")
                prior = read_records(path) if path.exists() else []
                already = sum(r["type"] == "measurement_start" for r in prior)
                upper = max(0, job.get("budget", 1) * job.get("repeats", 1) - already)
                print(json.dumps(dict(task=job["id"], role=job["role"], state="running")), flush=True)
                record = controlled(command(job, directory, protocol, protocol_path), directory,
                    job["id"], job["role"], upper, journal=path,
                    complete_clock_guard=manifest["stage"]!="diagnostic")
                append(Path(directory) / "driver.jsonl", "task_end", **{k:v for k,v in record.items() if k not in ("type", "at")})
                if validate_task(job, directory, protocol) != "complete":
                    raise ValueError("task did not complete its valid frozen job")
                if record["driver_wall_s"] > 1:
                    ratio = record["clock_elapsed_s"]["raw"] / record["driver_wall_s"]
                    baseline = protocol["measurement"]["clock_health"].get("raw_mono_ratio")
                    if baseline is not None and abs(ratio / baseline - 1) > .02:
                        raise ValueError("RAW/MONOTONIC relation changed by >2%; pause and diagnose")
                print(json.dumps(dict(task=job["id"], state="complete", calls=record["n4096_calls"],
                    driver_wall_s=record["driver_wall_s"], resource_s=record["resource_s"])), flush=True)
                completed += 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "execute", "status", "usage", "recover"))
    parser.add_argument("--protocol", type=Path, default=P1 / "evidence/protocol_v2.json")
    parser.add_argument("--stage", choices=("diagnostic", "reference", "comparison", "confirmation", "starts"))
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--algorithms")
    parser.add_argument("--max-jobs", type=int)
    parser.add_argument("--recovery-evidence", type=Path)
    args = parser.parse_args(argv)
    if args.action == "usage":
        calls, cost = usage()
        print(json.dumps(dict(n4096_calls=calls, resource_s=cost, call_cap=MAX_CALLS, time_cap_s=MAX_SECONDS)))
        return
    if args.action=="recover":
        if args.recovery_evidence is None:
            parser.error("--recovery-evidence is required")
        with performance_lock():
            print(json.dumps(recover_resource(args.recovery_evidence)))
        return
    protocol = load_json(args.protocol)
    protocol.update(protocol_sha256=sha256(args.protocol), protocol_path=str(args.protocol.resolve().relative_to(P1)),
                    measurement_root=str(P1))
    if args.directory is None:
        parser.error("--directory is required")
    directory = args.directory.resolve()
    directory.relative_to(P1)
    if args.action == "plan":
        directory.mkdir(parents=True, exist_ok=True)
        result = plan(protocol, args.stage, args.algorithms.split(",") if args.algorithms else None)
        with (directory / "plan.json").open("x") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
        print(json.dumps(dict(plan=str(directory / "plan.json"), jobs=len(result["jobs"])))); return
    manifest = load_json(directory / "plan.json")
    if args.action == "execute":
        execute(directory, manifest, protocol, args.protocol.resolve(), args.reference, args.max_jobs)
    else:
        protocol["measurement_root"]=manifest["measurement_root"]
        freeze_check(protocol, manifest, args.protocol.resolve())
        states = {}
        for entry in manifest["jobs"]:
            if entry["action"] == "panel":
                path = directory / (entry["id"] + ".json")
                jobs = load_json(path)["jobs"] if path.exists() else []
                states[entry["id"]] = [validate_task(job, directory, protocol, True) for job in jobs] or ["pending"]
            else:
                states[entry["id"]] = validate_task(entry, directory, protocol, True)
        print(json.dumps(states, indent=2))


if __name__ == "__main__":
    def interrupt(signum,frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,interrupt)
    try:
        main()
    except KeyboardInterrupt:
        print("interrupted; owned processes stopped and known costs recorded",file=sys.stderr)
        raise SystemExit(130)
