set -eu
set -x
cat P2/evidence/commands/writeup1-debug-build.txt
cat P2/evidence/commands/writeup1-release-build.txt
rg '^w1-' P2/evidence/profiling/cache-summary.txt
cat P2/evidence/performance/writeup1-debug/summary.csv
cat P2/evidence/performance/writeup1-release/summary.csv
