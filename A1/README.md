# A1 初试环境和工具

## 1. 实验环境

| 项目 | 实际环境 |
|---|---|
| OS | Ubuntu 24.04.2 LTS，Windows 上的 WSL2 |
| Kernel | 6.18.33.2-microsoft-standard-WSL2 |
| Architecture | x86_64 |
| CPU | Intel Core Ultra 9 185H |
| GCC / Clang | 13.3.0 / 18.1.3 |
| Python / Java | 3.12.3 / OpenJDK 21.0.12（javac 21.0.12） |
| Valgrind / perf | 3.22.0 / 6.8.12 |

环境要求采用《环境搭建和工具安装》中的新版要求。`perf stat ls` 能取得软件事件；当前内核报告 `no PMU driver, software events only`，cycles、instructions、branches、branch-misses 均不支持。按环境文档，此项不强制要求。用户级 `perf` 链接指向 Ubuntu tools 包内 binary，系统 wrapper 未覆盖。[环境检查输出](evidence/final/environment_final_check.txt)。

以下 CPU、NUMA 和内存数据均为本次 Linux guest 可见信息，不当作 Windows 宿主物理硬件的完整清单。进程列表还受当前终端的 PID namespace 限制。

## 2. 常用系统工具

已实际执行各命令，并查阅本机 `man` 文档。较长输出仅节选；完整输出和本机手册保存在 [linux_commands](evidence/linux_commands/) 中。

### 2.1 uname

```bash
uname -a
```

```text
Linux LAPTOP-KI0GT6AJ 6.18.33.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun 18 21:54:43 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
```

`-a` 显示内核名称、节点名、内核 release、内核构建版本、机器架构、处理器类型、硬件平台和操作系统等信息。这里 `Linux` 是内核名称，`LAPTOP-KI0GT6AJ` 是节点名，`#1 SMP PREEMPT_DYNAMIC ...` 是构建/调度相关版本信息；后面的三个 `x86_64` 分别对应 machine、processor、hardware platform，末尾为 `GNU/Linux`。

本机 **内核版本为 `6.18.33.2-microsoft-standard-WSL2`，指令集架构为 `x86_64`**。[原始输出](evidence/linux_commands/uname_a.txt)。

### 2.2 sysctl

```bash
sysctl -a
ls /proc/sys
sysctl kernel.hostname kernel.osrelease vm.swappiness
cat /proc/sys/kernel/hostname
cat /proc/sys/kernel/osrelease
cat /proc/sys/vm/swappiness
```

`sysctl` 用于读取或修改运行时内核参数；本次仅执行读取。`-a` 尝试列出当前可用的参数及其值。部分受保护参数出现 `permission denied`，完整日志保留这些消息，没有为读取而修改权限。

Linux 上这些参数通过 `/proc/sys` 暴露。例如本次读取：

```text
kernel.hostname = LAPTOP-KI0GT6AJ
kernel.osrelease = 6.18.33.2-microsoft-standard-WSL2
vm.swappiness = 60
```

分别与 `/proc/sys/kernel/hostname`、`/proc/sys/kernel/osrelease`、`/proc/sys/vm/swappiness` 的文件内容一致。点号形式的参数名通常对应目录分隔路径；`/proc/sys` 是内核提供的虚拟接口，并非普通磁盘配置文件。[完整 sysctl 输出](evidence/linux_commands/sysctl_a.txt)、[路径对应验证](evidence/linux_commands/proc_sys_mapping.txt)。

### 2.3 top

```bash
top
```

在交互界面观察刷新后按 `q` 正常退出。首次屏幕的摘要和列名如下：

```text
top - 18:56:11 up  1:38,  1 user,  load average: 0.14, 0.08, 0.02
Tasks:   3 total,   1 running,   2 sleeping,   0 stopped,   0 zombie
%Cpu(s):  1.8 us,  4.8 sy,  0.0 ni, 93.0 id,  0.0 wa,  0.0 hi,  0.4 si,  0.0 st 
MiB Mem :  15794.2 total,  13236.2 free,   1782.8 used,    997.1 buff/cache     
MiB Swap:   4096.0 total,   4096.0 free,      0.0 used.  14011.3 avail Mem 

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND  
```

