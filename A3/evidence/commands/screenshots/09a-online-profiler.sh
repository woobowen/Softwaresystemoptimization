set -eu
printf '$ cat A3/evidence/online/online.cpu_table.txt\n'
cat A3/evidence/online/online.cpu_table.txt
printf '\nFull 100x5000 FP32 comparison; 1 profiled call each, with_stack=False:\n'
python3 - <<'FIELDS'
import json
m=json.load(open('A3/evidence/review/derived_results.json'))
for name in ['online_naive','online']:
 p=m['profiles'][name]
 print(name, 'kernels=',p['kernel_count'], 'GPU kernel total=',round(p['kernel_total_us']/1000,6),'ms', 'max abs error=',p['max_abs_error'])
 print('  no-profiler synchronized call median (5 repetitions):',p['synchronized_call_median_ms'],'ms')
print('Synchronized latency slowdown:',m['online_wall_slowdown'])
FIELDS
