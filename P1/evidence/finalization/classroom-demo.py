import json
from pathlib import Path
import shlex
import subprocess

def execute(command, label):
    print('$ ' + shlex.join(command), flush=True)
    result = subprocess.run(command, capture_output=True, text=True)
    Path('.cache/' + label + '.stdout.txt').write_text(result.stdout)
    Path('.cache/' + label + '.stderr.txt').write_text(result.stderr)
    if result.returncode:
        print(result.stderr, flush=True)
        raise SystemExit(result.returncode)
    return json.loads(result.stdout)

command = ['python3', '-B', 'src/autotuner.py', 'build', '--cache-dir', '.cache/classroom-build',
           '--output', '.cache/cold-build.jsonl']
data = execute(command, 'build')
assert len(data['builds']) == 4
for row in data['builds']:
    assert row['status'] == 'ok' and not row['cached'] and row['compile']['returncode'] == 0
    print('gcc ' + ' '.join(row['flags']) + '  exit=0 cached=false', flush=True)
command = ['taskset', '-c', '0', 'python3', '-B', 'src/autotuner.py', 'run', '--s', '128',
           '--opt', 'O3', '--repeats', '1', '--timeout', '1200',
           '--cache-dir', '.cache/classroom-build', '--output', '.cache/fresh-n4096.jsonl']
data = execute(command, 'run')
rows = [json.loads(line) for line in Path('.cache/fresh-n4096.jsonl').read_text().splitlines()]
header = rows[0]['metadata']
measurement = next(r for r in rows if r['type'] == 'measurement')
assert header['target']['n'] == 4096 and header['runtime_affinity'] == [0]
assert data['process_runs'] == 1 and data['failed_runs'] == 0 and data['compile_processes'] == 0
assert measurement['status'] == 'ok' and measurement['returncode'] == 0
assert measurement['kernel_end_ns'] > measurement['kernel_start_ns']
print(measurement['stdout'], end='', flush=True)
print('target exit=0  n=4096  s=128  O3  calls=1  failed=0', flush=True)
print(f"process RAW={measurement['process_raw_s']:.6f} s; kernel clock={measurement['kernel_clock']}", flush=True)