- 首行显示当前时间、系统运行时间、登录用户数，以及过去 1、5、15 分钟的 load average。load average 是可运行及不可中断等待任务数量的平均值，不是 CPU 使用百分比。
- `Tasks` 是当前可见任务数及 running、sleeping、stopped、zombie 状态分布。本次仅可见 3 个任务，不能据此说整个 WSL 或 Windows 只有 3 个进程。
- CPU 行中 `us/sy/ni/id/wa/hi/si/st` 分别为用户态、内核态、调整 nice 的用户态、空闲、I/O 等待、硬中断、软中断和虚拟化 steal 时间占比。
- 内存行给出总量、空闲、使用量及缓冲/缓存；swap 行给出交换空间及可用内存估计，屏幕使用 MiB。

| 列 | 含义 |
|---|---|
| PID / USER | 进程 ID / 所属用户 |
| PR / NI | 调度优先级 / nice 值 |
| VIRT / RES / SHR | 虚拟内存量 / 驻留物理内存量 / 可共享的驻留内存量 |
| S | 进程状态，如 R 运行、S 睡眠 |
| %CPU / %MEM | CPU 使用率 / 驻留内存占可用物理内存总量的比例 |
| TIME+ | 累计 CPU 时间，显示到百分之一秒 |
| COMMAND | 命令名 |

[原始交互记录](evidence/linux_commands/top.txt)、[去除终端控制码的文本](evidence/linux_commands/top_plain.txt)。

### 2.4 dmidecode

```bash
dmidecode
```

```text
# dmidecode 3.5
Scanning /dev/mem for entry point.
Can't read memory from /dev/mem
```

该工具解码固件提供的 DMI/SMBIOS 表，通常可以了解系统、BIOS、主板和内存设备信息；它不是直接探测 DIMM 的工具。以内存为例，若表存在，可包含内存阵列容量、槽位、模块容量、类型、速度、厂商等记录。

**本次没有读到任何内存设备记录**，所以无法报告 DIMM 数量、每条容量、速度或厂商。进一步检查发现当前环境的 `/dev/mem`、`/sys/firmware/dmi/tables`、`/sys/class/dmi/id` 均不存在，不能把这个问题仅解释为普通用户权限不足。没有虚构物理机数据；后面的 `free` 反映 guest 可用内存，不是 DIMM 清单。[命令输出](evidence/linux_commands/dmidecode.txt)、[DMI 接口检查](evidence/linux_commands/dmi_availability.txt)。

### 2.5 numactl

```bash
numactl -H
```

```text
available: 1 nodes (0)
node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21
node 0 size: 15794 MB
node 0 free: 13319 MB
node distances:
node   0 
  0:  10 
```

`numactl` 可以控制进程的 NUMA 内存分配策略和 CPU/节点绑定；`-H`（`--hardware`）查看可用 NUMA 节点及其 CPU、内存和节点距离。本次 **guest 可见 1 个节点，编号 0**，包含 CPU 0–21。距离矩阵仅显示节点自身的距离 10。[原始输出](evidence/linux_commands/numactl_H.txt)。

### 2.6 lscpu 与 /proc/cpuinfo

```bash
lscpu
cat /proc/cpuinfo
```

`lscpu` 主要结果：

```text
Architecture:        x86_64
CPU op-mode(s):       32-bit, 64-bit
CPU(s):              22
On-line CPU(s) list:  0-21
Model name:          Intel(R) Core(TM) Ultra 9 185H
Thread(s) per core:  2
Core(s) per socket:  11
Socket(s):           1
Hypervisor vendor:   Microsoft
NUMA node(s):        1
```

