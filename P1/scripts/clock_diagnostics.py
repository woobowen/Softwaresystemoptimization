#!/usr/bin/env python3
"""Read-only clock probes and a separately identified multi-clock matrix build."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import signal
import sys

from experiment_v2 import P1, controlled, performance_lock, load_json, sha256
from validate_target import kernel

PROBE = r'''
#define _GNU_SOURCE
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/timex.h>
#include <time.h>

static const clockid_t clocks[4] = {CLOCK_MONOTONIC, CLOCK_MONOTONIC_RAW,
    CLOCK_REALTIME, CLOCK_PROCESS_CPUTIME_ID};
static void sample(int64_t values[4]) {
    for (int i=0; i<4; ++i) {
        struct timespec t;
        if (clock_gettime(clocks[i], &t)) exit(2);
        values[i]=(int64_t)t.tv_sec*1000000000LL+t.tv_nsec;
    }
}
int main(int argc, char **argv) {
    if (argc != 4) return 2;
    const char *mode=argv[1];
    unsigned long long count=strtoull(argv[2], NULL, 10);
    int seconds=atoi(argv[3]);
    int64_t begin[4], end[4];
    volatile double state=0.25;
    sample(begin);
    if (!strcmp(mode,"idle")) {
        struct timespec wait={seconds,0};
        int rc;
        while ((rc=clock_nanosleep(CLOCK_BOOTTIME,0,&wait,&wait))==EINTR) {}
        if (rc) return 3;
    } else if (!strcmp(mode,"work")) {
        for (unsigned long long i=0; i<count; ++i)
            state=state*0.9999999+0.00000003;
    } else if (!strcmp(mode,"overhead")) {
        int64_t values[4];
        for (unsigned long long i=0; i<count; ++i) sample(values);
    } else return 2;
    sample(end);
    printf("{\"mode\":\"%s\",\"iterations\":%llu,\"requested_idle_seconds\":%d,",mode,count,seconds);
    printf("\"idle_control_clock\":\"CLOCK_BOOTTIME\",\"clock_order\":[\"MONOTONIC\",\"RAW\",\"REALTIME\",\"PROCESS_CPU\"],");
    printf("\"start_ns\":[%lld,%lld,%lld,%lld],\"end_ns\":[%lld,%lld,%lld,%lld],",
        (long long)begin[0],(long long)begin[1],(long long)begin[2],(long long)begin[3],
        (long long)end[0],(long long)end[1],(long long)end[2],(long long)end[3]);
    printf("\"elapsed_s\":[%.9f,%.9f,%.9f,%.9f],\"work_checksum\":%.17g}",
        (end[0]-begin[0])/1e9,(end[1]-begin[1])/1e9,(end[2]-begin[2])/1e9,(end[3]-begin[3])/1e9,(double)state);
    puts("");
    struct timex tx={0};
    int rc=adjtimex(&tx); /* modes=0: query only, never change the clock. */
    printf("{\"adjtimex_readonly\":true,\"returncode\":%d,\"offset_raw\":%ld,\"offset_unit\":\"%s\",\"frequency_scaled_ppm\":%ld,\"tick_us\":%ld,\"status\":%d,\"precision_us\":%ld}\n",
        rc,tx.offset,(tx.status & STA_NANO)?"ns":"us",tx.freq,tx.tick,tx.status,tx.precision);
    return 0;
}
'''

MATRIX_CLOCKS = r'''
static long long diagnostic_read(clockid_t id) {
    struct timespec t;
    if (clock_gettime(id,&t)) exit(2);
    return (long long)t.tv_sec*1000000000LL+t.tv_nsec;
}
'''


def diagnostic_source(text):
    before = kernel(text)
    # The diagnostic still reads all four domains in the original fixed order.
    for boundary in ("start", "end"):
        text = text.replace(f"clock_gettime(CLOCK_MONOTONIC_RAW, &{boundary})",
                            f"clock_gettime(CLOCK_MONOTONIC, &{boundary})", 1)
    text = text.replace("int main(int argc, const char *argv[]){", MATRIX_CLOCKS + "\nint main(int argc, const char *argv[]){", 1)
    for boundary in ("start", "end"):
        marker = f"    if (clock_gettime(CLOCK_MONOTONIC, &{boundary}) != 0) return 1;"
        assert text.count(marker) == 1
        extra = f"""
    long long {boundary}_ns[4];
    {boundary}_ns[0]=(long long){boundary}.tv_sec*1000000000LL+{boundary}.tv_nsec;
    {boundary}_ns[1]=diagnostic_read(CLOCK_MONOTONIC_RAW);
    {boundary}_ns[2]=diagnostic_read(CLOCK_REALTIME);
    {boundary}_ns[3]=diagnostic_read(CLOCK_PROCESS_CPUTIME_ID);"""
        text = text.replace(marker, marker + extra, 1)
    output = r'''
    printf("{\"clock_order\":[\"MONOTONIC\",\"RAW\",\"REALTIME\",\"PROCESS_CPU\"],\"start_ns\":[%lld,%lld,%lld,%lld],\"end_ns\":[%lld,%lld,%lld,%lld],\"elapsed_s\":[%.9f,%.9f,%.9f,%.9f]}\n",
        start_ns[0],start_ns[1],start_ns[2],start_ns[3],end_ns[0],end_ns[1],end_ns[2],end_ns[3],
        (end_ns[0]-start_ns[0])/1e9,(end_ns[1]-start_ns[1])/1e9,
        (end_ns[2]-start_ns[2])/1e9,(end_ns[3]-start_ns[3])/1e9);
'''
    assert text.count("    return 0;") == 1
    text = text.replace("    return 0;", output + "    return 0;", 1)
    assert kernel(text) == before
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "probes", "matrix"))
    args = parser.parse_args()
    cache, evidence = P1 / ".cache/clock_goal2", P1 / "evidence/measurement/clocks"
    cache.mkdir(parents=True, exist_ok=True)
    with performance_lock():
        if args.action == "build":
            if (evidence / "identity.json").exists():
                raise ValueError("diagnostic build identity already exists; do not overwrite it")
            source = P1 / "src/matrix_multiplication.c"
            variant = diagnostic_source(source.read_text())
            (cache / "probe.c").write_text(PROBE)
            (cache / "matrix_multiclock.c").write_text(variant)
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "matrix_multiclock.diff").write_text("".join(difflib.unified_diff(source.read_text().splitlines(True),variant.splitlines(True),fromfile="formal_target",tofile="diagnostic_only")))
            identity = {"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
                "variant_sha256":hashlib.sha256(variant.encode()).hexdigest(),
                "kernel_sha256":hashlib.sha256(kernel(variant).encode()).hexdigest(),
                "probe_sha256":hashlib.sha256(PROBE.encode()).hexdigest(),
                "flags":["-std=c11","-Wall","-Wextra","-O2"],
                "diagnostic_only":True,"idle_control":"BOOTTIME; no absolute-accuracy claim",
                "long_fixed_iterations":8000000000}
            compiler=load_json(P1/"evidence/protocol_diagnostic.json")["target"]["compiler_identity"]
            if sha256(compiler["path"])!=compiler["sha256"]:
                raise ValueError("diagnostic compiler differs from the captured identity")
            identity["compiler"]=compiler
            (evidence / "identity.json").write_text(json.dumps(identity,indent=2)+"\n")
            for name in ("probe", "matrix_multiclock"):
                controlled([compiler["path"],*identity["flags"],cache/(name+".c"),"-o",cache/name],evidence,"build-"+name,"diagnostic_build",time_limit=60)
            identity["binary_sha256"]={n:sha256(cache/n) for n in ("probe","matrix_multiclock")}
            (evidence/"identity.json").write_text(json.dumps(identity,indent=2)+"\n")
        elif args.action == "probes":
            check_identity(cache,evidence)
            # Stops are BOOTTIME idle waits or a fixed iteration count, not one of the tested clocks.
            cases = [("overhead",10000,0),("idle",0,1),("idle",0,1),("work",10000000,0),
                     ("idle",0,40),("work",8000000000,0),("work",8000000000,0)]
            for index,(mode,count,seconds) in enumerate(cases,1):
                task=f"probe-{index}-{mode}"
                controlled(["taskset","-c","0",cache/"probe",mode,str(count),str(seconds)],
                    evidence,task,"clock_probe",time_limit=300)
                print(task, (evidence/(task+".stdout.txt")).read_text(), flush=True)
        else:
            check_identity(cache,evidence)
            for name,s in (("fast",128),("medium",8)):
                task="matrix-multiclock-"+name
                controlled(["taskset","-c","0",cache/"matrix_multiclock",str(s)],evidence,
                    task,"clock_matrix_diagnostic",call_upper=1,direct_calls=1,time_limit=1200)
                print(task,(evidence/(task+".stdout.txt")).read_text(),flush=True)


def check_identity(cache,evidence):
    identity=load_json(evidence/"identity.json")
    if sha256(cache/"probe.c")!=identity["probe_sha256"] or \
            sha256(cache/"matrix_multiclock.c")!=identity["variant_sha256"] or \
            sha256(P1/"src/matrix_multiplication.c")!=identity["source_sha256"] or any(
                sha256(cache/n)!=digest for n,digest in identity["binary_sha256"].items()):
        raise ValueError("diagnostic source or binary changed after build")


if __name__ == "__main__":
    def interrupt(signum,frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,interrupt)
    try:
        main()
    except KeyboardInterrupt:
        print("interrupted; owned diagnostic processes stopped and costs recorded",file=sys.stderr)
        raise SystemExit(130)
