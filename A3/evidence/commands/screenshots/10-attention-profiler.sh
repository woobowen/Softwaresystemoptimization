set -eu
printf '$ cat A3/evidence/attention/attention_l512.device_table.txt\n'
cat A3/evidence/attention/attention_l512.device_table.txt
printf '\nFP32, dk=dv=64, matmul precision=highest (TF32 off), 10 profiled calls per size:\n'
python3 - <<'FIELDS'
import json
m=json.load(open('A3/evidence/review/derived_results.json'))
for length in [128,512,2048]:
 p=m['profiles'][f'attention_l{length}']
 print('L=',length, 'GPU kernel us/call=',round(p['kernel_us_per_call'],4), 'no-profiler sync median ms=',p['synchronized_call_median_ms'], 'max abs error=',p['max_abs_error'])
p=m['profiles']['attention_l512']
for stage,s in p['stages'].items(): print(stage, 'GPU us/call=',round(s['us_per_call'],4), 'share=',round(s['percent'],3),'%', 'kernel count=',s['kernel_count'])
print('L512 model:',p['model'])
FIELDS
