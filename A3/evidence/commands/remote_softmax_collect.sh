set -eu
cd /home/bwwu/lab/SSO_A3
test "$(cat jobs/softmax.exitcode)" = 0
tar -czf softmax_results.tar.gz evidence/environment evidence/correctness evidence/gpu evidence/commands jobs/correctness.log jobs/correctness.exitcode jobs/softmax.log jobs/softmax.exitcode
sha256sum softmax_results.tar.gz
printf '\nFORMAL GPU METADATA\n'
cat evidence/gpu/*.metadata.json
