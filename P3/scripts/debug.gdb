set pagination off
set confirm off
set style enabled off
set trace-commands on
file loop/loop.aarch64.gcc.debug
target remote /tmp/p3-qemu-gdb3.sock
show architecture
break loop.c:60
continue
next
print IterMul
backtrace
continue
quit
