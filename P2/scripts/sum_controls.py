#!/usr/bin/env python3
"""Run the fixed Checkoff 2 cache experiments outside the source directory."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
P2 = ROOT / "P2"
LOCAL = ROOT / ".cache/P2/sum-controls"
OUTPUT = P2 / "evidence/profiling/checkoff2"


def run(command, logfile):
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    logfile.write_text("$ " + " ".join(map(str, command)) + "\n" + result.stdout)
    result.check_returncode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", type=Path, default=LOCAL)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    local, output = args.local.resolve(), args.output.resolve()
    local.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=False)
    original = (P2 / "recitation/sum.c").read_text()
    # 16 KiB fits D1; 4 MiB fits LL but not D1; 40 MB exceeds simulated LL.
    cases = [(10000000, 100000000), (4096, 100000000), (1048576, 100000000),
             (10000000, 10000000), (10000000, 50000000)]
    rows = []
    provenance = []
    for u, n in cases:
        name = f"u{u}-n{n}"
        source = local / (name + ".c")
        binary = local / name
        source.write_text(original.replace("const int U = 10000000;", f"const int U = {u};")
                         .replace("const int N = 100000000;", f"const int N = {n};"))
        build = ["clang", "-Wall", "-O1", "-DNDEBUG", "-g", str(source), "-lrt", "-o", str(binary)]
        run(build, output / (name + "-build.txt"))
        cache = local / (name + ".cg")
        command = ["valgrind", "--tool=cachegrind", "--cache-sim=yes", "--branch-sim=yes",
                   "--cachegrind-out-file=" + str(cache), str(binary)]
        run(command, output / (name + "-cachegrind.txt"))
        run(["cg_annotate", "--auto=yes", "--context=4", "--show-percs=no", str(cache)],
            output / (name + "-annotate.txt"))
        lines = cache.read_text().splitlines()
        events = next(line.split()[1:] for line in lines if line.startswith("events:"))
        values = next(map(int, line.split()[1:]) for line in lines if line.startswith("summary:"))
        counts = dict(zip(events, values))
        refs = counts["Dr"] + counts["Dw"]
        misses = counts["D1mr"] + counts["D1mw"]
        last = counts["DLmr"] + counts["DLmw"]
        rows.append(dict(U=u, N=n, array_bytes=4*u, D_refs=refs, D1_misses=misses,
                         D1_miss_percent=100*misses/refs, LLd_misses=last,
                         LLd_miss_percent=100*last/refs))
        provenance.append(dict(case=name, source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                               binary=str(binary), binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                               cache=str(cache), cache_sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),
                               build=build, command=command,
                               cache_configuration=[line for line in lines if line.startswith("desc:")], counts=counts))
        (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
        print(name + " finished", flush=True)
    with (output / "summary.csv").open("w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
