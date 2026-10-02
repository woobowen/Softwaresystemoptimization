"""Capture one real command and print a short view for the native terminal."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import textwrap
import time

stage, command = sys.argv[1], sys.argv[2:]
directory = Path(__file__).resolve().parent
print('\n'.join(textwrap.wrap('$ ' + shlex.join(command), width=110,
                               break_long_words=False, break_on_hyphens=False)), flush=True)
started_at = datetime.now(timezone.utc).isoformat()
started = time.monotonic()
result = subprocess.run(command, capture_output=True)
wall = time.monotonic() - started
stdout = directory / (stage + '.stdout.txt')
stderr = directory / (stage + '.stderr.txt')
stdout.write_bytes(result.stdout)
stderr.write_bytes(result.stderr)
record = dict(stage=stage, command=command, started_at=started_at,
              ended_at=datetime.now(timezone.utc).isoformat(), returncode=result.returncode,
              external_wall_monotonic_s=wall, stdout=str(stdout), stderr=str(stderr))
with (directory / 'steps.jsonl').open('a') as stream:
    stream.write(json.dumps(record) + '\n')
    stream.flush()
    os.fsync(stream.fileno())
if result.returncode:
    print(result.stderr.decode('utf-8', errors='replace'), flush=True)
    raise SystemExit(result.returncode)
if stage == 'unittest':
    report = result.stderr.decode('utf-8')
    assert 'Ran 54 tests' in report and report.rstrip().endswith('OK'), report
    assert 'skipped' not in report.lower(), report
    print('\n'.join(report.strip().splitlines()[-4:]))
elif stage == 'build':
    builds = json.loads(result.stdout)['builds']
    assert len(builds) == 4 and all(not row['cached'] and row['status'] == 'ok' for row in builds)
    for row in builds:
        print(f"{row['opt']}: {' '.join(row['flags'])}  sha256={row['binary_sha256'][:16]}  rc={row['compile']['returncode']}")
    print(f"Cold build: {len(builds)} binaries; source sha256={builds[0]['source_sha256'][:16]}")
elif stage == 'run':
    output = Path(command[command.index('--output') + 1])
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    metadata = rows[0]['metadata']
    measurement = next(row for row in rows if row['type'] == 'measurement')
    summary = rows[-1]
    build = next(row for row in rows if row['type'] == 'build')
    guard = measurement['kernel_s'] <= measurement['process_wall_s'] + .005
    assert metadata['target']['n'] == 4096 and metadata['runtime_affinity'] == [0]
    assert measurement['status'] == 'ok' and measurement['returncode'] == 0 and guard
    assert summary['process_runs'] == 1 and summary['compile_processes'] == 0 and build['cached']
    print(f"n={metadata['target']['n']} s=128 O3 repeats=1 CPU={metadata['runtime_affinity']} rc={measurement['returncode']}")
    print(f"kernel={measurement['kernel_s']:.6f}s  process_wall={measurement['process_wall_s']:.6f}s")
    print(f"checksum={measurement['checksum']:.17g}")
    print(f"O3 cache_hit={build['cached']}; compile processes={summary['compile_processes']}; CLOCK_MONOTONIC guard={guard}")
    print(f"binary sha256={measurement['binary_sha256']}")
print(f"{stage}: exit={result.returncode} external wall={wall:.6f}s", flush=True)
