set -eu
umask 077
mkdir -p "$HOME/lab"
work="$HOME/lab/SSO_A3_preflight"
if test -e "$work"; then echo 'Refusing to overwrite existing workspace' >&2; exit 23; fi
mkdir -m 700 "$work"
mkdir "$work/logs" "$work/traces" "$work/cache"
printf 'REMOTE_WORKDIR=%s\n' "$work"
stat -c '%U %G %a %F %n' "$work"
printf 'WSL-to-Windows-OpenSSH-to-school-server\nA3 remote preflight only\n' > "$work/remote_marker.txt"
sha256sum "$work/remote_marker.txt"
printf '\nCANDIDATE IMPORTS (CPU only)\n'
PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME="$work/cache" /data/bwwu/envs/tiger/bin/python - <<'PYREMOTE'
import torch, triton, triton.language as tl, sys, json, importlib.metadata as m
print(json.dumps({"executable":sys.executable,"python":sys.version,"torch":torch.__version__,"torch_cuda_runtime":torch.version.cuda,"triton":triton.__version__,"torch_path":torch.__file__,"triton_path":triton.__file__,"profiler_cpu_supported":str(torch.profiler.ProfilerActivity.CPU),"kineto_available":torch.profiler.kineto_available(),"cpu_scalar":(torch.tensor([1.,2.])+1).tolist()},indent=2))
print('Torch configured toolchain:')
print(torch.__config__.show())
PYREMOTE
