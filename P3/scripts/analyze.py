#!/usr/bin/env python3
import csv, pathlib, statistics, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
source = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
with source.open(newline='') as f: rows = list(csv.DictReader(f))
paths = ['arm-gcc', 'arm-clang', 'native-gcc', 'native-clang']; args = sorted({int(r['argument']) for r in rows})
with (out/'summary.csv').open('w', newline='') as f:
    w=csv.writer(f); w.writerow(['path','argument','samples_seconds','median_seconds','min_seconds','max_seconds'])
    for p in paths:
        for a in args:
            samples = [float(r['seconds']) for r in rows if r['path']==p and int(r['argument'])==a and r['exit']=='0']
            if not samples: raise ValueError((p,a))
            w.writerow([p,a,';'.join(f'{x:.6f}' for x in samples),f'{statistics.median(samples):.6f}',f'{min(samples):.6f}',f'{max(samples):.6f}'])
labels = {'arm-gcc':'AArch64 GCC / QEMU','arm-clang':'AArch64 Clang / QEMU','native-gcc':'x86-64 GCC / native','native-clang':'x86-64 Clang / native'}
for name, selected in [('qemu-comparison.png', paths[:2]),('all-comparison.png',paths)]:
    fig, ax=plt.subplots(figsize=(9,5.2))
    for p in selected:
        y=[statistics.median(float(r['seconds']) for r in rows if r['path']==p and int(r['argument'])==a and r['exit']=='0') for a in args]
        ax.plot(args,y,marker='o',label=labels[p])
    ax.set_xlabel('Iteration multiplier (N = 1024)'); ax.set_ylabel('Elapsed time (s), median'); ax.set_ylim(bottom=0); ax.grid(alpha=.3); ax.legend(); fig.tight_layout(); fig.savefig(out/name,dpi=160); plt.close(fig)
