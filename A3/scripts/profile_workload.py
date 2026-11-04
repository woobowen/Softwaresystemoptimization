"""按题号串行采集 Profiler；每个命令只运行一个实验。"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from softmax import naive_softmax, online_softmax
from attention import attention


SEED = 10245102410


def synchronize(device):
    if device == "cuda":
        torch.cuda.synchronize()


def save_profile(prof, prefix, calls):
    trace_path = prefix.with_suffix(".trace.json")
    prof.export_chrome_trace(str(trace_path))
    averages = prof.key_averages()
    table = averages.table(sort_by="cpu_time_total", row_limit=-1)
    prefix.with_suffix(".cpu_table.txt").write_text(table + "\n")
    print(table)
    device_field = "device_time_total" if hasattr(averages[0], "device_time_total") else "cuda_time_total"
    self_device_field = "self_" + device_field
    rows = []
    for event in averages:
        rows.append({
            "name": event.key, "count": event.count,
            "cpu_total_us": event.cpu_time_total,
            "self_cpu_us": event.self_cpu_time_total,
            "cpu_avg_us": event.cpu_time_total / event.count,
            "device_total_us": getattr(event, device_field),
            "self_device_us": getattr(event, self_device_field),
            "device_type": str(event.device_type),
        })
    # 用原始 GPU kernel 事件求和，避免重复计入 ATen 父子节点。
    trace = json.loads(trace_path.read_text())
    kernels = [e for e in trace["traceEvents"]
               if e.get("ph") == "X" and e.get("cat") == "kernel"]
    kernel_total_us = sum(e["dur"] for e in kernels)
    eligible = [r for r in rows if r["name"].startswith("aten::")
                or (r["name"].startswith("softmax_kernel")
                    and "CUDA" in r["device_type"])]
    summary = {
        "calls": calls, "device_time_field": device_field,
        "profiler_self_cpu_total_us": sum(r["self_cpu_us"] for r in rows),
        "cpu_top3": sorted(eligible, key=lambda r: r["cpu_total_us"], reverse=True)[:3],
        "device_top3": sorted(
            [r for r in eligible if r["device_total_us"] > 0],
            key=lambda r: r["device_total_us"], reverse=True,
        )[:3],
        "gpu_kernel_count": len(kernels),
        "gpu_kernel_names": dict(Counter(e["name"] for e in kernels)),
        "gpu_kernel_total_us": kernel_total_us,
        "gpu_kernel_us_per_complete_call": kernel_total_us / calls,
        "trace_categories": dict(Counter(e.get("cat", "") for e in trace["traceEvents"])),
        "rows": rows,
    }
    prefix.with_suffix(".statistics.json").write_text(json.dumps(summary, indent=2) + "\n")
    if kernels:
        table = averages.table(sort_by=device_field, row_limit=-1)
        prefix.with_suffix(".device_table.txt").write_text(table + "\n")
        print(table)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", choices=("cpu-naive", "gpu-naive", "gpu-triton", "online-naive", "online", "attention"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--length", type=int, choices=(128, 512, 2048), default=512)
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")
    device = "cpu" if args.experiment == "cpu-naive" else "cuda"
    torch.set_num_threads(args.threads)
    torch.set_float32_matmul_precision("highest")
    if device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA is unavailable; no fallback experiment was run")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    generator = torch.Generator(device="cpu").manual_seed(SEED)
    metadata = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "experiment": args.experiment, "device": device, "dtype": "torch.float32",
        "seed": SEED, "cwd": str(Path.cwd()), "torch": torch.__version__,
        "cpu_threads": torch.get_num_threads(),
        "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        "input_generation": "CPU Generator then copy before warmup/profiling",
        "warmup_calls": 5, "timing_repetitions": 5,
        "timing_method": "perf_counter_ns; synchronize before and after each complete call; profiler disabled",
    }
    if device == "cuda":
        metadata["gpu"] = torch.cuda.get_device_name(0)
        metadata["cuda_visible_devices"] = os.environ.get("CUDA_VISIBLE_DEVICES")
        metadata["cuda_runtime"] = torch.version.cuda
    if args.experiment == "attention":
        length = args.length
        cpu_inputs = [torch.randn(length, 64, generator=generator, dtype=torch.float32) for _ in range(3)]
        inputs = [x.to(device) for x in cpu_inputs]
        function = lambda: attention(*inputs)
        reference = attention(*(x.double() for x in cpu_inputs)).to(device)
        calls = 10
        metadata["shapes"] = [list(x.shape) for x in inputs]
        metadata["reference"] = "CPU FP64 explicit attention from the same FP32 inputs"
        prefix = args.output_dir / f"attention_l{length}"
    else:
        cpu_input = torch.randn(100, 5000, generator=generator, dtype=torch.float32)
        cpu_inputs = [cpu_input]
        x = cpu_input.to(device)
        implementation = naive_softmax
        if args.experiment == "gpu-triton":
            from triton_softmax import softmax
            implementation = softmax
        elif args.experiment == "online":
            implementation = online_softmax
        function = lambda: implementation(x)
        reference = torch.softmax(x, dim=1)
        calls = 1 if args.experiment.startswith("online") else 200
        metadata["shapes"] = [list(x.shape)]
        metadata["reference"] = "torch.softmax(x, dim=1)"
        prefix = args.output_dir / args.experiment.replace("-", "_")
    metadata["input_sha256"] = [hashlib.sha256(x.numpy().tobytes()).hexdigest() for x in cpu_inputs]
    metadata["calls"] = calls
    with torch.no_grad():
        synchronize(device)
        start = time.perf_counter_ns()
        output = function()
        synchronize(device)
        metadata["preflight_complete_call_ms"] = (time.perf_counter_ns() - start) / 1e6
        metadata["max_abs_error"] = (output.double() - reference.double()).abs().max().item()
        metadata["max_relative_error_floor_1e_6"] = (
            (output.double() - reference.double()).abs()
            / reference.double().abs().clamp_min(1e-6)
        ).max().item()
        if args.experiment != "attention":
            metadata["max_row_sum_error"] = (output.sum(dim=1) - 1).abs().max().item()
        if not torch.isfinite(output).all() or not torch.allclose(output.double(), reference.double(), rtol=1e-4, atol=1e-6):
            raise RuntimeError("preflight correctness failed; no performance profile collected")
        del output
        for _ in range(metadata["warmup_calls"]):
            function()
        synchronize(device)
        activities = [torch.profiler.ProfilerActivity.CPU]
        if device == "cuda":
            activities.append(torch.profiler.ProfilerActivity.CUDA)
        with_stack = not args.experiment.startswith("online")
        metadata["with_stack"] = with_stack
        # 预检查确认需要提前初始化 lazy imports，避免进入正式 Python 栈采集。
        with torch.profiler.profile(activities=activities, with_stack=False):
            pass
        with torch.profiler.profile(activities=activities, with_stack=with_stack) as prof:
            for _ in range(calls):
                function()
            synchronize(device)
        summary = save_profile(prof, prefix, calls)
        if device == "cuda" and summary["gpu_kernel_count"] == 0:
            raise RuntimeError("no GPU kernel events in trace; GPU profile is incomplete")
        samples_ms = []
        for _ in range(metadata["timing_repetitions"]):
            synchronize(device)
            start = time.perf_counter_ns()
            function()
            synchronize(device)
            samples_ms.append((time.perf_counter_ns() - start) / 1e6)
    metadata["synchronized_complete_call_ms"] = samples_ms
    metadata["synchronized_complete_call_median_ms"] = statistics.median(samples_ms)
    metadata["source_sha256"] = {
        str(p.relative_to(Path(__file__).resolve().parents[1])): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((Path(__file__).resolve().parents[1] / "src").glob("*.py"))
    }
    prefix.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))
    print("Filtered CPU top3:", json.dumps(summary["cpu_top3"], indent=2))
    print("Filtered GPU top3:", json.dumps(summary["device_top3"], indent=2))
    print("GPU kernel us / complete call:", summary["gpu_kernel_us_per_complete_call"])


if __name__ == "__main__":
    main()
