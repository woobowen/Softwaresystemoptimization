#!/usr/bin/env python3
"""A3 compatibility checks only: one invocation per profiling region, no benchmark."""
import argparse
import collections
import datetime
import json
from pathlib import Path
import sys

import torch


def naive_softmax(x):
    x_max = x.max(dim=1)[0]
    z = x - x_max[:, None]
    numerator = torch.exp(z)
    denominator = numerator.sum(dim=1)
    return numerator / denominator[:, None]


def online_softmax(x):
    m = torch.full((x.shape[0],), -float("inf"), device=x.device)
    d = torch.zeros_like(m)
    for j in range(x.shape[1]):
        column = x[:, j]
        m_new = torch.maximum(m, column)
        d = d * torch.exp(m - m_new) + torch.exp(column - m_new)
        m = m_new
    y = torch.empty_like(x)
    for j in range(x.shape[1]):
        y[:, j] = torch.exp(x[:, j] - m) / d
    return y


def attention(q, k, v):
    scores = q @ k.T
    scaled = scores / (q.shape[1] ** 0.5)
    probabilities = torch.softmax(scaled, dim=1)
    return probabilities @ v


def compare(y, reference, probability=False):
    torch.testing.assert_close(y, reference, atol=1e-6, rtol=1e-5)
    assert bool(torch.isfinite(y).all())
    result = {"shape": list(y.shape), "dtype": str(y.dtype),
              "max_abs_error": float((y - reference).abs().max()), "finite": True}
    if probability:
        sums = y.sum(dim=1)
        torch.testing.assert_close(sums, torch.ones_like(sums), atol=1e-6, rtol=1e-5)
        result["row_sum_max_abs_error"] = float((sums - 1).abs().max())
    return result


def profile_once(fn, name, work, cuda=False):
    activities = [torch.profiler.ProfilerActivity.CPU]
    if cuda:
        activities.append(torch.profiler.ProfilerActivity.CUDA)
        torch.cuda.synchronize()
    # Initialize lazy profiler imports before collecting Python call frames.
    with torch.profiler.profile(activities=activities, with_stack=False):
        pass
    # Every function has already run outside the profiler, including Triton JIT.
    with torch.profiler.profile(activities=activities, with_stack=True,
                                record_shapes=True) as prof:
        with torch.profiler.record_function("preflight::" + name):
            y = fn()
        if cuda:
            torch.cuda.synchronize()
    trace_path = work / "traces" / (name + ".trace.json")
    prof.export_chrome_trace(str(trace_path))
    table = prof.key_averages().table(sort_by="cpu_time_total", row_limit=15)
    print(table, flush=True)
    if cuda:
        print(prof.key_averages().table(sort_by="device_time_total", row_limit=15), flush=True)
    events = prof.events()
    aten = sorted({e.name for e in events if e.name.startswith("aten::")})
    device_events = [e for e in events if e.device_type == torch.autograd.DeviceType.CUDA]
    stacks = [e for e in events if e.stack]
    trace = json.loads(trace_path.read_text())
    trace_events = trace["traceEvents"]
    kernels = [e for e in trace_events if e.get("cat") == "kernel" and e.get("ph") == "X"]
    python_events = [e for e in trace_events if e.get("cat") == "python_function"]
    summary = {"profiled_calls": 1, "with_stack": True, "trace": str(trace_path),
               "trace_bytes": trace_path.stat().st_size, "aten_events": aten,
               "profiler_cuda_events": len(device_events),
               "profiler_cuda_duration_us": sum(e.device_time_total for e in device_events),
               "trace_kernel_events": len(kernels),
               "trace_kernel_duration_us": sum(e.get("dur", 0) for e in kernels),
               "kernel_names": sorted({e["name"] for e in kernels}),
               "events_with_stack": len(stacks),
               "stack_example": stacks[0].stack[:8] if stacks else [],
               "python_function_events": len(python_events),
               "python_function_examples": [e["name"] for e in python_events
                                              if any(n in e["name"] for n in
                                                     ("naive_softmax", "softmax", "attention"))][:10],
               "categories": dict(collections.Counter(e.get("cat", "") for e in trace_events))}
    assert aten or name == "triton"
    if cuda:
        assert device_events, "Profiler has no CUDA device events"
        assert kernels, "Exported trace has no real GPU kernels"
        assert all(isinstance(e.get("ts"), (int, float)) and e.get("dur", 0) > 0 for e in kernels)
    print(json.dumps(summary, indent=2), flush=True)
    return y, summary


