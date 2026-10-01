#!/usr/bin/env python3
"""Check the completed seven-run campaign and write its timing/source tables."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

a2 = Path(__file__).resolve().parents[2]
root = a2 / "evidence/formal-campaign"


def read(path):
    return json.loads(path.read_text())


campaign = read(root / "campaign.json")
assert campaign["status"] == "MEASUREMENTS_COMPLETE"
assert all(read(root / "restore.json")["checks"].values())
assert read(root / "final-gate/timing-review.json")["status"] == "PASS"
assert read(root / "final-gate/independent-calculation.json")["all_checks_pass"]
assert len(campaign["completed_runs"]) == 7
parser_command = [sys.executable, "-B", str(a2 / "scripts/summarize-spec.py"),
                  str(a2 / "results/repeat"), "--compare", str(a2 / "results/parameter")]
comparison = json.loads(subprocess.check_output(parser_command, text=True))
(root / "final-statistics.json").write_text(json.dumps(comparison, indent=2) + "\n")
base = read(root / "base-parsed.json")["runs"][0]
parsed = {Path(r["raw_file"]).parent.name: r for r in
          [base] + comparison["original"]["runs"] + comparison["modified"]["runs"]}
records, pids, environments, configurations = [], [], [], []
previous_end = None
for completed in campaign["completed_runs"]:
    directory = root / completed["slot"]
    timing = read(directory / "timing-review.json")
    assert timing["status"] == "PASS" and all(timing["checks"].values())
    run = read(directory / "benchmark/run.json")
    assessment = read(directory / "benchmark/assessment.json")
    host = read(directory / "host-summary.json")
    native = parsed[completed["run_id"]]
    assert run["campaign_id"] == host["campaign_id"] == campaign["campaign_id"]
    assert run["exit_code"] == 0 and run["proc_cmdline"] == run["command"]
    assert assessment["checksum"] == assessment["correctness"] == "passed"
    assert native["unit"] == "ops/m"
    assert run["boot_id_start"] == run["boot_id_end"] == timing["boot_id"]
    assert run["clocksource_start"] == run["clocksource_end"] == "tsc"
    assert run["timesyncd_state_start"] == run["timesyncd_state_end"] == "inactive"
    assert host["power_line_before"] == host["power_line_after"] == "Online"
    assert host["power_scheme_before"] == host["power_scheme_after"]
    pids.append(run["pid"])
    environments.append(run["environment"])
    measure = native["measurements"]["compress"]
    configurations.append(measure["configuration"])
    assert measure["configuration"]["numberBmThreads"] == "22"
    assert measure["warmup"][0]["expectedDuration"] == "120000"
    assert measure["iterations"][0]["expectedDuration"] == "240000"
    kind = completed["slot"].split("-", 1)[0]
    expected = ["-jar", "SPECjvm2008.jar", "--base" if kind == "base" else "compress"]
    if kind == "parameter":
        expected.insert(0, "-XX:+UseSerialGC")
    assert run["command"][1:] == expected
    if kind == "base":
        assert len(native["workloads_ops_m"]) == 38 and native["violations"] == []
    else:
        assert list(native["workloads_ops_m"]) == ["compress"]
    manifests = read(directory / "benchmark/copy-manifest.json")
    for manifest in manifests:
        copied = Path(manifest["copy"])
        assert {str(p.relative_to(copied)) for p in copied.rglob("*") if p.is_file()} == set(manifest["sha256"])
        for name, digest in manifest["sha256"].items():
            assert hashlib.sha256((copied / name).read_bytes()).hexdigest() == digest
            assert hashlib.sha256((Path(manifest["source"]) / name).read_bytes()).hexdigest() == digest
    start = datetime.datetime.fromisoformat(run["start"])
    gap = None if previous_end is None else (start - previous_end).total_seconds()
    assert gap is None or gap >= 60
    previous_end = datetime.datetime.fromisoformat(run["end"])
    records.append({"slot": completed["slot"], "run_id": completed["run_id"],
        "pid": run["pid"], "command": run["command"], "proc_cmdline": run["proc_cmdline"],
        "start": run["start"], "end": run["end"], "gap_from_previous_runner_seconds": gap,
        "host_elapsed": timing["host_seconds"], "runner_wall": run["wall_clock_seconds"],
        "runner_monotonic": run["monotonic_seconds"],
        "host_minus_runner": timing["host_seconds"] - run["monotonic_seconds"],
        "host_minus_launcher": timing["host_minus_guest_seconds"],
        "monitor_wall_minus_monotonic": timing["wall_minus_monotonic_seconds"],
        "max_step": timing["largest_step_seconds"], "timing": "PASS",
        "native_status": native["native_status"], "violations": native["violations"],
        "file_count": sum(m["file_count"] for m in manifests),
        "resource_links": sum(m["relative_links_checked"] for m in manifests)})
assert len(set(pids)) == 7
assert all(e == environments[0] for e in environments)
assert all(c == configurations[0] for c in configurations)
default_mean = comparison["original"]["statistics"]["mean"]
context = {"base_compress": base["workloads_ops_m"]["compress"], "standalone_mean": default_mean,
    "standalone_vs_base_percent": (default_mean / base["workloads_ops_m"]["compress"] - 1) * 100,
    "same_compress_configuration": True,
    "explanation": "Same parser, JDK, environment and compress configuration. Base executes compress after other workloads in the same JVM; standalone runs use fresh JVMs. The measured context difference is retained without assigning an unmeasured cause or rerunning for score."}
audit = {"at": datetime.datetime.now().astimezone().isoformat(), "campaign_id": campaign["campaign_id"],
         "parser_command": parser_command, "all_checks_pass": True,
         "runs": records, "base_vs_standalone": context,
         "configuration": configurations[0], "fresh_jvm_pids": pids,
         "gc_flags_evidence": "gc-flags/summary.json: separate diagnostic JVMs; formal argv above"}
(root / "final-data-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
gate = read(root / "final-gate/timing-review.json")
rows = ["# 最终计时检查", "", "所有时间单位为秒。Gate 与七次正式运行均通过；这不是最终工程验收。", "",
        "| 运行 | Host elapsed | Guest monotonic | Host−guest | wall−monotonic | 最大单次 step | clocksource | timesyncd | boot ID | 状态 |",
        "|---|---:|---:|---:|---:|---:|---|---|---|---|"]
entries = [("Final Gate", gate["host_seconds"], gate["guest_monotonic_seconds"],
            gate["host_minus_guest_seconds"], gate["wall_minus_monotonic_seconds"], gate["largest_step_seconds"])]
entries += [(r["slot"] + " / " + r["run_id"], r["host_elapsed"], r["runner_monotonic"],
             r["host_minus_runner"], r["monitor_wall_minus_monotonic"], r["max_step"]) for r in records]
for label, host, guest, delta, wall, step in entries:
    rows.append(f"| {label} | {host:.9f} | {guest:.9f} | {delta:.9f} | {wall:.9f} | {step:.9f} | tsc | inactive | `{gate['boot_id']}` | PASS |")
rows += ["", "Guest monotonic：Gate 使用采样首末区间，benchmark 使用 runner 包围 Java 进程的区间。Host Stopwatch 包含 WSL 启动及外围监视器准备/清理，所以 Host−guest 小幅为正。逐次 timing-review.json 中的 host_minus_guest_seconds 则对比更外层 launcher；两个边界没有混用。",
         "", "wall−monotonic 与最大 step 来自原始 monitor 样本的独立计算；Gate 的最大 step 同时检查 Python 与 Java。没有超过 50 ms 的离散校正，没有睡眠、boot 或 clocksource 变化，服务在所有测量区间保持 inactive。",
         "", "[Gate 独立复算](final-gate/independent-calculation.json) · [八次计时边界与配置记录](final-data-audit.json) · [完整统计](final-statistics.json) · [服务及配置恢复](restore.json)"]
(root / "final-timing-audit.md").write_text("\n".join(rows) + "\n")
print(json.dumps({"runs": len(records), "checks": True, "statistics": {
    "default": comparison["original"]["statistics"], "serial": comparison["modified"]["statistics"],
    "change_percent": comparison["percentage_change"]}, "base_vs_standalone": context}, indent=2))
