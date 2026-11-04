set -u
printf 'UTC: '; date -u --iso-8601=seconds
printf 'REMOTE WORKSPACE PREEXISTENCE: '
if test -e "$HOME/lab/SSO_A3_preflight"; then stat -c '%U %G %a %F %n' "$HOME/lab/SSO_A3_preflight"; else echo absent; fi
printf '\nDRIVER PROFILING RESTRICTIONS\n'
if test -r /proc/driver/nvidia/params; then sed -n '/Profiling/p' /proc/driver/nvidia/params; fi
printf '\nCUDA TOOLKIT PATHS\n'
for d in /usr/local/cuda /usr/local/cuda-*; do
 if test -d "$d"; then ls -ld "$d"; test ! -x "$d/bin/nvcc" || "$d/bin/nvcc" --version; fi
done
printf '\nREGISTERED ENVIRONMENT PACKAGE METADATA (no CUDA initialization)\n'
for py in /usr/bin/python3 /data/bwwu/envs/tiger/bin/python /data/bwwu/envs/grid-20261009-e61baf3/bin/python; do
 if test -x "$py"; then
 PYTHONDONTWRITEBYTECODE=1 "$py" - <<'META'
import sys, importlib.metadata as m, importlib.util, json
out={"python_executable":sys.executable,"python":sys.version,"prefix":sys.prefix,"modules":{n:importlib.util.find_spec(n) is not None for n in ("venv","pip","torch","triton")},"packages":{}}
for n in ("torch","triton","pip","nvidia-cuda-runtime-cu12","nvidia-cuda-cupti-cu12","nvidia-cuda-nvrtc-cu12","nvidia-cublas-cu12","numpy"):
 try: out["packages"][n]=m.version(n)
 except m.PackageNotFoundError: out["packages"][n]=None
print(json.dumps(out,indent=2))
META
 fi
done
printf '\nGPU LATER SNAPSHOT\n'
date -u --iso-8601=seconds
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu,driver_version,compute_cap --format=csv
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv
