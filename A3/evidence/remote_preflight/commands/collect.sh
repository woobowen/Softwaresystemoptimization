set -u
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=""
printf 'TARGETED METADATA PROBE REPRODUCTION\n'
/data/bwwu/envs/tiger/bin/python -B - <<'DIAG'
import importlib.util, sys
print('Before pip find_spec:', 'distutils.core' in sys.modules,flush=True)
print('pip spec exists:',importlib.util.find_spec('pip') is not None,flush=True)
import triton
print(triton.__version__)
DIAG
printf 'REPRODUCTION_EXIT=%s\n' "$?"
printf '\nSETUPTOOLS FINDER BEHAVIOR (public installed dependency source)\n'
sed -n '/    def spec_for_pip/,/    @classmethod/p' /data/bwwu/envs/tiger/lib/python3.10/site-packages/_distutils_hack/__init__.py
printf '\nFINAL GPU SNAPSHOT (after every GPU test exited)\n'
date -u --iso-8601=seconds
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.free,memory.reserved,utilization.gpu,driver_version,compute_cap --format=csv
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv
cd /home/bwwu/lab/SSO_A3_preflight
printf '\nREMOTE RESULTS MANIFEST\n'
sha256sum traces/*.json logs/*.json logs/*.log logs/*.exitcode preflight_smoke.py teacher_softmax_preflight.py preflight_run.sh transfer_probe.sh remote_marker.txt > remote_results.sha256
cat remote_results.sha256
# No cache or research environment content is transferred.
tar -czf remote_results.tar.gz traces logs remote_results.sha256 preflight_smoke.py teacher_softmax_preflight.py preflight_run.sh transfer_probe.sh remote_marker.txt
sha256sum remote_results.tar.gz
printf '\nFINAL DIRECTORY SIZE (bytes)\n'
du -sb . cache
