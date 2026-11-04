set -eu
cd /home/bwwu/lab/SSO_A3
printf 'EXITCODE\n'
if test -e jobs/cpu.exitcode; then cat jobs/cpu.exitcode; else ps -p "$(cat jobs/cpu.pid)" -o pid,etime,stat,args; fi
printf '\nLOG TAIL\n'
tail -n 25 jobs/cpu.log
printf '\nRESULT FILES\n'
find evidence -maxdepth 2 -type f -printf '%P %s bytes\n'
