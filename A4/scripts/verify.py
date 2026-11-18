#!/usr/bin/env python3
"""Independently check saved reports against the summary."""
from pathlib import Path
import csv
import hashlib
import re
import statistics

root = Path(__file__).resolve().parent.parent
formal = root / 'results/formal'
reports = sorted(formal.glob('*.run[123].txt'))
assert len(reports) == 24
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in reports}) == 24
with (root / 'results/summary.csv').open() as f:
    summaries = {(r['compiler'], int(r['opt_level'])): r for r in csv.DictReader(f)}
for compiler in ('gcc', 'clang'):
    for level in range(4):
        name = f'{compiler}-O{level}'
        cxx = 'g++' if compiler == 'gcc' else 'clang++'
        build = (formal / f'{name}.build.txt').read_text().splitlines()
        assert build[0].startswith('rm -f')
        assert build[1] == f'{cxx} -std=c++14 -I. -O{level} -o loop_fusion loop_fusion.cpp -lm'
        totals = []
        for run in range(1, 4):
            text = (formal / f'{name}.run{run}.txt').read_text()
            assert not re.search(r'failed|error|could not allocate', text, re.I)
            lines = [s for s in text.splitlines() if re.match(r'^\s*\d+\s+"', s)]
            assert len(lines) == 144
            values = [float(s.split(' sec')[0].rsplit(None, 1)[-1]) for s in lines]
            assert min(values) > 0
            groups = [float(x) for x in re.findall(r'^Total absolute time for .*: ([\d.]+) sec$', text, re.M)]
            assert len(groups) == 30 and abs(sum(values) - sum(groups)) < 0.0001
            totals.append(sum(values))
        row = summaries[compiler, level]
        assert all(abs(float(row[f'run{i}_seconds']) - totals[i-1]) < 1e-9 for i in range(1, 4))
        assert abs(float(row['median_seconds']) - statistics.median(totals)) < 1e-9
        assert int(row['file_bytes']) == int((formal / f'{name}.size.txt').read_text().split()[1])
        print(name, '3 reports, 144 rows, 30 groups, build and size agree; median', round(statistics.median(totals), 6))
for path in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', (root / 'README.md').read_text()):
    if not path.startswith('https://'):
        assert (root / path).exists(), path
print('24 distinct report hashes; README local links exist')
