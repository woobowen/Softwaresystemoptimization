#!/usr/bin/env python3
"""The one approved twelve-run clock diagnostic; no formal search exception."""

import argparse
import ctypes
import hashlib
import json
import math
from pathlib import Path
import signal
import sys

import clock_diagnostics as cd
import experiment_v2 as ex

QUERY = r'''
#include <sys/timex.h>
int query_timex(long out[7]) {
    struct timex value = {0}; /* modes=0: read only. */
    int rc = adjtimex(&value);
    out[0]=value.offset; out[1]=value.freq; out[2]=value.tick;
    out[3]=value.status; out[4]=value.precision; out[5]=rc;
    out[6]=(value.status & STA_NANO) != 0;
    return rc;
}
'''


def query_reader(cache, identity):
    if identity.get("readonly_modes")!=0 or identity["source_sha256"]!=hashlib.sha256(QUERY.encode()).hexdigest() or \
            ex.sha256(cache/"timex.c") != identity["source_sha256"] or \
            ex.sha256(cache/"timex.so") != identity["binary_sha256"]:
        raise ValueError("read-only timex diagnostic build changed")
    library = ctypes.CDLL(str(cache/"timex.so"))
    library.query_timex.argtypes = [ctypes.POINTER(ctypes.c_long)]
    library.query_timex.restype = ctypes.c_int
    def read():
        values = (ctypes.c_long * 7)()
        if library.query_timex(values) < 0:
            raise ValueError("read-only adjtimex query failed")
        return dict(readonly=True, offset_raw=values[0], frequency_scaled_ppm=values[1],
            tick_us=values[2], status=values[3], precision_us=values[4],
            returncode=values[5], offset_unit="ns" if values[6] else "us")
    return read


def ratio_check(source, values, previous):
    if any(not math.isfinite(x) or x <= 0 for x in values.values()):
        raise ValueError("nonpositive complete clock interval")
    ratio = values["raw"] / values["monotonic"]
    baselines = previous[:1] + previous[-1:] if previous else []
    changes = [ratio/value-1 for value in baselines]
    return dict(source=source, elapsed_s=values, ratio=ratio, baseline_ratios=baselines,
        relative_changes=changes, conflict=any(abs(x) > .02 for x in changes))


def complete_sources(ledger, before_attempt=None):
    """Compare like full intervals; failed/prefix/other-boot records are excluded."""
    rows = ex.read_records(ledger) if Path(ledger).exists() else []
    if before_attempt is not None:
        indices=[i for i,r in enumerate(rows) if r["type"]=="task_start" and r["attempt_id"]==before_attempt]
        if len(indices)!=1: raise ValueError("no unique start for completed-clock recovery")
        rows=rows[:indices[0]]
    starts = {r["attempt_id"]:r for r in rows if r["type"]=="task_start"}
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    result = dict(driver=[], formal_target_process=[], diagnostic_kernel=[])
    for end in rows:
        if end["type"] != "task_end" or end.get("returncode") != 0 or end.get("reason") or \
                not end.get("n4096_calls_known",True) or end.get("n4096_calls",0) < 1:
            continue
        start = starts[end["attempt_id"]]
        if start["boot_id"] != boot:
            continue
        if end.get("clock_elapsed_s") and end.get("driver_wall_s",0) >= 10:
            result["driver"].append(end["clock_elapsed_s"]["raw"]/end["driver_wall_s"])
        if start.get("journal"):
            journal=ex.read_records(ex.P1/start["journal"])
            ids=[(r["run_id"],r["trial_id"],r["repeat"],r["pid"]) for r in journal if r["type"]=="measurement_start"]
            offset=start["prior_measurement_starts"]
            selected=set(ids[offset:offset+end["n4096_calls"]])
            for row in journal:
                if row["type"]=="measurement" and (row["run_id"],row["trial_id"],row["repeat"],row["pid"]) in selected and row["status"]=="ok" and row["spawned"]:
                    values=row["clock_deltas_s"]
                    result["formal_target_process"].append(values["CLOCK_MONOTONIC_RAW"]/values["CLOCK_MONOTONIC"])
        elif start["role"]=="clock_matrix_diagnostic":
            values=matrix_interval(ex.P1/end["stdout"])
            result["diagnostic_kernel"].append(values["raw"]/values["monotonic"])
    return result


