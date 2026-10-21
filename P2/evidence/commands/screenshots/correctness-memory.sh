set -eu
set -x
cat P2/evidence/commands/sanitizer-build.txt
rg 'qsort reference' P2/evidence/correctness/asan-ubsan.txt
cat P2/evidence/correctness/extremes-asan.txt
tail -9 P2/evidence/correctness/memcheck.txt
