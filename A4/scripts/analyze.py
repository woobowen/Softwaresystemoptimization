#!/usr/bin/env python3
import csv
import re
import statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent.parent
formal = root / 'results' / 'formal'
compilers = ('gcc', 'clang')
all_rows = []
summary = []
expected = None
for compiler in compilers:
    for level in range(4):
        name = f'{compiler}-O{level}'
        totals = []
        for run in range(1, 4):
            text = (formal / f'{name}.run{run}.txt').read_text()
            pairs = re.findall(r'^\s*\d+\s+"([^"]+)"\s+([0-9.]+) sec', text, re.M)
            labels = [x[0] for x in pairs]
            if len(pairs) != 144 or (expected is not None and labels != expected):
                raise ValueError(f'Unexpected labels: {name} run {run}')
            expected = labels
            values = [float(x[1]) for x in pairs]
            if min(values) <= 0:
                raise ValueError('Nonpositive value')
            totals.append(sum(values))
            all_rows.extend((compiler, level, run, label, value) for label, value in zip(labels, values))
        size = int((formal / f'{name}.size.txt').read_text().split()[1])
        summary.append((compiler, level, *totals, statistics.median(totals), min(totals), max(totals), size))
with (root / 'results' / 'subtests.csv').open('w', newline='') as f:
    w = csv.writer(f); w.writerow(['compiler','opt_level','run','subtest','cpu_seconds']); w.writerows(all_rows)
with (root / 'results' / 'summary.csv').open('w', newline='') as f:
    w = csv.writer(f); w.writerow(['compiler','opt_level','run1_seconds','run2_seconds','run3_seconds','median_seconds','min_seconds','max_seconds','file_bytes']); w.writerows(summary)
for metric, title, ylabel, filename in [('time','loop_fusion: sum of 144 subtest CPU times','CPU time (seconds; median, range)', 'runtime.png'), ('size','loop_fusion executable size','File size (bytes)', 'size.png')]:
    fig, ax = plt.subplots(figsize=(9,5))
    x = list(range(4)); width = .35
    for j, compiler in enumerate(compilers):
        entries = [row for row in summary if row[0] == compiler]
        pos = [i + (j-.5)*width for i in x]
        vals = [row[5] if metric == 'time' else row[8] for row in entries]
        kwargs = {}
        if metric == 'time':
            kwargs['yerr'] = [[row[5]-row[6] for row in entries], [row[7]-row[5] for row in entries]]
            kwargs['capsize'] = 4
        ax.bar(pos, vals, width, label=compiler.upper(), **kwargs)
    ax.set_xticks(x, ['O0','O1','O2','O3']); ax.set_xlabel('Optimization level')
    ax.set_ylabel(ylabel); ax.set_title(title); ax.legend(); ax.grid(axis='y', alpha=.25)
    fig.tight_layout(); fig.savefig(root / 'images' / filename, dpi=160); plt.close(fig)
