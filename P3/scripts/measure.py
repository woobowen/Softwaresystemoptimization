#!/usr/bin/env python3
import csv, datetime, hashlib, os, pathlib, re, subprocess, sys, time
root = pathlib.Path(__file__).resolve().parents[1]
out = pathlib.Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=False)
qemu = os.environ.get('QEMU', 'qemu-aarch64')
programs = [('arm-gcc', 'loop.aarch64.gcc'), ('arm-clang', 'loop.aarch64.clang'), ('native-gcc', 'loop.x64.gcc'), ('native-clang', 'loop.x64.clang')]
values = [int(x) for x in sys.argv[2].split(',')]
repeats = int(sys.argv[3])
fields = ['run', 'path', 'argument', 'repeat', 'start_utc', 'end_utc', 'command', 'binary_sha256', 'source_sha256', 'stdout', 'stderr', 'exit', 'seconds']
with (out / 'runs.csv').open('x', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); f.flush()
    n = 0
    for rep in range(1, repeats + 1):
        for arg in values:
            for shift in range(4):
                label, name = programs[(shift + rep + values.index(arg)) % 4]
                binary = root / 'loop' / name
                cmd = ([qemu] if label.startswith('arm') else []) + [str(binary), str(arg)]
                n += 1; start = datetime.datetime.now(datetime.timezone.utc).isoformat()
                try:
                    p = subprocess.run(cmd, text=True, capture_output=True, timeout=300)
                    stdout, stderr, code = p.stdout, p.stderr, p.returncode
                except subprocess.TimeoutExpired as e:
                    stdout, stderr, code = str(e.stdout), 'TIMEOUT: ' + str(e.stderr), -1
                end = datetime.datetime.now(datetime.timezone.utc).isoformat()
                m = re.search(r'Elapsed execution time: (\d+\.\d{6}) sec; N: 1024, I: (\d+), __OP__: \+, __TYPE__: uint32_t', stdout)
                seconds = m.group(1) if m and int(m.group(2)) == arg * 100000 else ''
                row = dict(run=n, path=label, argument=arg, repeat=rep, start_utc=start, end_utc=end, command=' '.join(cmd), binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(), source_sha256=hashlib.sha256((root/'loop/loop.c').read_bytes()).hexdigest(), stdout=stdout, stderr=stderr, exit=code, seconds=seconds)
                writer.writerow(row); f.flush(); print(n, label, arg, rep, seconds, 'exit', code, flush=True)
                if code != 0 or not seconds: raise SystemExit('Run failed; preserved in runs.csv')