除上述项目外，还显示字节序、地址宽度、CPU family/model、指令特性、缓存和漏洞缓解信息。该处理器型号为 **Intel Core Ultra 9 185H**。

按本次 **Linux guest 可见拓扑**，`1 socket × 11 cores/socket × 2 threads/core = 22 logical CPUs`，即显示 11 个 core、每 core 两个硬件线程槽位，呈现 SMT 拓扑。WSL 可能重建或裁剪拓扑，**不能由此断言宿主物理 CPU 实际只有 11 核，或其全部核心都采用相同 SMT 配置**；宿主真实 P/E 核布局未由本实验验证。

`lscpu` 综合 sysfs、`/proc/cpuinfo` 等接口，提供汇总后的拓扑视图；`/proc/cpuinfo` 是内核提供的逐逻辑处理器文本记录，包含 processor 编号、型号、频率/特性等，内容依架构而异，重复信息较多。[lscpu 完整输出](evidence/linux_commands/lscpu.txt)、[cpuinfo 完整输出](evidence/linux_commands/cpuinfo.txt)。

### 2.7 free

```bash
free
free -h
```

默认输出：

```text
               total        used        free      shared  buff/cache   available
Mem:        16173224     1753620    13636844        4056     1011008    14419604
Swap:        4194304           0     4194304
```

`Mem` 是 guest 可用物理内存统计，`Swap` 是交换空间统计。本次 Mem 总量为 16173224 KiB，Swap 总量为 4194304 KiB，已使用 Swap 为 0。

| 列 | 含义 |
|---|---|
| total | 可用内存或交换空间总量 |
| used | 已使用/不可用部分；本机手册中 Mem 按 `total - available` 计算 |
| free | 完全未使用的内存或交换空间 |
| shared | 主要由 tmpfs 使用的共享内存 |
| buff/cache | 内核 buffers、页缓存及可回收 slab 等的合计 |
| available | 无需换出即可供新程序使用的内存估计，不等同于 free |

本机 `man free` 明确默认单位为 **KiB（1024 字节）**。`free -h` 则自动使用带后缀的可读单位，本次显示 `15Gi` 内存和 `4.0Gi` swap；不能把这两种输出的裸数字按同一单位理解。[默认输出](evidence/linux_commands/free.txt)、[-h 输出](evidence/linux_commands/free_h.txt)。

## 3. vmstat / mpstat / pidstat / iostat 比较

实际在终端运行以下四条命令，观察约 4 秒后用 `Ctrl+C` 结束，未无限运行：

```bash
vmstat 1
mpstat -P ALL 1
pidstat 1
iostat -xz 1
```

| 命令 | 参数 `1` 与首份报告 | 主要统计内容及其他选项 |
|---|---|---|
| `vmstat 1` | 每秒更新；第一份速率类数据通常为开机以来平均，后续为采样区间；进程和内存列为即时值 | 全系统进程、内存、swap、块 I/O、中断/上下文切换及 CPU；输出按 procs、memory、swap、io、system、cpu 分组 |
| `mpstat -P ALL 1` | 每秒报告区间 CPU 活动；不能将本命令首份区间报告当作开机平均，`interval=0`/省略才使用开机统计 | `-P ALL` 输出全部在线 CPU 及 `all` 汇总；本次包含 CPU 0–21，列有 `%usr`、`%sys`、`%iowait`、`%idle` 等 |
| `pidstat 1` | 每秒报告进程统计；省略 interval 或设为 0 时使用开机以来统计 | 默认显示活动任务的 CPU 数据；本次采样只有列头，没有非零活动进程行，不补造进程读数。`-r`、`-d` 可另选内存/I/O，本次未把它们当作已执行命令 |
| `iostat -xz 1` | 每秒报告；第一份为开机以来统计，随后为相邻采样区间 | CPU 和块设备 I/O；`-x` 为扩展统计，`-z` 省略区间内无活动设备。实际有读写速率、合并请求、await、平均请求大小、队列长度和 `%util` 等列 |

