set -eu
cd /home/bwwu/lab/SSO_A3
test "$(cat jobs/online.exitcode)" = 0
test ! -e jobs/attention.pid
nohup bash jobs/worker.sh attention > jobs/attention.log 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > jobs/attention.pid
printf 'Attention job PID: %s\n' "$pid"
