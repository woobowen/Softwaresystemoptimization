set -eu
cd /home/bwwu/lab/SSO_A3_preflight
printf 'RECONNECT_UTC: '; date -u --iso-8601=seconds
printf 'Detached CPU job output:\n'; cat logs/detached.log
printf 'Detached exit status: '; cat logs/detached.exitcode
printf 'Own background PID state (if retained as zombie):\n'
pid=$(cat logs/detached.pid)
ps -p "$pid" -o pid=,stat=,comm= || true
printf '\nUNMASKED CUDA DEVICE ENUMERATION (no tensor allocations)\n'
PYTHONDONTWRITEBYTECODE=1 /data/bwwu/envs/tiger/bin/python -B - <<'META'
import torch
print('is_available:',torch.cuda.is_available())
print('device_count:',torch.cuda.device_count())
print('context_initialized:',torch.cuda.is_initialized())
META
