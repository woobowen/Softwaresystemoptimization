set -eu
cd /home/bwwu/lab/SSO_A3
test "$(cat jobs/online.exitcode)" = 0
tar -czf online_results.tar.gz evidence/online evidence/commands/gpu_before_online*.txt evidence/commands/school_online*.txt jobs/online.log jobs/online.exitcode
sha256sum online_results.tar.gz
cat evidence/online/*.metadata.json
