import json
import math
from pathlib import Path
import random
import subprocess
import time

p1 = Path.cwd()
space = [(s, opt) for s in (8, 16, 24, 64, 128) for opt in ('O0', 'O1', 'O2', 'O3')]
commands, checked = [], []
for algorithm in ('grid', 'random', 'greedy'):
    output = Path('.cache/control-' + algorithm + '.jsonl')
    command = ['python3', '-B', 'src/autotuner.py', 'search', '--target', '.cache/small.c',
               '--algorithm', algorithm, '--budget', '20', '--seed', '17', '--repeats', '1',
               '--timeout', '30', '--cache-dir', '.cache/small-build', '--output', str(output)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert rows[0]['metadata']['target']['n'] == 129
    starts = [r for r in rows if r['type'] == 'measurement_start']
    measurements = [r for r in rows if r['type'] == 'measurement']
    trials = [r for r in rows if r['type'] == 'trial']
    configurations = [(r['config']['s'], r['config']['opt']) for r in trials]
    assert len(starts) == len(measurements) == len(trials) == rows[-1]['process_runs']
    assert 0 < len(trials) <= 20 and len(set(configurations)) == len(trials)
    for row in measurements:
        assert row['returncode'] == 0 and row['status'] == 'ok'
        assert math.isfinite(row['checksum']) and row['kernel_end_ns'] > row['kernel_start_ns']
        assert abs(float(row['stdout'].splitlines()[0]) -
                   (row['kernel_end_ns'] - row['kernel_start_ns']) / 1e9) <= .000000501
    if algorithm == 'grid':
        assert configurations == space
    elif algorithm == 'random':
        order = list(space); random.Random(17).shuffle(order)
        assert configurations == order
    else:
        current = random.Random(17).choice(space)
        scores = {}
        for trial, actual in zip(trials, configurations):
            while current in scores:
                si = [8, 16, 24, 64, 128].index(current[0]); oi = ['O0','O1','O2','O3'].index(current[1])
                nearby = [c for c in space if c != current and
                          ((c[1] == current[1] and abs([8,16,24,64,128].index(c[0])-si) == 1)
                           or (c[0] == current[0] and abs(['O0','O1','O2','O3'].index(c[1])-oi) == 1))]
                pending = [c for c in nearby if c not in scores]
                if pending:
                    expected = pending[0]; break
                winner = min([current, *nearby], key=lambda c: scores[c])
                assert scores[winner] < scores[current]
                current = winner
            else:
                expected = current
            assert actual == expected
            scores[actual] = trial['score']
        assert rows[-1]['stop_reason'] in ('budget', 'local_optimum')
    assert rows[-1]['failed_runs'] == 0 and rows[-1]['failed_trials'] == 0
    commands.append(command)
    checked.append(dict(algorithm=algorithm, n=129, actual_calls=len(starts),
                        distinct=len(set(configurations)), stop_reason=rows[-1]['stop_reason'],
                        returned=rows[-1]['best']['config'], failed_runs=0))
    print(json.dumps(checked[-1]), flush=True)
(p1/'.cache/minimal-control-check.json').write_text(json.dumps(dict(commands=commands, checked=checked,
    n4096_calls=0, claim='same-source small matrix control flow only; not formal performance'), indent=2)+'\n')