def init_cuda():
    assert torch.cuda.is_available()
    assert torch.cuda.device_count() == 1, "Only one GPU may be visible in this preflight process"
    torch.cuda.set_device(0)
    p = torch.cuda.get_device_properties(0)
    return {"logical_device": 0, "visible_device_count": torch.cuda.device_count(),
            "name": p.name, "compute_capability": list(torch.cuda.get_device_capability(0)),
            "total_memory_bytes": p.total_memory}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("cpu", "cuda", "triton", "extras"))
    parser.add_argument("--workdir", type=Path, required=True)
    args = parser.parse_args()
    work = args.workdir
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.manual_seed(10245102410)
    torch.backends.cuda.matmul.allow_tf32 = False
    out = {"stage": args.stage, "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "python": sys.version, "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
           "cpu_threads": torch.get_num_threads()}
    if args.stage != "cpu":
        out["device"] = init_cuda()
    if args.stage in ("cpu", "cuda"):
        device = "cpu" if args.stage == "cpu" else "cuda:0"
        x = torch.randn((4, 127), device=device, dtype=torch.float32)
        y = naive_softmax(x)
        if device != "cpu":
            torch.cuda.synchronize()
        out["correctness"] = compare(y, torch.softmax(x, dim=1), probability=True)
        yp, out["profile"] = profile_once(lambda: naive_softmax(x),
                                           args.stage + "_naive", work, cuda=device != "cpu")
        compare(yp, y, probability=True)
        assert "aten::exp" in out["profile"]["aten_events"]
    elif args.stage == "triton":
        import triton
        import teacher_softmax_preflight as teacher
        import subprocess
        import os
        out["triton_version"] = triton.__version__
        out["target"] = str(teacher.target)
        out["properties"] = teacher.properties
        ptxas = Path(triton.__file__).parent / "backends/nvidia/bin/ptxas"
        out["bundled_ptxas"] = str(ptxas)
        if ptxas.exists():
            out["ptxas_version"] = subprocess.check_output([str(ptxas), "--version"], text=True)
        metadata = []

        def launch_and_check(shape):
            x = torch.randn(shape, device="cuda:0", dtype=torch.float32)
            y = teacher.softmax(x)  # unchanged PDF host logic and kernel
            torch.cuda.synchronize()
            check = compare(y, torch.softmax(x, dim=1), probability=True)
            # Inspect the already compiled specialization, without another GPU launch.
            block = triton.next_power_of_2(shape[1])
            stages = 4 if teacher.SIZE_SMEM > 200000 else 2
            k = teacher.softmax_kernel.warmup(y, x, x.stride(0), y.stride(0), *shape,
                                               block, num_stages=stages, num_warps=8, grid=(1,))
            k._init_handles()
            occupancy = teacher.NUM_REGS // (k.n_regs * teacher.WARP_SIZE * 8)
            occupancy = min(occupancy, teacher.SIZE_SMEM // k.metadata.shared)
            metadata.append({"shape": list(shape), "BLOCK_SIZE": block, "num_warps": 8,
                             "num_stages": stages, "n_regs": k.n_regs,
                             "shared_bytes": k.metadata.shared, "occupancy": occupancy,
                             "persistent_programs": min(teacher.NUM_SM * occupancy, shape[0]),
                             "correctness": check})
            return x, y

        small, expected = launch_and_check((4, 127))
        # Exactly one full assignment-shape execution, outside profiling.
        launch_and_check((100, 5000))
        out["compiled_specializations"] = metadata
        yp, out["profile"] = profile_once(lambda: teacher.softmax(small), "triton", work, cuda=True)
        compare(yp, expected, probability=True)
        out["teacher_softmax_launches"] = {"4x127": 2, "100x5000": 1}
        out["cache_directory"] = os.environ.get("TRITON_CACHE_DIR")
    else:
        online_results = {}
        for device in ("cpu", "cuda:0"):
            x = torch.randn((4, 32), device=device)
            online_results[device] = compare(online_softmax(x), torch.softmax(x, dim=1), probability=True)
        torch.cuda.synchronize()
        out["online_4x32"] = online_results
        q, k, v = [torch.randn((16, 64), device="cuda:0", dtype=torch.float32) for _ in range(3)]
        result = attention(q, k, v)
        torch.cuda.synchronize()
        reference = attention(q.cpu().double(), k.cpu().double(), v.cpu().double()).float()
        out["attention_16x64"] = compare(result.cpu(), reference)
        yp, out["attention_profile"] = profile_once(lambda: attention(q, k, v), "attention", work, cuda=True)
        compare(yp, result)
        assert {"aten::mm", "aten::div", "aten::softmax"}.issubset(out["attention_profile"]["aten_events"])
    if args.stage != "cpu":
        torch.cuda.synchronize()
        out["peak_tensor_allocated_bytes"] = torch.cuda.max_memory_allocated(0)
        out["peak_allocator_reserved_bytes"] = torch.cuda.max_memory_reserved(0)
        # Current process only; report CUDA context separately from tensor allocator.
        import subprocess
        out["gpu_process_snapshot"] = subprocess.check_output([
            "nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_gpu_memory", "--format=csv"], text=True)
        with Path("/proc/self/maps").open() as maps:
            out["loaded_cuda_libraries"] = sorted({line.split()[-1] for line in maps
                                                   if any(s in line for s in
                                                          ("libcupti", "libcudart", "libcuda.so"))})
    out["result"] = "PASS"
    (work / "logs" / (args.stage + ".json")).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    main()
