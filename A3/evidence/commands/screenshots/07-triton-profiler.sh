set -eu
printf '$ cat A3/evidence/gpu/gpu_triton.device_table.txt\n'
cat A3/evidence/gpu/gpu_triton.device_table.txt
printf '\nSame input: 100x5000 FP32, seed=10245102410; 200 calls each\n'
python3 - <<'FIELDS'
import json
m=json.load(open('A3/evidence/review/derived_results.json'))
for name in ['gpu_naive','gpu_triton']:
 p=m['profiles'][name]
 print(name, 'kernels=',p['kernel_count'], 'GPU us/call=',round(p['kernel_us_per_call'],6), 'logical GB/s=',round(p['effective_GBps'],3), 'peak %=',round(p['percent_of_peak'],3))
 print('  no-profiler synchronized call median:',p['synchronized_call_median_ms'],'ms')
print('GPU kernel speedup:',m['gpu_kernel_speedup'])
print('Traffic: naive=16001600 B; Triton=4000000 B')
print('RTX4090 peak reference: 1008 GB/s (NVIDIA specification)')
print('Effective bandwidth is a logical estimate, not measured DRAM traffic.')
FIELDS
