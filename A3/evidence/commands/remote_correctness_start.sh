set -eu
cd /home/bwwu/lab/SSO_A3
test "$(cat jobs/cpu.exitcode)" = 0
test ! -e jobs/correctness.pid
nohup bash jobs/worker.sh correctness > jobs/correctness.log 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > jobs/correctness.pid
printf 'Correctness job PID: %s\n' "$pid"
# CPU 结果在采集完成后打包；不含环境和编译缓存。
tar -czf cpu_results.tar.gz evidence jobs/cpu.log jobs/cpu.exitcode jobs/worker.sh
sha256sum cpu_results.tar.gz
