#!/usr/bin/env bash
set -eu
export JAVA_HOME="$HOME/.local/opt/java-se-7u75-ri"
export PATH="$JAVA_HOME/bin:$PATH"
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libfreetype.so.6
export LC_ALL=C.UTF-8
unset CLASSPATH JAVA_TOOL_OPTIONS _JAVA_OPTIONS JDK_JAVA_OPTIONS
printf '$ java -version\n'
java -version
printf '\n$ javac -version\n'
javac -version
printf '\n$ command -v java\n'
command -v java
printf '\nSelected process environment:\n'
python3 - <<'PY'
import os
for key in ('JAVA_HOME', 'LD_PRELOAD', 'CLASSPATH', 'JAVA_TOOL_OPTIONS',
            '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS'):
    print(key + '=' + os.environ.get(key, '<unset>'))
PY
printf '\nClocksource after timing diagnostics:\n'
cat /sys/devices/system/clocksource/clocksource0/current_clocksource