这些命令都没有指定 count，所以默认持续采样，但首份报告和默认统计对象不同。例如 `vmstat` 首行 CPU idle 为 100，后续某次为 98；`iostat` 首份报告列出 sda–sdd，后续部分区间没有设备行，符合 `-z` 的筛选行为。

原始输出：[vmstat](evidence/linux_commands/vmstat.txt)、[mpstat](evidence/linux_commands/mpstat.txt)、[pidstat](evidence/linux_commands/pidstat.txt)、[iostat](evidence/linux_commands/iostat.txt)。终止时 `vmstat` 返回 130，其他工具正常汇总后退出，均为主动结束采样。

## 4. sar 网络统计

```bash
sar -n DEV 1
```

`1` 为一秒采样间隔；未指定 count 时持续报告，本次观察后用 `Ctrl+C` 结束。`-n DEV` 按网络接口统计流量。一个实际采样节选：

```text
18:56:11        IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil
18:56:12    loopback0     72.00     62.00     34.50     33.81      0.00      0.00      0.00      0.00
```

| 指标 | 含义 |
|---|---|
| IFACE | 网络接口名 |
| rxpck/s、txpck/s | 每秒接收、发送包数 |
| rxkB/s、txkB/s | 每秒接收、发送数据量；本机 sysstat 手册说明这里实际使用 KiB/s |
| rxcmp/s、txcmp/s | 每秒接收、发送的压缩包数 |
| rxmcst/s | 每秒接收的多播包数 |
| %ifutil | 按接口速率估算的利用率；半双工取收发之和，全双工取较大方向 |

本次有流量的 `loopback0` 显示 `%ifutil=0.00`，不能据此断言没有流量；虚拟/回环接口的速率信息不一定适合利用率估算。`DEV` 不等同于错误统计选项 `EDEV`，本次不报告未采集的错误计数。[完整网络采样](evidence/linux_commands/sar_network.txt)。

## 5. MIT 6.172 Homework 1

使用 MIT OCW Fall 2018 的 [Homework 1 文档](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/resources/homework-1-getting-started/) 和 [官方 starter code](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/resources/mit6_172f18_hw1/)。老师文档中的旧 PDF 页面返回 404，改从同一官方课程的 Assignments 页面定位原文件，没有更换作业。

公开 PDF 从第 1 节直接跳到第 4 节，未提供第 2、3 节正文；已阅读/练习第 1、4、5、7 节。第 6 节整体跳过，因此不做其中的矩阵扩容、循环调优和 Write-up 9/10；AWSRUN 与 Git 操作均忽略。Exercise 的完整输出不作为正式答案展开，仅保留支撑以下 Write-up 的必要结果。

### Write-up 2

原始 `pointer.c` 编译时产生 6 个 const 相关错误；按题目要求注释这些非法语句后编译成功，运行输出：

```text
char d = 6
```

| 代码/问题 | 解释 |
|---|---|
| `char *argv[]` | 作为函数形参会调整为 `char **argv`，指向参数字符串指针序列 |
| `int *pi = &i; int j = *pi;` | `&i` 取得 i 的地址，解引用得到 5，因此 j 为 5 |
| `char *pc = c; char d = *pc;` | 此表达式中数组 c 转换为首元素指针，d 得到字符 `'6'` |
| `pcp = argv` | 两边均为 `char **`，类型匹配 |
| `const char *pcc` 与 `char const *pcc2` | 两者同为“指向 const char 的可修改指针”，不能通过它修改字符 |
| `*pcc = '7'` | 非法：尝试经 const char 左值写入字符 |
| `pcc = *pcp; pcc = argv[0];` | 合法：修改的是非 const 的指针本身；`char *` 可转换为 `const char *` |
| `char *const cp = c` | cp 本身不能重新指向别处，指向的 char 可以修改 |
| `cp = *pcp; cp = *argv;` | 均非法：尝试重新赋值 const 指针 |
| `*cp = '!'` | 合法：修改可写字符数组 c 的第一个字符；先前 d 是值拷贝，不随之改变 |
| `const char *const cpc = c` | 指针本身及经其访问的字符均不可修改 |
| `cpc = *pcp; cpc = argv[0]; *cpc = '@';` | 前两条违反指针 const，第三条违反所指对象的 const，均非法 |

