#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN=${PYTHON_BIN:-python3}
mkdir -p evidence/commands
run() {
    local log=$1
    shift
    printf '%q ' "$@" | tee "$log"
    printf '\n' | tee -a "$log"
    "$@" 2>&1 | tee -a "$log"
}
run evidence/commands/school_cpu_environment.txt "$PYTHON_BIN" -B scripts/environment.py --device cpu --label school-cpu --threads 1 --output evidence/environment/school_cpu.json
run evidence/commands/school_cpu_softmax_correctness.txt "$PYTHON_BIN" -B scripts/check_softmax.py --device cpu --threads 1 --output evidence/correctness/school_softmax_cpu.json
run evidence/commands/school_cpu_attention_correctness.txt "$PYTHON_BIN" -B scripts/check_attention.py --device cpu --threads 1 --output evidence/correctness/school_attention_cpu.json
run evidence/commands/school_cpu_naive.txt "$PYTHON_BIN" -B scripts/profile_workload.py cpu-naive --threads 1 --output-dir evidence/cpu
