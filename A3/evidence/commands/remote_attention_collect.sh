set -eu
cd /home/bwwu/lab/SSO_A3
if test ! -e jobs/attention.exitcode; then
    ps -p "$(cat jobs/attention.pid)" -o pid,etime,stat,args
    tail -n 10 jobs/attention.log
    exit 3
fi
test "$(cat jobs/attention.exitcode)" = 0
tar -czf attention_results.tar.gz evidence/attention evidence/commands/gpu_before_attention*.txt evidence/commands/school_attention*.txt jobs/attention.log jobs/attention.exitcode
sha256sum attention_results.tar.gz
printf '\nFINAL GPU STATE\n'
nvidia-smi --query-gpu=index,uuid,memory.used,utilization.gpu --format=csv
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv
printf '\nTASK STORAGE\n'
du -sb . cache
