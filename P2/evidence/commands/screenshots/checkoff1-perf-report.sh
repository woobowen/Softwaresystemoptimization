set -eu
set -x
cat P2/evidence/commands/checkoff1-build.txt
sed -n '1,15p' P2/evidence/profiling/checkoff1/report.txt
sed -n '1,12p' P2/evidence/environment/perf-hardware-check.txt