修复后的示例仍有题目允许的未使用变量警告，没有把警告写成编译失败。[源码](mit6172/c-primer/pointer.c)、[原始编译错误](evidence/mit6172/baseline_build.txt)、[修复与 verifier 输出](evidence/mit6172/c_primer_validation.txt)。

### Write-up 3

在 `sizes.c` 中对各类型及其指针使用 `sizeof`。结构体用 `&you`，数组用 `&x`；后者类型是 `int (*)[5]`，不是 `int **`。

```bash
cd mit6172/c-primer
make sizes
./sizes
```

实际完整输出：

```text
size of int : 4 bytes
size of int* : 8 bytes
size of short : 2 bytes
size of short* : 8 bytes
size of long : 8 bytes
size of long* : 8 bytes
size of char : 1 bytes
size of char* : 8 bytes
size of float : 4 bytes
size of float* : 8 bytes
size of double : 8 bytes
size of double* : 8 bytes
size of unsigned int : 4 bytes
size of unsigned int* : 8 bytes
size of long long : 8 bytes
size of long long* : 8 bytes
size of uint8_t : 1 bytes
size of uint8_t* : 8 bytes
size of uint16_t : 2 bytes
size of uint16_t* : 8 bytes
size of uint32_t : 4 bytes
size of uint32_t* : 8 bytes
size of uint64_t : 8 bytes
size of uint64_t* : 8 bytes
size of uint_fast8_t : 1 bytes
size of uint_fast8_t* : 8 bytes
size of uint_fast16_t : 8 bytes
size of uint_fast16_t* : 8 bytes
size of uintmax_t : 8 bytes
size of uintmax_t* : 8 bytes
size of intmax_t : 8 bytes
size of intmax_t* : 8 bytes
size of __int128 : 16 bytes
size of __int128* : 8 bytes
size of student : 8 bytes
size of student* : 8 bytes
size of x : 20 bytes
size of &x : 8 bytes
```

本次所有列出的对象指针均为 8 字节；`int x[5]` 是 20 字节，指向整个数组的 `&x` 是 8 字节。类型大小来自当前 x86_64 Linux ABI，不是 C 对所有平台的统一保证。[源码](mit6172/c-primer/sizes.c)、[输出](evidence/mit6172/writeup3_evidence.txt)。

### Write-up 4

原程序按值传递，交换的是形参副本，实测仍输出 `k = 1, m = 2`。改为传入变量地址，通过解引用修改调用者的变量：

```c
// Copyright (c) 2012 MIT License by 6.172 Staff

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

void swap(int* i, int* j) {
  int temp = *i;
  *i = *j;
  *j = temp;
}

int main() {
  int k = 1;
  int m = 2;
  swap(&k, &m);
  // What does this print?
  printf("k = %d, m = %d\n", k, m);

  return 0;
}
```

```bash
make swap
./swap
python3 verifier.py
```

```text
k = 2, m = 1
```

官方 `verifier.py` 原为 Python 2；仅将 print 语法、字符串参数判断和 subprocess 文本读取改为 Python 3，未改 expected values 或放宽校验。执行后对 sizes、pointer、swap 的检查全部通过，末尾输出 `LGTM`。[源码](mit6172/c-primer/swap.c)、[验证记录](evidence/mit6172/c_primer_validation.txt)。

### Write-up 5

将 `matrix-multiply/Makefile` 的 release 配置由 `-O1` 改为 `-O3`，其他构建结构保留。执行：

```bash
cd mit6172/matrix-multiply
make clean
make
```

实际编译/链接命令：

