"""Check explicit attention against a stable FP64 mathematical reference."""

import argparse
import json
import math
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from attention import attention


SEED = 10245102410
RTOL = 1e-4
ATOL = 1e-6


def reference_attention(q, k, v):
    # Use the same FP32 input values, then calculate on the CPU in FP64.
    scores = q.double() @ k.double().T / math.sqrt(q.shape[-1])
    numerator = torch.exp(scores - scores.amax(dim=-1, keepdim=True))
    probabilities = numerator / numerator.sum(dim=-1, keepdim=True)
    return probabilities @ v.double()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA was requested but is unavailable")

    torch.set_num_threads(args.threads)
    # 'highest' uses full FP32 internal matmul and disables TF32 matmul.
    torch.set_float32_matmul_precision("highest")
    generator = torch.Generator(device="cpu").manual_seed(SEED)
    device = torch.device(args.device)
    cases = [
        ("random_small", 4, 6, 8, 5),
        ("nonsquare", 7, 11, 13, 3),
        ("zero_q", 5, 9, 7, 4),
        ("single_key", 4, 1, 6, 3),
        ("single_query", 1, 8, 6, 2),
        ("single_both", 1, 1, 1, 1),
        ("length_128", 128, 128, 64, 64),
        ("length_512", 512, 512, 64, 64),
        ("length_2048", 2048, 2048, 64, 64),
    ]
    results = []
    with torch.no_grad():
        for name, lq, lk, dk, dv in cases:
            q = torch.randn(lq, dk, generator=generator, dtype=torch.float32)
            k = torch.randn(lk, dk, generator=generator, dtype=torch.float32)
            v = torch.randn(lk, dv, generator=generator, dtype=torch.float32)
            if name == "zero_q":
                q.zero_()
                expected = v.double().mean(dim=0).expand(lq, dv)
            else:
                expected = reference_attention(q, k, v)

            q_device, k_device, v_device = q.to(device), k.to(device), v.to(device)
            actual = attention(q_device, k_device, v_device)
            observed = actual.cpu().double()
            error = (observed - expected).abs()
            tolerance = ATOL + RTOL * expected.abs()
            failed_elements = int((error > tolerance).sum().item())
            finite = bool(torch.isfinite(observed).all().item())
            result = {
                "name": name,
                "q_shape": list(q.shape),
                "k_shape": list(k.shape),
                "v_shape": list(v.shape),
                "output_shape": list(actual.shape),
                "shape_correct": list(actual.shape) == [lq, dv],
                "dtype_correct": actual.dtype == torch.float32,
                "device_correct": actual.device == q_device.device,
                "finite": finite,
                "max_absolute_error": error.max().item() if finite else None,
                "max_tolerance_ratio": (error / tolerance).max().item() if finite else None,
                "failed_elements": failed_elements,
            }
            if name == "zero_q":
                weights = torch.softmax(
                    q_device @ k_device.T / math.sqrt(dk), dim=-1
                )
                uniform = torch.full_like(weights, 1.0 / lk)
                result["weights_uniform"] = bool(
                    torch.allclose(weights, uniform, rtol=RTOL, atol=ATOL)
                )
            result["passed"] = (
                result["shape_correct"]
                and result["dtype_correct"]
                and result["device_correct"]
                and result["finite"]
                and failed_elements == 0
                and result.get("weights_uniform", True)
            )
            results.append(result)

    report = {
        "torch_version": torch.__version__,
        "device": args.device,
        "seed": SEED,
        "input_generation": "CPU torch.Generator, FP32, then copy to device",
        "reference": "CPU FP64 stable mathematical attention; zero_q uses mean(V)",
        "rtol": RTOL,
        "atol": ATOL,
        "cpu_threads": torch.get_num_threads(),
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "cases": results,
        "passed": all(result["passed"] for result in results),
    }
    output = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
