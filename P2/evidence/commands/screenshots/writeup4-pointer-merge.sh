set -eu
set -x
nl -ba P2/homework/sort_p.c | sed -n '57,82p'
rg '^(sort_i |sort_p )' P2/evidence/profiling/cache-summary.txt
