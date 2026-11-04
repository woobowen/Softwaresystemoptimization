set -eu
printf '$ cat A3/evidence/cpu/cpu_naive.cpu_table.txt\n'
cat A3/evidence/cpu/cpu_naive.cpu_table.txt
printf '\nSaved metadata: A3/evidence/cpu/cpu_naive.metadata.json (selected fields)\n'
python3 - <<'FIELDS'
import json
m=json.load(open('A3/evidence/cpu/cpu_naive.metadata.json'))
for key in ['experiment','dtype','cpu_threads','shapes','calls','warmup_calls','with_stack','seed','max_abs_error','max_row_sum_error']: print(f'{key}: {m[key]}')
FIELDS
