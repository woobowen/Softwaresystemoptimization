set -eu
set -x
uname -sr
lscpu | sed '/^Flags:/d; /^Vulnerability/d'
