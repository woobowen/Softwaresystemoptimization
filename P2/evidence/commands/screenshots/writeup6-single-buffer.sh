set -eu
set -x
nl -ba P2/homework/sort_m.c | sed -n '53,73p'
rg '^(sort_c |sort_m )' P2/evidence/profiling/cache-summary.txt
cat P2/evidence/correctness/extremes-asan.txt
