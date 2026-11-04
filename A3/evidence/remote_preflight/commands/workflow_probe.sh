set -u
work=/home/bwwu/lab/SSO_A3_preflight
cd "$work"
printf 'DETACHED_LAUNCH_UTC: '; date -u --iso-8601=seconds
nohup sh -c 'sleep 8; date -u --iso-8601=seconds; printf "detached_cpu_probe_complete\n"; printf "0\n" > logs/detached.exitcode' > logs/detached.log 2>&1 < /dev/null &
printf '%s\n' "$!" > logs/detached.pid
printf 'Own short CPU job PID: '; cat logs/detached.pid
printf '\nCPU TRACE INITIALIZATION DIAGNOSTIC\n'
PYTHONDONTWRITEBYTECODE=1 /data/bwwu/envs/tiger/bin/python - <<'DIAG'
import json, collections
j=json.load(open('traces/cpu_naive.trace.json'))
e=[e for e in j['traceEvents'] if e.get('cat')=='python_function']
print('Most common Python call frames:',collections.Counter(x['name'] for x in e).most_common(12))
print('Longest Python frames:',[(x['name'],x.get('dur')) for x in sorted(e,key=lambda x:x.get('dur',0),reverse=True)[:12]])
DIAG
printf '\nINTENTIONAL NONZERO REMOTE SCRIPT\n'
sh transfer_probe.sh > logs/transfer_probe.log 2>&1
rc=$?
cat logs/transfer_probe.log
printf 'REMOTE_PROBE_EXIT=%s\n' "$rc"
exit "$rc"
