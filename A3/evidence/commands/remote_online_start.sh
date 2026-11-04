set -eu
cd /home/bwwu/lab/SSO_A3
test "$(cat jobs/softmax.exitcode)" = 0
test ! -e jobs/online.pid
nohup bash jobs/worker.sh online > jobs/online.log 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > jobs/online.pid
printf 'Online job PID: %s\n' "$pid"
