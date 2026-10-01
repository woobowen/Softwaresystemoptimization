set -eu
export JAVA_HOME="$HOME/.local/opt/java-se-7u75-ri"
export PATH="$JAVA_HOME/bin:$PATH"
export LC_ALL=C.UTF-8
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libfreetype.so.6
unset CLASSPATH JAVA_TOOL_OPTIONS _JAVA_OPTIONS JDK_JAVA_OPTIONS
show() { printf '$'; printf ' %s' "$@"; printf '\n'; "$@"; }
show java -version
show command -v java
show printenv JAVA_HOME LD_PRELOAD
printf '\n$ env | rg "^(CLASSPATH|JAVA_TOOL_OPTIONS|_JAVA_OPTIONS|JDK_JAVA_OPTIONS)="\n'
if env | rg '^(CLASSPATH|JAVA_TOOL_OPTIONS|_JAVA_OPTIONS|JDK_JAVA_OPTIONS)='; then
    exit 1
else
    printf 'All four variables are unset.\n'
fi
show cat /sys/devices/system/clocksource/clocksource0/current_clocksource
printf '\nService state after measurements:\n'
show systemctl is-active systemd-timesyncd.service
show systemctl is-enabled systemd-timesyncd.service