def matrix_interval(stdout):
    lines=Path(stdout).read_text().strip().splitlines()
    if len(lines)!=3 or not lines[1].startswith("checksum=") or \
            not 1.7e10 < float(lines[1].split("=",1)[1]) < 1.8e10:
        raise ValueError("diagnostic target output/checksum is incomplete")
    row=json.loads(lines[2])
    if row["clock_order"] != ["MONOTONIC","RAW","REALTIME","PROCESS_CPU"] or \
            len(row["start_ns"])!=4 or len(row["end_ns"])!=4 or len(row["elapsed_s"])!=4 or \
            any(type(x) is not int for x in row["start_ns"]+row["end_ns"]):
        raise ValueError("diagnostic kernel clock fields/units differ")
    values=[(b-a)/1e9 for a,b in zip(row["start_ns"],row["end_ns"])]
    if any(x<=0 for x in values) or any(not math.isfinite(x) for x in row["elapsed_s"]) or \
            not math.isfinite(float(lines[0])) or any(abs(a-b)>1e-9 for a,b in zip(values,row["elapsed_s"])) or \
            abs(float(lines[0])-values[0])>1e-4:
        raise ValueError("diagnostic kernel clock deltas differ from raw boundaries")
    return dict(zip(("monotonic","raw","realtime"),values[:3]))


class Observer:
    def __init__(self, protocol, job, command, trace, read_timex, previous):
        self.protocol, self.job, self.command = protocol, job, list(map(str,command))
        self.trace, self.read_timex, self.previous = Path(trace), read_timex, previous
        self.begin, self.last, self.prefix_conflict = None, None, False

    def validate(self, task, command, call_upper, journal):
        if self.protocol.get("purpose")!="one_finite_clock_relation_followup" or \
                self.protocol.get("state")!="approved" or \
                self.protocol["measurement"].get("formal_admission") is not False or \
                len(self.protocol["diagnostic_jobs"])!=12 or self.job not in self.protocol["diagnostic_jobs"] or \
                task!=self.job["id"] or command!=self.command or call_upper!=1 or \
                (journal is None)!=(self.job["action"]=="clock_matrix") or self.trace.exists():
            raise ValueError("record-only observation is restricted to the exact approved twelve diagnostic jobs")

    def sample(self, kind, current, baselines):
        if self.begin is None:
            self.begin = self.last = current
        prefix=ex.elapsed(self.begin,current)
        local=ex.elapsed(self.last,current)
        if kind=="interval" and local["monotonic"]<2:
            return
        ratio=prefix["raw"]/prefix["monotonic"] if prefix["monotonic"]>0 else None
        conflict=prefix["monotonic"]>=10 and any(abs(ratio/b-1)>.02 for b in baselines[:1]+baselines[-1:])
        self.prefix_conflict |= conflict
        ex.append(self.trace,"clock_sample",phase=kind,task=self.job["id"],clock_ns=current,
            unit="ns",read_order=list(ex.CLOCKS),prefix_elapsed_s=prefix,local_elapsed_s=local,
            prefix_ratio=ratio,local_ratio=local["raw"]/local["monotonic"] if local["monotonic"]>0 else None,
            prefix_clock_conflict=conflict,adjtimex=self.read_timex(),
            diagnostic_only=True,action="record; finite diagnostic continues unless a hard limit fails")
        self.last=current

    def finish(self, after, rows, stdout, code, baselines):
        self.sample("end",after,baselines)
        checks=[ratio_check("driver",ex.elapsed(self.begin,after),self.previous["driver"])]
        if code==0:
            if self.job["action"]=="clock_matrix":
                source,values="diagnostic_kernel",matrix_interval(stdout)
            else:
                measurements=[r for r in rows if r["type"]=="measurement" and r["status"]=="ok" and r["spawned"]]
                if len(measurements)!=1 or not any(r["type"]=="summary" for r in rows):
                    raise ValueError("one complete diagnostic target measurement is required")
                source="formal_target_process"
                values=dict(zip(ex.CLOCKS,(measurements[0]["clock_deltas_s"][key] for key in
                    ("CLOCK_MONOTONIC","CLOCK_MONOTONIC_RAW","CLOCK_REALTIME"))))
            checks.append(ratio_check(source,values,self.previous[source]))
        conflict=any(row["conflict"] for row in checks)
        result=dict(clock_diagnostic_only=True,clock_complete_checks=checks,
            prefix_clock_conflict=self.prefix_conflict,complete_clock_conflict=conflict,
            clock_conflict=conflict,complete_clock_observation=code==0,
            clock_trace=str(self.trace.relative_to(ex.P1)))
        ex.append(self.trace,"clock_complete",task=self.job["id"],**result)
        result["clock_trace_sha256"]=ex.sha256(self.trace)
        return result


