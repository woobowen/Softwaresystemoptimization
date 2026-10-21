set -eu
set -x
sed -n '5,12p' P2/evidence/profiling/checkoff1/annotate.txt
nl -ba P2/recitation/isort.c | sed -n '16,24p'
sed -n '/11cb:/,/11f0:/p' P2/evidence/profiling/checkoff1/opcodes.txt
rg '11e2:|11ea:|11f0:|1212:' P2/evidence/profiling/checkoff1/annotate.txt
