#!/usr/bin/env bash
# Read-only audit. Exit 0 means checks completed, NOT Engineering PASS.
# No installation, sudo, sysctl writes, temporary files, or output-file writes.
set -u
export LC_ALL=C

mode=${1:---all}
case "$mode" in
  --all|--versions|--commands|--perf) ;;
  --help)
    printf 'Usage: bash %s [--all|--versions|--commands|--perf]\n' "$0"
    printf 'Read-only; redirect stdout/stderr yourself to save evidence.\n'
    printf 'Exit 0: audit completed, even if requirements are missing. Read SUMMARY.\n'
    exit 0 ;;
  *) printf 'Unknown argument: %s\n' "$mode" >&2; exit 2 ;;
esac

pass=0 missing=0 old=0 unverified=0
perf_status=UNVERIFIED
software_status=UNVERIFIED
hardware_status=UNVERIFIED
cpu_scope_status=UNVERIFIED
run() {
  printf '\n$'; printf ' %q' "$@"; printf '\n'
  "$@" 2>&1
  local result=$?
  printf 'exit_code=%s\n' "$result"
  return "$result"
}
row() {
  printf 'CHECK\t%s\tRequired=%s\tDetected=%s\tStatus=%s\n' "$1" "$2" "$3" "$4"
  case "$4" in
    PASS) ((pass+=1)) ;; MISSING) ((missing+=1)) ;;
    VERSION_TOO_OLD) ((old+=1)) ;; UNVERIFIED) ((unverified+=1)) ;;
  esac
}
at_least() {
  local detected=$1 required=$2 i left right
  local -a a b
  IFS=. read -r -a a <<< "$detected"
  IFS=. read -r -a b <<< "$required"
  for ((i=0; i<${#a[@]} || i<${#b[@]}; i++)); do
    left=${a[i]:-0}; right=${b[i]:-0}
    ((10#$left > 10#$right)) && return 0
    ((10#$left < 10#$right)) && return 1
  done
  return 0
}
version_check() {
  local tool=$1 required=$2 output result detected status
  shift 2
  if ! command -v "$tool"; then
    run "$tool" "$@" || :
    row "$tool" "$required" absent MISSING
    return
  fi
  printf '\n$ %s' "$tool"; printf ' %q' "$@"; printf '\n'
  output=$("$tool" "$@" 2>&1); result=$?
  printf '%s\nexit_code=%s\n' "$output" "$result"
  # Parse first line to avoid copyright years or wrapper installation hints.
  detected=$(printf '%s\n' "$output" | head -n 1 | grep -oE '[0-9]+(\.[0-9]+)+' | head -n 1)
  if ((result != 0)) || [[ -z "$detected" ]]; then status=UNVERIFIED
  elif at_least "$detected" "$required"; then status=PASS
  else status=VERSION_TOO_OLD; fi
  row "$tool" "$required" "${detected:-unknown}" "$status"
}
versions() {
  local ID=unknown VERSION_ID=unknown PRETTY_NAME=unknown VERSION=unknown kernel numeric
  run pwd || :
  run whoami || :
  run cat /etc/os-release || :
  if [[ -r /etc/os-release ]]; then source /etc/os-release; fi
  if [[ "$ID" != ubuntu ]]; then row OS 'Ubuntu >=22.04 LTS' "$PRETTY_NAME" UNVERIFIED
  elif [[ "$VERSION_ID" =~ ^[0-9]+(\.[0-9]+)*$ ]] && ! at_least "$VERSION_ID" 22.04; then
    row OS 'Ubuntu >=22.04 LTS' "$PRETTY_NAME" VERSION_TOO_OLD
  elif [[ "$VERSION" == *LTS* ]]; then row OS 'Ubuntu >=22.04 LTS' "$PRETTY_NAME" PASS
  else row OS 'Ubuntu >=22.04 LTS' "$PRETTY_NAME" UNVERIFIED; fi
  run uname -a || :
  run uname -r || :
  run uname -m || :
  kernel=$(uname -r); numeric=${kernel%%-*}
  if [[ ! "$numeric" =~ ^[0-9]+(\.[0-9]+)*$ ]]; then row Kernel '>=5.15' "$kernel" UNVERIFIED
  elif at_least "$numeric" 5.15; then row Kernel '>=5.15' "$kernel" PASS
  else row Kernel '>=5.15' "$kernel" VERSION_TOO_OLD; fi
  run cat /proc/version || :
  run cat /proc/sys/kernel/osrelease || :
  if grep -qiE 'microsoft|wsl' /proc/version /proc/sys/kernel/osrelease 2>/dev/null; then
    printf 'WSL_DETECTED=yes\n'
  else printf 'WSL_DETECTED=no (based on available kernel strings)\n'; fi
  run lscpu || :
  version_check gcc 9.3 --version
  version_check clang 10.0 --version
  version_check python3 3.10 --version
  version_check java 11 -version
  version_check javac 11 -version
  version_check valgrind 3.18 --version
  version_check perf 5.15 --version
}
commands() {
  local tool location
  for tool in uname sysctl top dmidecode numactl lscpu cat free vmstat mpstat pidstat iostat sar head man; do
    if location=$(command -v "$tool"); then row "$tool" available "$location" PASS
    else row "$tool" available absent MISSING; fi
  done
}
perf_checks() {
  local output result first_result cpu_result software_result hardware_result
  local software_output hardware_output kernel_log kernel_log_result unsupported_count
  run uname -r || :
  run command -v perf || :
  if ! run perf --version; then
    run perf stat ls || :
    printf 'perf stat -C 0 sleep 3: NOT_RUN (prerequisite failed)\n'
    if command -v perf >/dev/null 2>&1; then perf_status=UNRESOLVED_SOFTWARE_CONFIGURATION
    else perf_status=MISSING; fi
    printf 'PMU_COUNTERS=UNVERIFIED\n'
    return
  fi
  printf '\n$ perf stat ls\n'
  output=$(perf stat ls 2>&1); first_result=$?
  printf '%s\nexit_code=%s\n' "$output" "$first_result"
  # R1 requires this attempt even when the preceding default stat fails.
  printf '\n$ perf stat -C 0 sleep 3\n'
  output=$(perf stat -C 0 sleep 3 2>&1); cpu_result=$?
  printf '%s\nexit_code=%s\n' "$output" "$cpu_result"
  if ((cpu_result == 0)); then cpu_scope_status=PASS
  elif grep -qiE 'permission|access.*limited|operation not permitted' <<< "$output"; then
    cpu_scope_status=PERMISSION_DENIED
  fi
  # :u requests user-space events without changing perf_event_paranoid.
  printf '\n$ perf stat -e task-clock:u,page-faults:u -- ls\n'
  software_output=$(perf stat -e task-clock:u,page-faults:u -- ls 2>&1); software_result=$?
  printf '%s\nexit_code=%s\n' "$software_output" "$software_result"
  if ((software_result == 0)) &&
     grep -qE '[0-9].*task-clock:u' <<< "$software_output" &&
     grep -qE '[0-9].*page-faults:u' <<< "$software_output" &&
     ! grep -qiE 'not supported|not counted' <<< "$software_output"; then software_status=PASS; fi
  printf '\n$ perf stat -e cycles:u,instructions:u,branches:u,branch-misses:u -- sleep 1\n'
  hardware_output=$(perf stat -e cycles:u,instructions:u,branches:u,branch-misses:u -- sleep 1 2>&1); hardware_result=$?
  printf '%s\nexit_code=%s\n' "$hardware_output" "$hardware_result"
  unsupported_count=$(grep -cE '<not supported>[[:space:]]+(cycles|instructions|branches|branch-misses):u([[:space:]]|$)' <<< "$hardware_output")
  if [[ "$unsupported_count" == 4 ]]; then hardware_status=NOT_SUPPORTED
  elif ((hardware_result == 0)) &&
       ! grep -qiE 'not supported|not counted' <<< "$hardware_output" &&
       [[ $(grep -cE '[0-9][[:space:]]+(cycles|instructions|branches|branch-misses):u([[:space:]]|$)' <<< "$hardware_output") == 4 ]]; then
    hardware_status=PASS
  elif grep -qiE 'permission|access.*limited|operation not permitted' <<< "$hardware_output"; then
    hardware_status=PERMISSION_DENIED
  fi
  run cat /proc/sys/kernel/perf_event_paranoid || :
  run ls /sys/bus/event_source/devices || :
  printf '\n$ dmesg (output filtered to perf/PMU lines)\n'
  kernel_log=$(dmesg 2>&1); kernel_log_result=$?
  if ((kernel_log_result == 0)); then printf '%s\n' "$kernel_log" | grep -iE 'perf|PMU' || :
  else printf '%s\n' "$kernel_log"; fi
  printf 'dmesg_exit_code=%s\n' "$kernel_log_result"
  if ((first_result == 0)) && [[ "$software_status" == PASS && "$hardware_status" == PASS && "$cpu_scope_status" == PASS ]]; then
    perf_status=PASS
  elif ((first_result == 0 && kernel_log_result == 0)) &&
       [[ "$software_status" == PASS && "$hardware_status" == NOT_SUPPORTED ]] &&
       [[ "$cpu_scope_status" == PASS || "$cpu_scope_status" == PERMISSION_DENIED ]] &&
       grep -qiE 'no PMU driver, software events only' <<< "$kernel_log"; then
    perf_status=NON_BLOCKING_PMU_LIMITATION
  elif [[ "$hardware_status" == PERMISSION_DENIED || "$cpu_scope_status" == PERMISSION_DENIED ]]; then
    perf_status=PERMISSION_DENIED
  else perf_status=UNVERIFIED; fi
  printf 'CPU-wide permission restrictions are reported separately; no sysctl change is made.\n'
}

printf 'A1 environment audit — %s\n' "$(date -Is)"
printf 'MODE=%s\n' "$mode"
case "$mode" in
  --all) versions; commands; perf_checks ;;
  --versions) versions ;;
  --commands) commands ;;
  --perf) perf_checks ;;
esac
printf '\nSUMMARY: PASS=%d MISSING=%d VERSION_TOO_OLD=%d UNVERIFIED=%d\n' "$pass" "$missing" "$old" "$unverified"
if [[ "$mode" == --all || "$mode" == --perf ]]; then
  printf 'SOFTWARE_EVENTS=%s\nHARDWARE_COUNTERS=%s\nCPU_SCOPE_STATUS=%s\nPERF_STATUS=%s\n' \
    "$software_status" "$hardware_status" "$cpu_scope_status" "$perf_status"
fi
if [[ "$mode" != --all ]]; then printf 'ENGINEERING_STATUS=UNVERIFIED (partial audit mode)\n'
elif ((missing > 0 || old > 0 || unverified > 0)); then printf 'ENGINEERING_STATUS=BLOCKED\n'
elif [[ "$perf_status" == PASS ]]; then printf 'ENGINEERING_STATUS=PASS\n'
elif [[ "$perf_status" == NON_BLOCKING_PMU_LIMITATION ]]; then printf 'ENGINEERING_STATUS=PASS_WITH_NONBLOCKING_PMU_LIMITATION\n'
else printf 'ENGINEERING_STATUS=BLOCKED (perf requires evidence-based review)\n'; fi
printf 'AUDIT_COMPLETED=yes; exit 0 means the audit ran, not that every requirement passed.\n'
exit 0
