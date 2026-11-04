set -eu
printf '$ cat A3/evidence/gpu/gpu_naive.cpu_table.txt\n'
cat A3/evidence/gpu/gpu_naive.cpu_table.txt
printf '\nFiltered rankings from all rows (200 complete calls):\n'
python3 - <<'FIELDS'
import json
s=json.load(open('A3/evidence/gpu/gpu_naive.statistics.json'))
print('CPU total top3 (ms):',[(r['name'],round(r['cpu_total_us']/1000,6)) for r in s['cpu_top3']])
print('CUDA total top3 (ms):',[(r['name'],round(r['device_total_us']/1000,6)) for r in s['device_top3']])
print('Total GPU kernels:',s['gpu_kernel_count'])
print('Sum of GPU kernel durations:',s['gpu_kernel_total_us'],'us')
print('GPU kernel time / complete call:',s['gpu_kernel_us_per_complete_call'],'us')
FIELDS