def completed_job(job, directory, protocol, protocol_path, end):
    """A resume skips only the same completed command and unmodified raw trace."""
    starts=[r for r in ex.read_records(ex.LEDGER) if r["type"]=="task_start" and r["attempt_id"]==end["attempt_id"]]
    if len(starts)!=1 or end["returncode"]!=0 or end.get("reason") is not None or \
            end.get("complete_clock_observation") is not True or end["n4096_calls"]!=1 or \
            end.get("n4096_calls_known") is not True:
        raise ValueError("previous followup did not complete successfully")
    start=starts[0]
    path=directory/(job["id"]+".jsonl") if job["action"]=="run" else None
    command=ex.command(job,directory,protocol,protocol_path) if path else [
        "taskset","-c","0",str(ex.P1/protocol["multiclock_identity"]["binary"]),str(job["config"]["s"])]
    if command[-1]=="--resume": command.pop()
    if start["command"]!=command or start["role"]!=job["role"] or start["call_upper"]!=1 or \
            start["prior_measurement_starts"]!=0 or start["journal"]!=(str(path.relative_to(ex.P1)) if path else None):
        raise ValueError("previous command or journal differs from the frozen followup job")
    spans=ex.elapsed(start["clock_start_ns"],end["clock_end_ns"])
    if spans!=end["clock_elapsed_s"] or end["driver_wall_s"]!=spans["monotonic"] or \
            end["resource_s"]!=max(spans.values()) or end["resource_wall_s"]!=max(spans.values()) or \
            start["boot_id"]!=Path("/proc/sys/kernel/random/boot_id").read_text().strip():
        raise ValueError("saved diagnostic driver cost differs from its raw boundaries")
    if path:
        if ex.validate_task(job,directory,protocol)!="complete":
            raise ValueError("previous formal-target diagnostic has changed")
        rows=ex.read_records(path)
        measurements=[r for r in rows if r["type"]=="measurement" and r["status"]=="ok" and r["spawned"]]
        if len(measurements)!=1: raise ValueError("completed diagnostic has not exactly one process")
        values=dict(zip(ex.CLOCKS,(measurements[0]["clock_deltas_s"][key] for key in
            ("CLOCK_MONOTONIC","CLOCK_MONOTONIC_RAW","CLOCK_REALTIME"))))
        source="formal_target_process"
    else:
        source="diagnostic_kernel"
        values=matrix_interval(directory/(job["id"]+".stdout.txt"))
    baselines=complete_sources(ex.LEDGER,end["attempt_id"])
    checks=[ratio_check("driver",spans,baselines["driver"]),ratio_check(source,values,baselines[source])]
    conflict=any(r["conflict"] for r in checks)
    if end["clock_complete_checks"]!=checks or end["complete_clock_conflict"]!=conflict or end["clock_conflict"]!=conflict:
        raise ValueError("complete diagnostic clock checks differ from raw intervals and preceding baselines")
    trace_path=directory/(job["id"]+".clocks.jsonl")
    if end["clock_trace"]!=str(trace_path.relative_to(ex.P1)) or end["clock_trace_sha256"]!=ex.sha256(trace_path):
        raise ValueError("completed raw clock trace changed")
    trace=ex.read_records(trace_path)
    if not trace or trace[0].get("clock_ns")!=start["clock_start_ns"] or \
            trace[-2].get("clock_ns")!=end["clock_end_ns"] or trace[-1]["type"]!="clock_complete" or \
            any(trace[-1].get(key)!=end.get(key) for key in ("task","clock_complete_checks",
                "prefix_clock_conflict","complete_clock_conflict","clock_conflict","complete_clock_observation")):
        raise ValueError("previous clock trace differs from its completed driver record")
    previous=start["clock_start_ns"]
    prefix_conflict=False
    for row in trace[:-1]:
        if row["type"]!="clock_sample" or row["unit"]!="ns" or row["read_order"]!=list(ex.CLOCKS) or \
                set(row["clock_ns"])!=set(ex.CLOCKS) or any(type(x) is not int for x in row["clock_ns"].values()) or \
                row["adjtimex"].get("readonly") is not True or \
                row["prefix_elapsed_s"]!=ex.elapsed(start["clock_start_ns"],row["clock_ns"]) or \
                row["local_elapsed_s"]!=ex.elapsed(previous,row["clock_ns"]):
            raise ValueError("saved clock timeline or read-only query differs from raw boundaries")
        prefix=row["prefix_elapsed_s"]
        local=row["local_elapsed_s"]
        ratio=prefix["raw"]/prefix["monotonic"] if prefix["monotonic"]>0 else None
        flag=prefix["monotonic"]>=10 and any(abs(ratio/b-1)>.02 for b in baselines["driver"][:1]+baselines["driver"][-1:])
        if row["prefix_ratio"]!=ratio or row["prefix_clock_conflict"]!=flag or \
                row["local_ratio"]!=(local["raw"]/local["monotonic"] if local["monotonic"]>0 else None):
            raise ValueError("prefix/local clock fields differ from raw intervals")
        prefix_conflict|=flag
        previous=row["clock_ns"]
    if end["prefix_clock_conflict"]!=prefix_conflict:
        raise ValueError("saved prefix conflict differs from independent timeline replay")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("build","check","execute"))
    parser.add_argument("--protocol",type=Path,default=ex.P1/"evidence/protocol_clock_followup_r1.json")
    parser.add_argument("--directory",type=Path,default=ex.P1/"results/clock_followup_v2_r1")
    args=parser.parse_args()
    protocol=ex.load_json(args.protocol)
    cache=ex.P1/".cache/clock_followup"
    evidence=ex.P1/"evidence/measurement/clock_followup"
    with ex.performance_lock():
        if args.action=="build":
            cache.mkdir(parents=True,exist_ok=True)
            evidence.mkdir(parents=True,exist_ok=True)
            if (evidence/"timex_identity.json").exists():
                raise ValueError("read-only query build already recorded")
            (cache/"timex.c").write_text(QUERY)
            compiler=protocol["target"]["compiler_identity"]
            if ex.sha256(compiler["path"])!=compiler["sha256"]:
                raise ValueError("diagnostic compiler identity changed")
            ex.controlled([compiler["path"],"-std=c11","-Wall","-Wextra","-O2","-shared","-fPIC",
                cache/"timex.c","-o",cache/"timex.so"],evidence,"build-timex-query","diagnostic_build",time_limit=60)
            identity=dict(source_sha256=hashlib.sha256(QUERY.encode()).hexdigest(),
                binary_sha256=ex.sha256(cache/"timex.so"),compiler=compiler,readonly_modes=0)
            (evidence/"timex_identity.json").write_text(json.dumps(identity,indent=2)+"\n")
            print(json.dumps(query_reader(cache,identity)()))
            return
        directory=args.directory.resolve()
        directory.relative_to(ex.P1)
        manifest=ex.load_json(directory/"plan.json")
        protocol.update(protocol_sha256=ex.sha256(args.protocol),measurement_root=str(ex.P1),
            protocol_path=str(args.protocol.resolve().relative_to(ex.P1)))
        ex.freeze_check(protocol,manifest,args.protocol,execute=True)
        if ex.sha256(__file__)!=protocol["approval"]["followup_executor_sha256"] or \
                ex.sha256(ex.P1/protocol["design"])!=protocol["design_sha256"]:
            raise ValueError("followup executor/design differs from approval")
        identity=protocol["multiclock_identity"]
        if ex.sha256(ex.P1/identity["path"])!=identity["sha256"]:
            raise ValueError("original multi-clock identity changed")
        cd.check_identity(ex.P1/".cache/clock_goal2",ex.P1/"evidence/measurement/clocks")
        query_identity=protocol["readonly_query_identity"]
        if ex.sha256(ex.P1/query_identity["path"])!=query_identity["sha256"]:
            raise ValueError("read-only query identity differs from the frozen protocol")
        compiled_query=ex.load_json(ex.P1/query_identity["path"])
        if compiled_query["compiler"]!=protocol["target"]["compiler_identity"]:
            raise ValueError("read-only query compiler differs from this protocol")
        read_timex=query_reader(cache,compiled_query)
        if args.action=="check":
            print(json.dumps(dict(state="checked",jobs=len(manifest["jobs"]),
                protocol_sha256=protocol["protocol_sha256"],n4096_calls=0)),flush=True)
            return
        for job in manifest["jobs"]:
            path=directory/(job["id"]+".jsonl") if job["action"]=="run" else None
            old=[r for r in ex.read_records(ex.LEDGER) if r["type"]=="task_end" and r["task"]==job["id"]]
            if old:
                if len(old)!=1:
                    raise ValueError("previous followup failed; inspect instead of rerunning")
                completed_job(job,directory,protocol,args.protocol,old[0])
                continue
            if path and path.exists():
                raise ValueError("unaccounted followup journal exists; inspect before recovery")
            command=ex.command(job,directory,protocol,args.protocol) if path else [
                "taskset","-c","0",str(ex.P1/identity["binary"]),str(job["config"]["s"])]
            observer=Observer(protocol,job,command,directory/(job["id"]+".clocks.jsonl"),
                read_timex,complete_sources(ex.LEDGER))
            print(json.dumps(dict(task=job["id"],state="running",diagnostic_only=True)),flush=True)
            end=ex.controlled(command,directory,job["id"],job["role"],call_upper=1,journal=path,
                direct_calls=1 if path is None else None,time_limit=1200,diagnostic_observer=observer)
            ex.append(directory/"driver.jsonl","task_end",**{k:v for k,v in end.items() if k not in ("type","at")})
            if path and ex.validate_task(job,directory,protocol)!="complete":
                raise ValueError("followup formal-target trace differs from its frozen job")
            print(json.dumps(dict(task=job["id"],state="complete",complete_clock_conflict=end["complete_clock_conflict"],
                prefix_clock_conflict=end["prefix_clock_conflict"],driver_wall_s=end["driver_wall_s"])),flush=True)


if __name__=="__main__":
    def interrupt(signum,frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,interrupt)
    try:
        main()
    except KeyboardInterrupt:
        print("interrupted; owned diagnostic processes stopped and costs recorded",file=sys.stderr)
        raise SystemExit(130)
