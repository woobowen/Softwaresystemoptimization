set -eu
cd /home/bwwu/lab/SSO_A3_preflight
# Preserve the initial verbose CPU trace and outputs, then verify profiler priming.
mv logs/cpu.log logs/cpu_initial.log
mv logs/cpu.json logs/cpu_initial.json
mv logs/cpu.exitcode logs/cpu_initial.exitcode
mv traces/cpu_naive.trace.json logs/cpu_initial.trace.json
bash preflight_run.sh cpu
bash preflight_run.sh extras
