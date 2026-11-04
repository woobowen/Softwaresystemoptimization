"""在真实 CUDA 上复用 Softmax 输入检查 Triton 实现。"""

import argparse
import json
from pathlib import Path

import torch

from check_softmax import ATOL, RTOL, SEED, check_result, make_cases
from triton_softmax import softmax


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    if not torch.cuda.is_available():
        parser.error("CUDA is unavailable")
    records = []
    with torch.no_grad():
        for case, cpu_input in make_cases():
            x = cpu_input.cuda()
            result = softmax(x)
            reference = torch.softmax(x, dim=1)
            record = check_result("triton", case, x, reference, result)
            records.append(record)
            print(json.dumps(record))
    report = {
        "status": "PASS" if all(r["status"] == "PASS" for r in records) else "FAIL",
        "seed": SEED, "rtol": RTOL, "atol": ATOL,
        "reference": "torch.softmax(x, dim=1)", "checks": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
