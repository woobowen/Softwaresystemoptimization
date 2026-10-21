set -eu
set -x
cat P2/evidence/performance/thresholds/table.txt
nl -ba P2/homework/isort.c | sed -n '31,46p'
