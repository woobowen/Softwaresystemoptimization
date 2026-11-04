"""记录本次运行环境；CPU 模式不探测或初始化 CUDA。"""

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

import torch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    report = {
        "label": args.label,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": str(Path.cwd()),
        "platform": platform.platform(),
        "os_release": platform.freedesktop_os_release(),
        "python": sys.version,
        "python_executable": sys.executable,
        "torch": torch.__version__,
        "torch_cuda_build": torch.version.cuda,
        "cpu_threads": torch.get_num_threads(),
        "cpu_interop_threads": torch.get_num_interop_threads(),
        "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "selected_device": args.device,
        "cuda_available": "not probed in CPU mode",
        "cuda_initialized": torch.cuda.is_initialized(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    try:
        report["triton"] = importlib.metadata.version("triton")
    except importlib.metadata.PackageNotFoundError:
        report["triton"] = "not installed"
    for command in (["lscpu"], ["free", "-b"]):
        result = subprocess.run(command, capture_output=True, text=True)
        report[command[0]] = result.stdout
        report[command[0] + "_exit_code"] = result.returncode
    report["meminfo"] = Path("/proc/meminfo").read_text()
    for file in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/cpu.max"):
        if Path(file).is_file():
            report[file] = Path(file).read_text().strip()
    if args.device == "cuda":
        report["cuda_available"] = torch.cuda.is_available()
        if not report["cuda_available"]:
            raise RuntimeError("CUDA is unavailable; GPU experiments cannot run")
        props = torch.cuda.get_device_properties(0)
        report["gpu"] = {
            "name": props.name, "memory_bytes": props.total_memory,
            "compute_capability": [props.major, props.minor],
            "multiprocessor_count": props.multi_processor_count,
        }
        if shutil.which("nvidia-smi"):
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            report["nvidia_smi"] = result.stdout
            report["nvidia_smi_exit_code"] = result.returncode
        report["cuda_initialized"] = torch.cuda.is_initialized()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
