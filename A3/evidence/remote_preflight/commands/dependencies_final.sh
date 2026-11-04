set -eu
cd /home/bwwu/lab/SSO_A3_preflight
printf 'ENVIRONMENT TOOLS / CUPTI / PERMISSIONS\n'
PYTHONDONTWRITEBYTECODE=1 /data/bwwu/envs/tiger/bin/python -B -m pip --version
/data/bwwu/envs/tiger/bin/python -B - <<'META'
import importlib.metadata as m, importlib.util, json, sys
from pathlib import Path
names=('torch','triton','pip','numpy','nvidia-cuda-runtime-cu12','nvidia-cuda-cupti-cu12','nvidia-cuda-nvrtc-cu12','nvidia-cublas-cu12')
print(json.dumps({'modules':{n:importlib.util.find_spec(n) is not None for n in ('venv','pip','triton.language')},'versions':{n:m.version(n) for n in names}},indent=2))
PYTHON='unused'
META
printf '\nGPU DEVICES\n'
ls -l /dev/nvidia0 /dev/nvidia1 /dev/nvidiactl /dev/nvidia-uvm
printf '\nWORKSPACE DISK\n'
du -sh . cache
