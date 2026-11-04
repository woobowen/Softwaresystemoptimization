set -eu
cd /home/bwwu/lab/SSO_A3
if test -e jobs/softmax.exitcode; then cat jobs/softmax.exitcode; else ps -p "$(cat jobs/softmax.pid)" -o pid,etime,stat,args; fi
tail -n 15 jobs/softmax.log