```text
clang -O3 -DNDEBUG -Wall -std=c99 -D_POSIX_C_SOURCE=200809L -c testbed.c -o testbed.o
clang -O3 -DNDEBUG -Wall -std=c99 -D_POSIX_C_SOURCE=200809L -c matrix_multiply.c -o matrix_multiply.o
clang -o matrix_multiply testbed.o matrix_multiply.o -lrt -flto -fuse-ld=gold
```

构建退出 0；此时尚未修复源代码，直接运行在输出 `Setup`、`Running matrix_multiply_run()...` 后发生段错误，退出 139。`-O3` 不会修复程序中的非法内存访问。

随后用 `make DEBUG=1` 和 GDB 的 `run`、`bt`、`print` 定位：崩溃发生在乘法累加语句，实测 `A->cols=5`、`B->rows=4`、`k=4`。启用原有 tbassert 后得到维度不匹配断言和 SIGABRT；将 A 创建为与 B、C 一致的 4×4 后消除了该越界。这里仍使用原作业的小矩阵，没有进行第 6 节的性能优化。

[Makefile](mit6172/matrix-multiply/Makefile)、[构建及段错误](evidence/mit6172/writeup5_evidence.txt)、[GDB 调试](evidence/mit6172/debug_segfault.txt)、[断言诊断](evidence/mit6172/debug_assertion.txt)。

### Write-up 6

在维度已修正、矩阵仍未初始化且未释放的阶段运行 ASan。系统 Clang 缺少 `libclang_rt.asan`，因此从 Ubuntu 官方包临时解出相同版本 runtime，仅在链接阶段传入 `-resource-dir`；编译器和题目逻辑未替换，系统库没有升级。复现方法见 [工具与阶段复现记录](evidence/mit6172/REPRODUCTION.md)。

ASan 程序的实际错误输出如下，退出码为 1：

```text
==9==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 32 byte(s) in 2 object(s) allocated from:
    #0 0x57c437651fc3 in malloc (/home/addaswsw/lab/Software_system_optimization/A1/mit6172/matrix-multiply/matrix_multiply+0xcafc3) (BuildId: 08d42407345a9b10e3a4f1dd7e77049cf48b1bb5)
    #1 0x57c437691159 in make_matrix /home/addaswsw/lab/Software_system_optimization/A1/mit6172/matrix-multiply/matrix_multiply.c:39:24

Indirect leak of 128 byte(s) in 8 object(s) allocated from:
    #0 0x57c437651fc3 in malloc (/home/addaswsw/lab/Software_system_optimization/A1/mit6172/matrix-multiply/matrix_multiply+0xcafc3) (BuildId: 08d42407345a9b10e3a4f1dd7e77049cf48b1bb5)
    #1 0x57c4376911e7 in make_matrix /home/addaswsw/lab/Software_system_optimization/A1/mit6172/matrix-multiply/matrix_multiply.c:48:35

Indirect leak of 64 byte(s) in 2 object(s) allocated from:
    #0 0x57c437651fc3 in malloc (/home/addaswsw/lab/Software_system_optimization/A1/mit6172/matrix-multiply/matrix_multiply+0xcafc3) (BuildId: 08d42407345a9b10e3a4f1dd7e77049cf48b1bb5)
    #1 0x57c4376911a2 in make_matrix /home/addaswsw/lab/Software_system_optimization/A1/mit6172/matrix-multiply/matrix_multiply.c:46:31

SUMMARY: AddressSanitizer: 224 byte(s) leaked in 12 allocation(s).
```

