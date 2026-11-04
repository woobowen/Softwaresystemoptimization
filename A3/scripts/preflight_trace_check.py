#!/usr/bin/env python3
"""Check unmodified PyTorch traces using the real Perfetto SQL importer."""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess


def check(trace, processor):
    events = json.loads(trace.read_text())["traceEvents"]
    counts = collections.Counter(e.get("cat") for e in events if e.get("ph") == "X")
    kernels = [e for e in events if e.get("cat") == "kernel"]
    assert all(e["dur"] > 0 and isinstance(e["ts"], (int, float)) for e in kernels)
    marker = "teacher_softmax_preflight.py%softmax" if trace.name.startswith("triton") else (
        "preflight_smoke.py%attention" if trace.name.startswith("attention") else
        "preflight_smoke.py%naive_softmax")
    query = f"""
    WITH RECURSIVE ancestors(kernel_id, id, parent_id, name) AS (
      SELECT k.id, launch.id, launch.parent_id, launch.name
      FROM flow f JOIN slice k ON k.id=f.slice_in
      JOIN slice launch ON launch.id=f.slice_out
      WHERE k.category='kernel'
      UNION ALL
      SELECT a.kernel_id, p.id, p.parent_id, p.name
      FROM ancestors a JOIN slice p ON p.id=a.parent_id
    )
    SELECT
      (SELECT COUNT(*) FROM slice WHERE category='cpu_op') AS cpu_ops,
      (SELECT COUNT(*) FROM slice WHERE category='python_function') AS python_frames,
      (SELECT COUNT(*) FROM slice WHERE category='kernel') AS gpu_kernels,
      (SELECT SUM(dur) FROM slice WHERE category='kernel') AS kernel_duration_ns,
      (SELECT COUNT(*) FROM slice WHERE category='kernel' AND (dur<=0 OR ts IS NULL)) AS bad_kernels,
      (SELECT COUNT(*) FROM flow f JOIN slice k ON k.id=f.slice_in WHERE k.category='kernel') AS kernel_flows,
      (SELECT COUNT(DISTINCT kernel_id) FROM ancestors WHERE name LIKE '%{marker}%') AS kernels_with_python_parent,
      (SELECT COUNT(*) FROM slice WHERE name='aten::exp') AS exp_calls,
      (SELECT SUM(dur) FROM slice WHERE name='aten::exp') AS exp_total_ns,
      (SELECT SUM(value) FROM stats WHERE name='slice_spill_overlapping_complete_event') AS spill_count,
      (SELECT COALESCE(SUM(value),0) FROM stats WHERE severity IN ('error','data_loss')
         AND name!='slice_spill_overlapping_complete_event') AS other_import_errors;
    """
    command = [str(processor), "query", "--quiet", "--format", "csv", str(trace), query]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    row = next(csv.DictReader(io.StringIO(proc.stdout)))
    for key in row:
        row[key] = None if row[key] == "[NULL]" else int(row[key])
    assert row["cpu_ops"] == counts["cpu_op"]
    assert row["python_frames"] == counts["python_function"] > 0
    assert row["gpu_kernels"] == len(kernels)
    assert row["kernel_flows"] == row["kernels_with_python_parent"] == len(kernels)
    assert row["bad_kernels"] == row["other_import_errors"] == 0
    assert row["spill_count"] == 1  # diagnostic below explains this retained warning

    grouped = collections.defaultdict(list)
    for e in events:
        if e.get("ph") == "X":
            grouped[(e["pid"], e["tid"])].append(e)
    overlaps = []
    for group in grouped.values():
        stack = []
        for e in sorted(group, key=lambda x: (x["ts"], -x["dur"])):
            while stack and stack[-1]["ts"] + stack[-1]["dur"] <= e["ts"]:
                stack.pop()
            if stack and e["ts"] + e["dur"] > stack[-1]["ts"] + stack[-1]["dur"] + 0.001:
                prior = stack[-1]
                assert "preflight::" in prior["name"] or "preflight::" in e["name"]
                assert prior.get("cat") not in ("cpu_op", "kernel")
                assert e.get("cat") not in ("cpu_op", "kernel")
                overlaps.append({"first": prior["name"], "second": e["name"]})
            stack.append(e)
    return {"trace": str(trace), "bytes": trace.stat().st_size,
            "sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
            "perfetto": row, "overlaps": overlaps,
            "warning": "Custom record_function scope overlaps its Python enter/exit frames; "
                       "Perfetto retains the event on an overflow track. No ATen/kernel data lost.",
            "result": "PASS_WITH_WARNING", "argv": command,
            "sql_stdout": proc.stdout, "sql_stderr": proc.stderr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_directory", type=Path)
    parser.add_argument("processor", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    results = [check(p, args.processor.resolve()) for p in sorted(args.trace_directory.glob("*.json"))]
    assert len(results) == 4
    assert sum(r["perfetto"]["gpu_kernels"] for r in results) == 10
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    for r in results:
        print(Path(r["trace"]).name, r["perfetto"], r["result"])


if __name__ == "__main__":
    main()
