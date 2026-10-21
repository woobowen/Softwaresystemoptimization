set -eu
set -x
rg "inlined into|not inlined into" P2/evidence/profiling/versions/inline-remarks.txt
rg ' [tT] (sort_a|sort_i|sort_recursive_i)$' P2/evidence/profiling/versions/symbol-sizes.txt
rg 'call.*(sort_recursive_i|merge_i|copy_i|mem_alloc)' P2/evidence/profiling/versions/sort_recursive_i-assembly.txt
cat P2/evidence/profiling/writeup3/text-sha256.txt
rg '^(sort_i |recursive-noinline)' P2/evidence/profiling/cache-summary.txt
