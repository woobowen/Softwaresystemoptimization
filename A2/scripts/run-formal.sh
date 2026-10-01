#!/usr/bin/env bash
# Use the same Java and font library for each SPEC process.
set -euo pipefail
export JAVA_HOME="$HOME/.local/opt/java-se-7u75-ri"
export PATH="$JAVA_HOME/bin:$PATH"
export LC_ALL=C.UTF-8
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libfreetype.so.6
export SPEC_HOME="$HOME/.local/opt/specjvm2008"
unset CLASSPATH JAVA_TOOL_OPTIONS _JAVA_OPTIONS JDK_JAVA_OPTIONS
exec python3 -B "$(dirname "$0")/run-spec.py" "$@"
