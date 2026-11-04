#!/usr/bin/env bash
# Run one bounded preflight stage in the isolated workspace.
set -eu
stage=${1:?cpu/cuda/triton/extras required}
case "$stage" in cpu|cuda|triton|extras) ;; *) exit 2 ;; esac
work=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
test ! -e "$work/logs/$stage.log" || { echo 'Refusing to replace previous run' >&2; exit 23; }
export PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$work/cache"
export TRITON_CACHE_DIR="$work/cache/triton"
export CUDA_CACHE_PATH="$work/cache/cuda"
export TORCHINDUCTOR_CACHE_DIR="$work/cache/inductor"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export CUDA_DEVICE_ORDER=PCI_BUS_ID
if test "$stage" = cpu; then
    export CUDA_VISIBLE_DEVICES=""
else
    export CUDA_VISIBLE_DEVICES=GPU-dfff0e95-1db6-e2f4-3431-55bb852fa0ae
    state=$(nvidia-smi -i "$CUDA_VISIBLE_DEVICES" --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits)
    printf 'UTC: '; date -u --iso-8601=seconds
    printf 'Physical GPU 0 %s: %s\n' "$CUDA_VISIBLE_DEVICES" "$state"
    # Refuse to start if the selected GPU has become busy. Do not affect its users.
    util=${state%%,*}; used=${state##*,}
    if test "$util" -gt 5 || test "$used" -gt 512; then
        echo 'Selected GPU is no longer sufficiently idle; stage skipped' >&2
        exit 75
    fi
fi
cd "$work"
set +e
timeout 180 /data/bwwu/envs/tiger/bin/python -B -u preflight_smoke.py "$stage" --workdir "$work" > "logs/$stage.log" 2>&1
rc=$?
set -e
printf '%s\n' "$rc" > "logs/$stage.exitcode"
cat "logs/$stage.log"
printf '\nREMOTE_STAGE_EXIT_CODE=%s\n' "$rc"
exit "$rc"
