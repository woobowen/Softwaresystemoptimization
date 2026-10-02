#!/usr/bin/env python3
"""Generate validation builds from the measured source, preserving its kernel."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/matrix_multiplication.c"


def kernel(text):
    start = text.index("    for(int ih")
    endings = ("    gettimeofday(&end", "    if (clock_gettime(CLOCK_MONOTONIC, &end)",
               "    if (clock_gettime(CLOCK_MONOTONIC_RAW, &end)")
    found = [text.index(marker, start) for marker in endings if marker in text[start:]]
    assert len(found) == 1, "Unexpected timer boundary"
    return "\n".join(line.rstrip() for line in text[start:found[0]].splitlines())


REFERENCE = r'''
#include <math.h>

static int check_element(int i, int j, long double *max_abs,
                         long double *max_rel) {
    long double expected = 0.0L;
    for (int k = 0; k < n; ++k)
        expected += (long double)A[i][k] * (long double)B[k][j];
    long double error = fabsl((long double)C[i][j] - expected);
    long double relative = error / fmaxl(fabsl(expected), 1e-12L);
    if (error > *max_abs) *max_abs = error;
    if (relative > *max_rel) *max_rel = relative;
    if (!isfinite(C[i][j]) || error > 1e-12L + 1e-11L * fabsl(expected)) {
        fprintf(stderr, "mismatch (%d,%d): got=%.17g expected=%.21Lg error=%.4Le\n",
                i, j, C[i][j], expected, error);
        return 1;
    }
    return 0;
}

static int verify(void) {
    long double max_abs = 0.0L, max_rel = 0.0L;
    int failures = 0, count = 0;
    if (n <= 129) {
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j) {
                failures += check_element(i, j, &max_abs, &max_rel);
                ++count;
            }
    } else {
        int edges[][2] = {{0,0},{0,n-1},{n-1,0},{n-1,n-1},
                          {n-2,n-1},{n-1,n-2},{n/2,n/2},{n-16,n-16}};
        for (unsigned p = 0; p < sizeof(edges)/sizeof(edges[0]); ++p) {
            failures += check_element(edges[p][0], edges[p][1], &max_abs, &max_rel);
            ++count;
        }
        unsigned state = 20260930U;
        for (int p = 0; p < 16; ++p) {
            state = state * 1664525U + 1013904223U;
            int i = (state >> 12) % n;
            state = state * 1664525U + 1013904223U;
            int j = (state >> 12) % n;
            failures += check_element(i, j, &max_abs, &max_rel);
            ++count;
        }
    }
    printf("CHECK n=%d count=%d max_abs=%.6Le max_rel=%.6Le atol=1e-12 rtol=1e-11 failures=%d\n",
           n, count, max_abs, max_rel, failures);
    return failures != 0;
}
'''


def validation_source(size):
    original = (ROOT / "src/matrix_multiplication.original.c").read_text()
    measured = SOURCE.read_text()
    assert kernel(measured) == kernel(original), "Measured kernel changed"
    replacements = [
        ("#define n 4096", f"#define n {size}"),
        ("    return 0;", "    return verify();"),
        ("int main(int argc, const char *argv[]){", REFERENCE + "\nint main(int argc, const char *argv[]){"),
        ("    if (argc != 2) {", "    if (argc != 4) {"),
        ("    int s = (int)block;", "    int s = (int)block;\n    srand((unsigned)strtoul(argv[2], NULL, 10));\n    int mode = atoi(argv[3]);"),
        ("            A[i][j] = (double)rand() / (double)RAND_MAX;\n            B[i][j] = (double)rand() / (double)RAND_MAX;",
         """            if (mode == 2) {
                A[i][j] = (i == j) ? 1.0 : 0.0;
                B[i][j] = (double)(i - j) / n;
            } else {
                A[i][j] = (double)rand() / (double)RAND_MAX;
                B[i][j] = (double)rand() / (double)RAND_MAX;
                if (mode == 1) {
                    A[i][j] = 2.0 * A[i][j] - 1.0;
                    B[i][j] = 2.0 * B[i][j] - 1.0;
                }
            }"""),
    ]
    for old, new in replacements:
        assert measured.count(old) == 1, f"Unexpected source marker: {old!r}"
        measured = measured.replace(old, new, 1)
    assert kernel(measured) == kernel(original), "Validation kernel changed"
    return measured


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("small", "full", "sanitizer"), default="small")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=1200)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cache = ROOT / ".cache/validation"
    cache.mkdir(parents=True, exist_ok=True)
    sizes = (128, 129) if args.suite == "small" else (129,) if args.suite == "sanitizer" else (4096,)
    opts = ("O1",) if args.suite == "sanitizer" else ("O0", "O1", "O2", "O3") if args.suite == "small" else ("O0", "O3")
    cases = ((1, 0), (7, 0), (19, 0), (1, 1), (7, 1), (1, 2)) if args.suite == "small" else ((1, 0),)
    failures = 0
    with args.output.open("w") as log:
        def record(item):
            log.write(json.dumps(item, sort_keys=True) + "\n")
            log.flush()
        record({"type": "source", "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "kernel_sha256": hashlib.sha256(kernel(SOURCE.read_text()).encode()).hexdigest(),
                "suite": args.suite, "atol": 1e-12, "rtol": 1e-11,
                "reference": "independent unblocked dot products accumulated in long double"})
        for size in sizes:
            src = cache / f"verify_{size}.c"
            src.write_text(validation_source(size))
            for opt in opts:
                binary = cache / f"verify_{size}_{opt}_{args.suite}"
                command = ["gcc", "-std=c11", "-Wall", "-Wextra", "-"+opt]
                if args.suite == "sanitizer":
                    command += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
                command += [str(src), "-lm", "-o", str(binary)]
                p = subprocess.run(command, capture_output=True, text=True, timeout=60)
                record({"type": "build", "n": size, "opt": opt, "command": command,
                        "variant_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                        "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
                if p.returncode:
                    raise RuntimeError(p.stderr)
                blocks = (8, 16, 24, 64, 128) if args.suite != "full" else (24,) if opt == "O0" else (128,)
                for block in blocks:
                    for seed, mode in cases:
                        command = [str(binary), str(block), str(seed), str(mode)]
                        try:
                            p = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
                            item = {"type": "check", "n": size, "opt": opt, "s": block, "seed": seed,
                                    "mode": mode, "command": command, "returncode": p.returncode,
                                    "stdout": p.stdout, "stderr": p.stderr}
                            valid = p.returncode == 0 and "failures=0" in p.stdout
                        except subprocess.TimeoutExpired as error:
                            item = {"type": "timeout", "command": command, "error": str(error)}
                            valid = False
                        record(item)
                        failures += not valid
                        print(f"n={size} {opt} s={block} seed={seed} mode={mode} {'OK' if valid else 'FAIL'}", flush=True)
    if failures:
        raise SystemExit(f"{failures} checks failed; inspect {args.output}")


if __name__ == "__main__":
    main()
