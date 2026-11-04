#!/usr/bin/env bash
# Read-only, bounded inventory for A3 remote preflight.
set -u
printf 'UTC: '; date -u --iso-8601=seconds
printf 'HOST: '; hostname
printf 'USER: '; id -un
printf 'UID: '; id -u
uname -srmo
cat /etc/os-release
printf '\nCPU / MEMORY\n'
lscpu | sed -n '/^CPU(s):/p; /^Model name:/p; /^Socket(s):/p'
printf 'Available logical CPUs: '; nproc
free -h
printf '\nUSER FILESYSTEM / LIMITS\n'
df -hT "$HOME"
findmnt -T "$HOME" -o TARGET,SOURCE,FSTYPE,OPTIONS
printf 'Home writable/searchable: '; test -w "$HOME" && test -x "$HOME" && echo yes
umask
ulimit -f -u -v
if command -v quota >/dev/null; then timeout 5 quota -s; else echo 'quota command: absent'; fi
printf '\nSCHEDULER / SESSION TOOLS\n'
for c in sbatch srun sinfo squeue qsub bsub condor_submit tmux screen nohup timeout; do
    command -v "$c" || true
done
printf 'Scheduler-related processes (names only):\n'
ps -eo comm= | sort -u | sed -n '/slurm/p; /pbs/p; /sge/p; /condor/p; /lsf/p'
for f in /etc/motd /etc/issue; do
    if test -r "$f"; then printf '\n%s\n' "$f"; head -n 60 "$f"; fi
done
printf 'Slurm config exists: '; test -f /etc/slurm/slurm.conf && echo yes || echo no
printf 'PBS config exists: '; test -f /etc/pbs.conf && echo yes || echo no
printf '\nGPU SNAPSHOT 1\n'
date -u --iso-8601=seconds
nvidia-smi
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu,driver_version,compute_cap --format=csv
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv
printf '\nAVAILABLE ENVIRONMENT ENTRY POINTS\n'
for c in python python3 pip pip3 conda gcc g++ clang nvcc nsys ncu; do
    command -v "$c" || true
done
for c in python python3; do
    if command -v "$c" >/dev/null; then "$c" --version; fi
done
for c in gcc g++ clang nvcc; do
    if command -v "$c" >/dev/null; then "$c" --version | head -n 4; fi
done
for d in "$HOME/miniconda3" "$HOME/anaconda3" "$HOME/miniforge3" "$HOME/mambaforge" /opt/conda; do
    if test -x "$d/bin/python"; then
        printf 'Conda root: %s\n' "$d"
        if test -x "$d/bin/conda"; then "$d/bin/conda" env list --json; fi
    fi
done
if test -r "$HOME/.conda/environments.txt"; then
    printf 'Registered environment paths:\n'; cat "$HOME/.conda/environments.txt"
fi
printf '\nGPU SNAPSHOT 2\n'
date -u --iso-8601=seconds
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu,driver_version,compute_cap --format=csv
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv
