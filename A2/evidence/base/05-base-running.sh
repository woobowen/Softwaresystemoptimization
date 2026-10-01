cd /home/addaswsw/lab/Software_system_optimization
base_pid=$(python3 -c 'import json; print(json.load(open("A2/evidence/base/base-1/run.json"))["pid"])')
PS4='$ '
set -x
date --iso-8601=seconds
ps -p "$base_pid" -o pid,etime,args
readlink -f "/proc/$base_pid/exe"
tail -n 16 A2/evidence/base/base-1/stdout.log
