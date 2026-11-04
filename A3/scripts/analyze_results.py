"""从原始 trace 和 Profiler 统计复算 A3 的调用次数、时间和逻辑访问量。"""

from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_trace(prefix):
    path = prefix.with_suffix(".trace.json")
    if path.exists():
        data = path.read_bytes()
    else:
        data = gzip.decompress(path.with_suffix(".json.gz").read_bytes())
    return json.loads(data), hashlib.sha256(data).hexdigest()


def summarize(directory, name, calls):
    prefix = ROOT / "evidence" / directory / name
    metadata = json.loads(prefix.with_suffix(".metadata.json").read_text())
    statistics = json.loads(prefix.with_suffix(".statistics.json").read_text())
    trace, sha256 = load_trace(prefix)
    events = [e for e in trace["traceEvents"] if e.get("ph") == "X"]
    kernels = [e for e in events if e.get("cat") == "kernel"]
    launches = {e["args"]["correlation"]: e for e in events
                if "LaunchKernel" in e["name"] and "correlation" in e.get("args", {})}
    assert metadata["calls"] == statistics["calls"] == calls
    assert len(kernels) == statistics["gpu_kernel_count"]
    total_us = sum(e["dur"] for e in kernels)
    assert abs(total_us - statistics["gpu_kernel_total_us"]) < 1e-5
    assert all(e["args"]["correlation"] in launches for e in kernels)
    eligible = [r for r in statistics["rows"] if r["name"].startswith("aten::")
                or (r["name"] == "softmax_kernel" and "CUDA" in r["device_type"])]
    cpu = sorted([r for r in eligible if r["cpu_total_us"] > 0],
                 key=lambda r: r["cpu_total_us"], reverse=True)[:3]
    device = sorted([r for r in eligible if r["device_total_us"] > 0],
                    key=lambda r: r["device_total_us"], reverse=True)[:3]
    result = {
        "calls": calls, "trace_sha256": sha256, "kernel_count": len(kernels),
        "kernel_total_us": total_us, "kernel_us_per_call": total_us / calls,
        "input_sha256": metadata["input_sha256"],
        "cuda_visible_devices": metadata.get("cuda_visible_devices"),
        "shape": metadata["shapes"], "with_stack": metadata["with_stack"],
        "cpu_top3": cpu, "device_top3": device,
        "profiler_self_cpu_total_us": statistics["profiler_self_cpu_total_us"],
        "synchronized_call_median_ms": metadata["synchronized_complete_call_median_ms"],
        "max_abs_error": metadata["max_abs_error"],
        "max_relative_error_floor_1e_6": metadata["max_relative_error_floor_1e_6"],
    }
    if directory == "attention":
        cpu_ops = sorted([e for e in events if e.get("cat") == "cpu_op"],
                         key=lambda e: e["ts"])
        matrices = [e for e in cpu_ops if e["name"] == "aten::mm"]
        assert len(matrices) == 2 * calls
        stages = {e["args"]["External id"]: ("QK_transpose" if i % 2 == 0 else "PV")
                  for i, e in enumerate(matrices)}
        for e in cpu_ops:
            if e["name"] in {"aten::div", "aten::_softmax"}:
                stages[e["args"]["External id"]] = (
                    "scale" if e["name"] == "aten::div" else "softmax")
        stage_us = defaultdict(float)
        stage_count = Counter()
        for kernel in kernels:
            launch = launches[kernel["args"]["correlation"]]
            stage = stages[launch["args"]["External id"]]
            stage_us[stage] += kernel["dur"]
            stage_count[stage] += 1
        assert abs(sum(stage_us.values()) - total_us) < 1e-6
        result["stages"] = {
            stage: {"total_us": us, "us_per_call": us / calls,
                    "kernel_count": stage_count[stage], "percent": 100 * us / total_us}
            for stage, us in stage_us.items()
        }
        length = metadata["shapes"][0][0]
        result["model"] = {
            "matmul_FLOPs": 4 * length ** 2 * 64,
            "logical_bytes": 4 * (4 * length * 64 + 6 * length ** 2),
            "one_attention_matrix_bytes": 4 * length ** 2,
        }
        result["model"]["FLOP_per_byte"] = (
            result["model"]["matmul_FLOPs"] / result["model"]["logical_bytes"])
    return result


def main():
    profiles = [("cpu", "cpu_naive", 200), ("gpu", "gpu_naive", 200),
                ("gpu", "gpu_triton", 200), ("online", "online_naive", 1),
                ("online", "online", 1)]
    profiles += [("attention", f"attention_l{length}", 10) for length in (128, 512, 2048)]
    results = {name: summarize(directory, name, calls) for directory, name, calls in profiles}
    softmax_names = ["cpu_naive", "gpu_naive", "gpu_triton", "online_naive", "online"]
    assert len({tuple(results[name]["input_sha256"]) for name in softmax_names}) == 1
    assert len({results[name]["cuda_visible_devices"] for name in softmax_names[1:]}) == 1
    access = {"read_elements": 5 * 100 * 5000 + 2 * 100,
              "write_elements": 3 * 100 * 5000 + 2 * 100,
              "naive_bytes": 4 * (8 * 100 * 5000 + 4 * 100),
              "triton_bytes": 4 * 2 * 100 * 5000, "peak_GBps": 1008}
    for name, byte_key in [("gpu_naive", "naive_bytes"), ("gpu_triton", "triton_bytes")]:
        bandwidth = access[byte_key] / (1000 * results[name]["kernel_us_per_call"])
        results[name]["effective_GBps"] = bandwidth
        results[name]["percent_of_peak"] = 100 * bandwidth / access["peak_GBps"]
    output = {
        "access_model": access, "profiles": results,
        "gpu_kernel_speedup": results["gpu_naive"]["kernel_us_per_call"] / results["gpu_triton"]["kernel_us_per_call"],
        "online_wall_slowdown": results["online"]["synchronized_call_median_ms"] / results["online_naive"]["synchronized_call_median_ms"],
    }
    path = ROOT / "evidence/review/derived_results.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    print("Verified 8 complete traces; same Softmax input and GPU; kernel launch associations complete.")
    print("GPU kernel speedup:", output["gpu_kernel_speedup"])
    print("Online synchronized latency slowdown:", output["online_wall_slowdown"])
    print("Derived results:", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
