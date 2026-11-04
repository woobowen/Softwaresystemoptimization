set -eu
cd /home/bwwu/lab/SSO_A3
if test -e jobs/correctness.exitcode; then cat jobs/correctness.exitcode; else ps -p "$(cat jobs/correctness.pid)" -o pid,etime,stat,args; fi
tail -n 12 jobs/correctness.log
