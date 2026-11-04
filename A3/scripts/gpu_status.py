"""记录两张卡的状态；所选卡有计算进程时停止，不干预其他任务。"""

from datetime import datetime, timezone
import os
import subprocess


print("UTC:", datetime.now(timezone.utc).isoformat(), flush=True)
selected = os.environ["CUDA_VISIBLE_DEVICES"]
if not selected.startswith("GPU-") or "," in selected:
    raise RuntimeError("Select exactly one physical GPU UUID")
print("Physical GPU UUID -> process cuda:0:", selected, flush=True)
subprocess.run([
    "nvidia-smi", "--query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu",
    "--format=csv",
], check=True)
processes = subprocess.check_output([
    "nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory",
    "--format=csv",
], text=True)
print(processes, end="", flush=True)
if any(line.split(",")[0].strip() == selected for line in processes.splitlines()[1:]):
    raise RuntimeError("Selected GPU has a compute process; measurements were not started")
