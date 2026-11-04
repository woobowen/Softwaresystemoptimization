"""比较两种作业实现与 torch.softmax，保存逐项误差。"""

import argparse
import json
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from softmax import naive_softmax, online_softmax


SEED = 10245102410
RTOL = 1e-4
ATOL = 1e-6


def make_cases():
    generator = torch.Generator(device="cpu").manual_seed(SEED)
    return [
        ("random_small", torch.randn(3, 7, generator=generator)),
        ("random_non_power_of_two", torch.randn(4, 129, generator=generator)),
        ("single_element", torch.tensor([[5.0]])),
        ("single_row", torch.randn(1, 13, generator=generator)),
        ("single_column", torch.randn(7, 1, generator=generator)),
        (
            "equal_elements_per_row",
            torch.tensor([-1000.0, 0.0, 3.25, 1000.0])[:, None]
            .expand(4, 37)
            .clone(),
        ),
        (
            "large_positive_negative",
            torch.tensor(
                [
                    [10000.0, 9999.0, -10000.0, 0.0, 10001.0],
                    [-10000.0, -10001.0, 10000.0, -9999.0, 0.0],
                    [1e20, -1e20, 0.0, 1e20, 1e20],
                ]
            ),
        ),
        ("formal_100x5000", torch.randn(100, 5000, generator=generator)),
    ]


def check_result(name, case, x, reference, result):
    shape_ok = result.shape == x.shape
    dtype_ok = result.dtype == x.dtype
    device_ok = result.device == x.device
    finite = bool(torch.isfinite(result).all())
    row_sums = result.sum(dim=1)
    row_sums_ok = torch.allclose(
        row_sums, torch.ones_like(row_sums), rtol=RTOL, atol=ATOL
    )
    matches_reference = torch.allclose(result, reference, rtol=RTOL, atol=ATOL)
    passed = all(
        (shape_ok, dtype_ok, device_ok, finite, row_sums_ok, matches_reference)
    )
    return {
        "implementation": name,
        "case": case,
        "shape": list(result.shape),
        "dtype": str(result.dtype),
        "device": str(result.device),
        "shape_ok": shape_ok,
        "dtype_ok": dtype_ok,
        "device_ok": device_ok,
        "finite": finite,
        "row_sums_ok": row_sums_ok,
        "matches_reference": matches_reference,
        "max_abs_error": (result - reference).abs().max().item(),
        "max_relative_error_floor_1e_6": (
            (result - reference).abs() / reference.abs().clamp_min(1e-6)
        ).max().item(),
        "max_row_sum_error": (row_sums - 1).abs().max().item(),
        "status": "PASS" if passed else "FAIL",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")
    torch.set_num_threads(args.threads)
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA is not available")

    records = []
    with torch.no_grad():
        for case, cpu_input in make_cases():
            x = cpu_input.to(device=args.device, dtype=torch.float32)
            reference = torch.softmax(x, dim=1)
            for name, implementation in (
                ("naive", naive_softmax),
                ("online", online_softmax),
            ):
                record = check_result(name, case, x, reference, implementation(x))
                records.append(record)
                print(
                    f"{record['status']} {name:6s} {case:28s} "
                    f"abs_error={record['max_abs_error']:.9g} "
                    f"row_sum_error={record['max_row_sum_error']:.9g}"
                )

    passed = all(record["status"] == "PASS" for record in records)
    report = {
        "status": "PASS" if passed else "FAIL",
        "reference": "torch.softmax(x, dim=1)",
        "seed": SEED,
        "input_generation": "CPU torch.Generator; identical cases copied to target device",
        "device": args.device,
        "torch_version": torch.__version__,
        "cpu_threads": torch.get_num_threads(),
        "rtol": RTOL,
        "atol": ATOL,
        "checks": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Overall: {report['status']}; {len(records)} checks; output={args.output}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
