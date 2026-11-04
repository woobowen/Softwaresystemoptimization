set -u
work=/home/bwwu/lab/SSO_A3_preflight
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" XDG_CACHE_HOME="$work/cache"
printf 'SETUPTOOLS_USE_DISTUTILS=%s\n' "${SETUPTOOLS_USE_DISTUTILS-unset}"
for probe in 'import triton; import triton.language; print(triton.__version__)' 'import importlib.metadata; import triton; print(triton.__version__)' 'import torch; import triton; import triton.language; print(torch.__version__,triton.__version__)'; do
 printf '\nIMPORT PROBE: %s\n' "$probe"
 /data/bwwu/envs/tiger/bin/python -B -c "$probe"
 printf 'PROBE_EXIT=%s\n' "$?"
done
printf '\nDEPENDENCY METADATA (separate interpreter)\n'
/data/bwwu/envs/tiger/bin/python -B - <<'META'
import importlib.metadata as m, importlib.util, json
names=('torch','triton','pip','setuptools','numpy','nvidia-cuda-runtime-cu12','nvidia-cuda-cupti-cu12','nvidia-cuda-nvrtc-cu12','nvidia-cublas-cu12')
print(json.dumps({'venv':importlib.util.find_spec('venv') is not None,'versions':{n:m.version(n) for n in names}},indent=2))
META
printf '\nGPU DEVICE PERMISSIONS\n'
ls -l /dev/nvidia0 /dev/nvidia1 /dev/nvidiactl /dev/nvidia-uvm
printf '\nWORKSPACE DISK\n'
du -sh "$work" "$work/cache"
