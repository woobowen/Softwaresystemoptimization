set -eu
cd /home/bwwu/lab/SSO_A3
test "$(cat jobs/correctness.exitcode)" = 0
test ! -e jobs/softmax.pid
nohup bash jobs/worker.sh softmax > jobs/softmax.log 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > jobs/softmax.pid
printf 'GPU Softmax job PID: %s\n' "$pid"
