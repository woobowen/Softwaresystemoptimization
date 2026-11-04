set -eu
cd /home/bwwu/lab/SSO_A3
if test -e jobs/online.exitcode; then cat jobs/online.exitcode; else ps -p "$(cat jobs/online.pid)" -o pid,etime,stat,args; fi
tail -n 18 jobs/online.log
find evidence/online -maxdepth 1 -type f -printf '%f %s bytes\n'
