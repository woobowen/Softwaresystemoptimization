#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN=${PYTHON_BIN:-python3}
: "${CUDA_VISIBLE_DEVICES:?Set CUDA_VISIBLE_DEVICES to one physical GPU UUID}"
mkdir -p evidence/commands evidence/environment
run() {
    local log=$1
    shift
    test ! -e "$log"
    printf '%q ' "$@" | tee "$log"
    printf '\n' | tee -a "$log"
    "$@" 2>&1 | tee -a "$log"
}
snapshot() {
    run "evidence/commands/gpu_before_$1.txt" "$PYTHON_BIN" -B scripts/gpu_status.py
}

phase=${1:-all}
case "$phase" in
    correctness|softmax|online|attention|all) ;;
    *) printf 'Unknown phase: %s\n' "$phase" >&2; exit 2 ;;
esac
if [[ "$phase" == correctness || "$phase" == all ]]; then
    snapshot correctness
    run evidence/commands/school_gpu_environment.txt "$PYTHON_BIN" -B scripts/environment.py --device cuda --label school-gpu --threads 1 --output evidence/environment/school_gpu.json
    run evidence/commands/school_gpu_softmax_correctness.txt "$PYTHON_BIN" -B scripts/check_softmax.py --device cuda --threads 1 --output evidence/correctness/school_softmax_cuda.json
    run evidence/commands/school_gpu_triton_correctness.txt "$PYTHON_BIN" -B scripts/check_triton.py --output evidence/correctness/school_triton.json
    run evidence/commands/school_gpu_attention_correctness.txt "$PYTHON_BIN" -B scripts/check_attention.py --device cuda --threads 1 --output evidence/correctness/school_attention_cuda.json
fi
if [[ "$phase" == softmax || "$phase" == all ]]; then
    for experiment in gpu-naive gpu-triton; do
        snapshot "$experiment"
        run "evidence/commands/school_${experiment}.txt" "$PYTHON_BIN" -B scripts/profile_workload.py "$experiment" --threads 1 --output-dir evidence/gpu
    done
fi
if [[ "$phase" == online || "$phase" == all ]]; then
    for experiment in online-naive online; do
        snapshot "$experiment"
        run "evidence/commands/school_${experiment}.txt" "$PYTHON_BIN" -B scripts/profile_workload.py "$experiment" --threads 1 --output-dir evidence/online
    done
fi
if [[ "$phase" == attention || "$phase" == all ]]; then
    for length in 128 512 2048; do
        snapshot "attention_$length"
        run "evidence/commands/school_attention_${length}.txt" "$PYTHON_BIN" -B scripts/profile_workload.py attention --length "$length" --threads 1 --output-dir evidence/attention
    done
fi
