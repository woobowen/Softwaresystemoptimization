export JAVA_HOME=/home/addaswsw/.local/opt/java-se-7u75-ri
export PATH="$JAVA_HOME/bin:$PATH"
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libfreetype.so.6
PS4='$ '
set -x
printenv JAVA_HOME
printenv LD_PRELOAD
command -v java
java -version
javac -version
printf 'CLASSPATH=%s\n' "${CLASSPATH-<unset>}"
printf 'JAVA_TOOL_OPTIONS=%s\n' "${JAVA_TOOL_OPTIONS-<unset>}"
printf '_JAVA_OPTIONS=%s\n' "${_JAVA_OPTIONS-<unset>}"
printf 'JDK_JAVA_OPTIONS=%s\n' "${JDK_JAVA_OPTIONS-<unset>}"
readlink -f /usr/bin/java