本次报告的是 LeakSanitizer 检出的 **224 字节泄漏**，不是“所有未初始化读都被 ASan 找到”。[LLVM 文档](https://clang.llvm.org/docs/AddressSanitizer.html)说明 ASan 需要编译插桩和运行库，Linux 上集成的 [LeakSanitizer](https://clang.llvm.org/docs/LeakSanitizer.html)负责泄漏检测；未初始化值属于另一类问题，[MemorySanitizer](https://clang.llvm.org/docs/MemorySanitizer.html)专门检测这类使用，本次按题目继续用 Valgrind 定位，未另做 MemorySanitizer 实验。

Valgrind 在此阶段实际报告 `Use of uninitialised value of size 8`，来源为 `make_matrix` 分配的内存，使用发生在输出 C 矩阵时。不能因为某次普通运行未崩溃就认定结果正确。[ASan 完整记录](evidence/mit6172/writeup6_evidence.txt)、[Valgrind 未初始化值诊断](evidence/mit6172/valgrind_before_initialization.txt)。

### Write-up 7

乘法使用 `C[i][j] += ...`，所以 C 必须从零开始。保留原 matrix 结构和三重循环，仅把 `make_matrix` 每行分配改为 `calloc(cols, sizeof(int))`。此时 `./matrix_multiply -p` 实际输出：

```text
Setup
Running matrix_multiply_run()...
Matrix A: 
------------
    3      7      8      1  
    7      9      8      3  
    1      2      6      7  
    9      8      1      9  
------------
Matrix B: 
------------
    1      3      0      1  
    5      5      7      8  
    0      1      9      8  
    9      3      1      7  
------------
---- RESULTS ----
Result: 
------------
   47     55    122    130  
   79     83    138    164  
   74     40     75    114  
  130     95     74    144  
------------
---- END RESULTS ----
Elapsed execution time: 0.000000 sec
```

例如 `C[0][0] = 3×1 + 7×5 + 8×0 + 1×9 = 47`。另用 [独立检查脚本](scripts/check_matrix.py)根据打印的 A、B 重新计算全部元素；普通输入和 `-pz` 零矩阵各运行 3 次，均一致且正确。输出中的 `0.000000 sec` 只是小矩阵在当前显示精度下的计时结果，不表示计算没有耗时，也不用于宣称加速比。[源码](mit6172/matrix-multiply/matrix_multiply.c)、[原始输出](evidence/mit6172/writeup7_evidence.txt)、[正确性检查](evidence/mit6172/matrix_correctness.txt)。

### Write-up 8

初始化修复后，Valgrind 仍报告 48 字节直接泄漏和 288 字节间接泄漏。随后在 `testbed.c` 使用结束处调用 `free_matrix(A)`、`free_matrix(B)`、`free_matrix(C)`，逐行释放矩阵及其容器。

```bash
make DEBUG=1
valgrind --leak-check=full --show-leak-kinds=all \
  --errors-for-leak-kinds=all --error-exitcode=97 ./matrix_multiply -p
```

实际输出末尾：

```text
==9== HEAP SUMMARY:
==9==     in use at exit: 0 bytes in 0 blocks
==9==   total heap usage: 39 allocs, 39 frees, 4,752 bytes allocated
==9== 
==9== All heap blocks were freed -- no leaks are possible
==9== 
==9== For lists of detected and suppressed errors, rerun with: -s
==9== ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)
```

Valgrind 命令退出 0；这里既检查了错误摘要，也检查了退出时剩余内存，未仅凭进程退出码判断。最终代码还通过一次 ASan 运行，退出 0。[testbed.c](mit6172/matrix-multiply/testbed.c)、[Valgrind 完整输出](evidence/mit6172/writeup8_evidence.txt)、[最终 ASan 输出](evidence/mit6172/asan_final.txt)。

## 6. 简要总结

本实验完成了系统工具的实际观察，以及从编译错误、段错误、断言到未初始化值和内存泄漏的定位与修复。系统工具反映的是当前可见环境；guest 拓扑、DMI 缺失和 PMU 限制不能用其他机器的数据替代。矩阵程序的最终普通构建已移除覆盖率插桩，保留 4×4 输入及原始循环顺序。

重新编译和检查可在本 README 所在的 `A1/` 目录执行：

```bash
make -C mit6172/c-primer
(cd mit6172/c-primer && python3 verifier.py)
make -C mit6172/matrix-multiply
python3 scripts/check_matrix.py
```
