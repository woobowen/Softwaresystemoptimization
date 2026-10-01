set -euo pipefail
cd /home/addaswsw/lab/Software_system_optimization
PS4='$ '
set -x
python3 A2/scripts/summarize-spec.py A2/results/repeat --compare A2/results/parameter > A2/evidence/parameter/comparison.json
python3 - <<'PY'
import json
from pathlib import Path
d = json.loads(Path('A2/evidence/parameter/comparison.json').read_text())
p = json.loads(Path('A2/evidence/parameter/selection.json').read_text())
print('Workload:', p['workload'], '| Unit: ops/m')
print('Only added JVM option:', p['one_jvm_option'])
print('UseSerialGC:', p['default']['UseSerialGC'], '->', p['modified']['UseSerialGC'])
print('UseParallelGC:', p['default']['UseParallelGC'], '->', p['modified']['UseParallelGC'])
print('\nConfiguration       Run 1      Run 2      Run 3       Mean')
for key in ('original', 'modified'):
    s = d[key]['statistics']
    numbers = [*s['scores'], s['mean']]
    print(f'{key:<15}' + ''.join(f'{v:>11.2f}' for v in numbers))
print(f"\nMean change: {d['percentage_change']:+.2f}%")
for key in ('original', 'modified'):
    s = d[key]['statistics']
    print(f"{key:<9} range: {s['range']:.2f} ops/m ({s['relative_range_percent']:.2f}%)")
    print('Raw files:', ', '.join(Path(r['raw_file']).name for r in d[key]['runs']))
PY
