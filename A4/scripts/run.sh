#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
mode=${1:?usage: run.sh OUTPUT_DIRECTORY ITERATIONS REPEATS}
iterations=${2:?}
repeats=${3:?}
[[ $iterations =~ ^[1-9][0-9]*$ && $repeats =~ ^[1-9][0-9]*$ ]]
mkdir "$mode"
mode=$(cd "$mode" && pwd)
cd "$root/source"
for compiler in gcc clang; do
  if [[ $compiler == gcc ]]; then cc=gcc; cxx=g++; else cc=clang; cxx=clang++; fi
  for level in 0 1 2 3; do
    id="$compiler-O$level"
    { make clean; make all CC="$cc" CXX="$cxx" OPTLEVEL="-O$level"; } > "$mode/$id.build.txt" 2>&1
    stat -c '%n %s' loop_fusion > "$mode/$id.size.txt"
    sha256sum loop_fusion > "$mode/$id.binary.sha256"
    for ((run=1; run<=repeats; run++)); do
      printf '%s\n' "make report CC=$cc CXX=$cxx OPTLEVEL=-O$level ITERATIONS=$iterations" > "$mode/$id.run$run.command.txt"
      make report CC="$cc" CXX="$cxx" OPTLEVEL="-O$level" ITERATIONS="$iterations" > "$mode/$id.run$run.log" 2>&1
      mv report.txt "$mode/$id.run$run.txt"
      if grep -Eiq 'failed|error|could not allocate' "$mode/$id.run$run.txt"; then echo "benchmark error: $id run $run" >&2; exit 1; fi
      python3 "$root/scripts/check_report.py" "$mode/$id.run$run.txt"
      echo "$id run $run complete"
    done
  done
done
