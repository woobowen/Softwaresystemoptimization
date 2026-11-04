set -eu
cd /home/bwwu/lab/SSO_A3
tar -xzf source.tar.gz
printf 'SOURCE HASHES\n'
sha256sum src/*.py scripts/*.py scripts/*.sh
cat > jobs/worker.sh <<'WORKER'
#!/usr/bin/env bash
set -uo pipefail
cd /home/bwwu/lab/SSO_A3
export PYTHON_BIN=/data/bwwu/envs/tiger/bin/python
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export TRITON_CACHE_DIR=/home/bwwu/lab/SSO_A3/cache/triton
export CUDA_CACHE_PATH=/home/bwwu/lab/SSO_A3/cache/cuda
printf 'START UTC: '; date -u --iso-8601=seconds
case "$1" in
    cpu)
        export CUDA_VISIBLE_DEVICES=''
        bash scripts/run_cpu.sh
        ;;
    correctness|softmax|online|attention)
        export CUDA_VISIBLE_DEVICES=GPU-dfff0e95-1db6-e2f4-3431-55bb852fa0ae
        bash scripts/run_gpu.sh "$1"
        ;;
    *) exit 2 ;;
esac
status=$?
printf '%s\n' "$status" > "jobs/$1.exitcode"
printf 'END UTC: '; date -u --iso-8601=seconds
exit "$status"
WORKER
test ! -e jobs/cpu.pid
nohup bash jobs/worker.sh cpu > jobs/cpu.log 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > jobs/cpu.pid
printf 'CPU job PID: %s\n' "$pid"
