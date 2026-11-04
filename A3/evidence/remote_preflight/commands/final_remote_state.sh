set -eu
printf 'UTC: '; date -u --iso-8601=seconds
printf 'HOST: '; hostname
printf 'USER: '; id -un
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.free,memory.reserved,utilization.gpu,driver_version,compute_cap --format=csv
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv
printf '\nTASK DIRECTORY / CACHE BYTES\n'
du -sb /home/bwwu/lab/SSO_A3_preflight
du -sb /home/bwwu/lab/SSO_A3_preflight/cache
printf '\nSHORT CPU JOB EXIT\n'
cat /home/bwwu/lab/SSO_A3_preflight/logs/detached.exitcode
