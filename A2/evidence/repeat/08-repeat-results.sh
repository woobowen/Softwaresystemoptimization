set -euo pipefail
cd /home/addaswsw/lab/Software_system_optimization
PS4='$ '
set -x
python3 A2/scripts/summarize-spec.py A2/results/repeat > A2/evidence/repeat/statistics.json
python3 - <<'PY'
import json
from pathlib import Path
d = json.loads(Path('A2/evidence/repeat/statistics.json').read_text())
s = d['statistics']
m = d['runs'][0]['measurements'][s['workload']]
print('Workload:', s['workload'], '| Unit:', s['unit'])
print('Threads:', m['configuration']['numberBmThreads'])
print('Warmup:', int(m['warmup'][0]['expectedDuration']) // 1000, 's | Measurement:', int(m['iterations'][0]['expectedDuration']) // 1000, 's')
print('\nRun  Raw file                 Score (ops/m)')
for n, r in enumerate(d['runs'], 1):
    print(f"{n:>3}  {Path(r['raw_file']).name:<23} {r['workloads_ops_m'][s['workload']]:>10.2f}")
print()
for name in ('mean', 'min', 'max', 'range'):
    print(f'{name:<16} {s[name]:.2f} ops/m')
print(f"relative range   {s['relative_range_percent']:.2f}%")
PY
