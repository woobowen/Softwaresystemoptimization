set -eu
set -x
nl -ba P2/homework/sort_f.c | tail -13
rg 'sort_m |sort_f ' P2/evidence/profiling/versions/allocation-counts.txt
sed -n '6,18p' P2/evidence/profiling/perf-versions/sort_m-report.txt
sed -n '6,15p' P2/evidence/profiling/perf-versions/sort_f-report.txt
