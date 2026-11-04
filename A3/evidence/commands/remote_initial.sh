set -eu
printf 'UTC: '; date -u --iso-8601=seconds
printf 'HOST: '; hostname
printf 'USER: '; id -un
printf '\nFORMAL DIRECTORY\n'
if test -e /home/bwwu/lab/SSO_A3; then
    stat -c '%U %G %A %n' /home/bwwu/lab/SSO_A3
    find /home/bwwu/lab/SSO_A3 -maxdepth 1 -mindepth 1 -printf '%f\n'
else
    printf 'SSO_A3 does not exist\n'
fi
printf '\nGPU RESOURCES\n'
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.free,memory.reserved,utilization.gpu,driver_version,compute_cap --format=csv
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv
printf '\nEXISTING PYTHON\n'
/data/bwwu/envs/tiger/bin/python -c 'import sys, torch, triton; print(sys.version); print(torch.__version__, torch.version.cuda, triton.__version__)'
