# A1 初试环境和工具

学号：10245102410

姓名：吴博闻

## 系统信息

| 项目 | 环境 |
|---|---|
| 操作系统 | Ubuntu 24.04.2 LTS（WSL2） |
| CPU | Intel Core Ultra 9 185H |
| 内存 | 15.42 GiB（WSL2 中显示） |

## 1. 环境搭建和工具安装

实验使用的软件版本与任务文档中的参考版本有所不同，满足课程要求。

OpenCilk 3.0 使用官方 Ubuntu 24.04 二进制包，安装在 `~/.local/opt/opencilk-3.0/`。它自带的 Clang 可编译运行 `cilk_for` 示例，结果为 `sum = 85344`。系统默认 Clang 为 18.1.3，后面的 ASan 实验使用系统 Clang 及其运行库。

![OpenCilk 版本与编译运行](images/opencilk-smoke.png)

这里的 `perf` 软件事件可用，硬件事件 `cycles` 和 `instructions` 提示不支持。

## 2. 常用工具命令操作练习

### (1) uname -a

![01-system](images/01-system.png)

```bash
uname -a
```

**a. 输出信息。** 依次为内核名称、主机名、内核版本、构建信息、机器架构、处理器类型、硬件平台和操作系统。输出中的 `Linux` 是内核名称，`#1 SMP PREEMPT_DYNAMIC ...` 是构建信息，后三个 `x86_64` 对应机器架构、处理器类型和硬件平台，最后为 `GNU/Linux`。

**b. 内核与指令集架构。** 内核版本为 `6.18.33.2-microsoft-standard-WSL2`，指令集架构为 x86-64。

### (2) cat /etc/os-release

```bash
cat /etc/os-release
```

**a. 发行版字段。** `NAME` 为发行版名称 Ubuntu；`VERSION` 为含代号的版本说明；`ID=ubuntu` 是程序识别用的名称；`VERSION_ID=24.04` 是版本号；`PRETTY_NAME` 为完整名称 Ubuntu 24.04.2 LTS。`VERSION_CODENAME` 和 `UBUNTU_CODENAME` 均为 noble，`ID_LIKE=debian` 表示所属发行版家族。其余字段给出相关网站和标识信息。这些字段描述发行版，与 `uname` 中的内核版本不同。

### (3) sysctl -a

![02-sysctl](images/02-sysctl.png)

```bash
sysctl -a
sysctl kernel.ostype kernel.osrelease vm.swappiness
cat /proc/sys/kernel/ostype /proc/sys/kernel/osrelease /proc/sys/vm/swappiness
```

**a. 功能和 -a。** `sysctl` 读取或修改运行时内核参数；`-a` 列出可读取的参数。

**b. 与 /proc/sys 的关系。** 点分名称对应 `/proc/sys` 下的路径，例如 `vm.swappiness` 对应 `/proc/sys/vm/swappiness`。这里两种方式读到的值相同，`vm.swappiness` 为 60。

**c. 与前两条命令比较。** `kernel.ostype` 为 Linux，`kernel.osrelease` 为 `6.18.33.2-microsoft-standard-WSL2`，与 `uname` 一致；`/etc/os-release` 中的 Ubuntu / 24.04 是发行版名称和版本，含义不同。

**d. 两个参数的含义。**

| 参数 | 值 | 含义 |
|---|---:|---|
| kernel.perf_event_paranoid | 2 | 限制无特权性能监控，普通用户只能测量用户态，不能测量内核态 |
| kernel.perf_event_max_sample_rate | 100000 | 每秒允许的最大采样率，过高会增加系统负担 |

### (4) lscpu

![03-lscpu](images/03-lscpu.png)

```bash
lscpu
lscpu -C
```

**a. 型号、核、线程、频率和缓存。**

| 项目 | 结果 |
|---|---|
| 型号 | Intel(R) Core(TM) Ultra 9 185H |
| 架构 / 大小端 | x86_64 / Little Endian |
| 处理器插槽 / 每插槽核心数 / 每核心线程数 | 1 / 11 / 2 |
| 逻辑 CPU | 22，编号 0–21 |
| Address sizes | 46 bits physical，48 bits virtual |
| 基准 / 最大 / 最小频率 | WSL2 中没有显示，无法得到这三个数值 |

表中的 11 个核心、22 个逻辑 CPU 是 WSL2 显示的虚拟拓扑，不能直接代表宿主机的物理核数或 P/E 核心布局。BogoMIPS 也不是 CPU 频率。

| 缓存 | 每个实例容量（lscpu -C） | 实例数 | lscpu 汇总容量 |
|---|---:|---:|---:|
| L1d | 48 KiB | 11 | 528 KiB |
| L1i | 64 KiB | 11 | 704 KiB |
| L2 | 2 MiB | 11 | 22 MiB |
| L3 | 24 MiB | 1 | 24 MiB |

**b. 大小端与应用场景。** 小端序表示多字节对象的低有效字节放在低地址。TCP/IP 协议中多字节整数字段的网络字节序采用大端序。

**c. Address sizes。** `physical` 是物理地址宽度，`virtual` 是虚拟地址宽度，这里分别为 46 位和 48 位。64 位指令集和通用寄存器并不要求地址也实现全部 64 位，页表和地址转换硬件只使用其中一部分，因此两项都不是 64 位。

### (5) dmidecode

![04-dmidecode-numa](images/04-dmidecode-numa.png)

```bash
dmidecode
```

**a. 功能。** `dmidecode` 解码固件提供的 DMI/SMBIOS 表，显示硬件信息。

**b. 内存信息。** 通常可看到内存条的容量、插槽、类型、速度、制造商、序列号、位宽和配置速度。WSL2 中无法读取 DMI 表，因此这里看不到宿主机的内存条信息。

### (6) numactl -H / --show

```bash
numactl -H
numactl --show
```

**a. 功能与 -H。** `numactl` 可为程序设置 CPU 和内存的 NUMA 策略；`-H`（`--hardware`）显示节点、CPU、节点内存及距离。

**b. 节点数。** 只有 1 个节点 node 0，包含逻辑 CPU 0–21。

**c. 距离与应用。** `node distances` 表示节点间的相对访问代价，数值越大通常表示访问代价越高。这里只有一个节点，本地距离为 10。多节点机器上的数据库、矩阵计算等内存密集型程序会受其影响，通常应尽量让线程和它使用的内存位于同一节点。

**d. --show 的作用、输出分析和区别。** `--show` 显示当前进程的 NUMA 策略与绑定，输出含义如下：

| 字段及结果 | 含义 |
|---|---|
| policy: default | 使用默认内存策略 |
| preferred node: current | 默认优先使用线程所在节点的内存 |
| physcpubind: 0 … 21 | 允许执行的逻辑 CPU |
| cpubind: 0 | 上述 CPU 所属的 NUMA 节点 |
| nodebind: 0 | 绑定的节点集合 |
| membind: 0 | 可用的内存节点集合 |
| preferred: 空 | 没有额外列出的优先节点 |

`-H` 显示硬件拓扑，`--show` 显示进程的策略。

### (7) free -h

```bash
free -h
```

**a. 两行及各列含义。** `Mem` 表示物理内存，`Swap` 表示交换空间。`total` 是总量；`used` 是已使用量；`free` 是完全空闲量；`shared` 主要是 tmpfs 等共享内存；`buff/cache` 是缓冲区、页缓存和可回收 slab；`available` 是系统估计无需使用交换空间、还能提供给新程序的内存。Swap 行只有 total、used、free，使用量为 0B。

**b. 单位。** GiB = 2^30 = 1,073,741,824 字节，GB = 10^9 = 1,000,000,000 字节；1 GiB ≈ 1.074 GB。`-h` 自动换算为便于阅读的二进制单位，例如 `15Gi`。

### (8) ps -aux

![05-ps-uptime](images/05-ps-uptime.png)

```bash
ps -aux
```

**a. 每列含义。**

| 列 | 含义 |
|---|---|
| USER / PID | 有效用户 / 进程 ID |
| %CPU | 累计 CPU 时间与进程从启动至今经过的时间之比 |
| %MEM | RSS 与可见物理内存之比 |
| VSZ / RSS | 虚拟地址空间大小 / 当前驻留内存，通常以 KiB 计 |
| TTY | 控制终端，`?` 表示没有 |
| STAT | 进程状态及附加标记；如 R 运行、S 可中断睡眠、D 不可中断睡眠、Z 僵尸，s 为会话首进程、+ 为前台进程组 |
| START / TIME | 启动时间 / 累计 CPU 时间 |
| COMMAND | 命令及参数 |

### (9) top 与 htop

![top-live](images/top-live.png)

![htop-live](images/htop-live.png)

```bash
top
htop
```

**a. top 各栏。** 摘要区依次为：当前时间、运行时长、登录用户数、1/5/15 分钟平均负载；Tasks 显示任务总数及运行、睡眠、停止、僵尸状态的数量；CPU 时间 `us/sy/ni/id/wa/hi/si/st` 分别表示用户态、内核态、调整过 nice 值的用户态、空闲、I/O 等待、硬中断、软中断和被虚拟化平台占用的时间；Mem/Swap 显示内存与交换空间的使用情况。

进程列 `PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND` 分别是进程 ID、用户、调度优先级、nice、虚拟内存、驻留内存、可共享驻留内存、状态、CPU 利用率、内存占比、累计 CPU 时间（到百分之一秒）和命令。

**b. top 与 htop 比较。** top 以紧凑的文本显示系统和进程信息，通常随系统安装。htop 用彩色条形图显示各 CPU 和内存负载，搜索、筛选、树状显示及调整优先级等操作更直观，通常需要另外安装。

### (10) vmstat 1

![06a-vmstat-mpstat](images/06a-vmstat-mpstat.png)

```bash
vmstat 1
```

### (11) mpstat -P ALL 1

```bash
mpstat -P ALL 1
```

### (12) pidstat 1

![06b-pidstat-iostat](images/06b-pidstat-iostat.png)

```bash
pidstat 1
```

`pidstat` 默认显示采样期间有活动的进程，所以系统空闲时可能没有进程记录。

### (13) iostat -xz 1

```bash
iostat -xz 1
```

**（10）—（13）共同问题 a、b：参数 1 与统计范围。**

| 命令 | 参数 1 的作用 | 主要统计内容 |
|---|---|---|
| vmstat 1 | 每 1 秒刷新，首份速率数据为开机以来的平均值 | 进程、内存、交换、块设备 I/O、中断、上下文切换和 CPU 时间 |
| mpstat -P ALL 1 | 每 1 秒统计一次 | 每个逻辑 CPU 及总体的用户态、内核态、中断、等待和空闲等时间比例 |
| pidstat 1 | 每 1 秒统计一次活动进程 | 进程的用户态、内核态、虚拟机 CPU 时间、总 CPU 利用率、等待运行比例及所在 CPU |
| iostat -xz 1 | 每 1 秒刷新，首份报告为开机以来的统计 | CPU 摘要及设备 I/O 速率、吞吐量、合并请求、平均等待时间、队列长度和利用率；-x 显示扩展统计，-z 省略无活动设备 |

**c. CPU 利用率的区别。** `ps` 的 `%CPU` 是进程从启动至今的平均值，`pidstat`、`top` 和 `htop` 通常显示相邻采样间的利用率。让一个进程先睡眠 3 秒，再单线程忙循环 8 秒，得到以下结果：

| 工具 | 观察结果 | 解释 |
|---|---|---|
| ps（指定 PID） | 进程启动约 3/5/7/9 秒时为 14.0/45.3/59.9/68.3% | 包含前 3 秒睡眠，因此平均值逐步上升 |
| pidstat -p 4 1 6 | 六个区间均为 100.00% | 每个 1 秒区间中，该线程持续占用一个 CPU |
| top -d 1 -p 4 | 刷新记录中为 100.0% | 按相邻刷新间增加的 CPU 时间计算 |
| htop -d 10 -p 4 | 显示 99.9% | 这里 -d 10 表示每 1 秒刷新，按采样间增加的 CPU 时间计算 |

这里三个实时工具都以一个逻辑 CPU 满载为 100%，多线程进程可能超过 100%。一个满载线程约占 22 个逻辑 CPU 总计算容量的 1/22，不能把它的进程利用率当成整机利用率。

### (14) sar -n DEV 1

![07-sar](images/07-sar.png)

```bash
sar -n DEV 1
```

**a.** `1` 为连续采样间隔 1 秒。

**b.** `-n DEV` 查看网络接口统计。`IFACE` 是接口名；`rxpck/s`、`txpck/s` 是每秒收、发包数；`rxkB/s`、`txkB/s` 是每秒收、发的数据量（KiB）；`rxcmp/s`、`txcmp/s` 是每秒收、发压缩包数；`rxmcst/s` 是每秒接收组播包数；`%ifutil` 是接口利用率。

### (15) uptime

```bash
uptime
```

**a. 输出信息。** 时间为 11:24:32，系统已运行 1 小时 33 分钟，有 1 个登录用户；1/5/15 分钟平均负载分别为 0.17/0.08/0.09。

**b. load average。** 表示正在运行、等待 CPU 和处于不可中断等待状态的任务的平均数量，不是 CPU 使用率。这里有 22 个逻辑 CPU，判断负载高低时应结合 CPU 数量。

### (16) /proc/interrupts 和 /proc/softirqs

![08-interrupts](images/08-interrupts.png)

```bash
cat /proc/interrupts
cat /proc/softirqs
```

**a. 输出信息。** 两者按 CPU 列出累计中断次数。`interrupts` 包含设备 IRQ 号、控制器、触发类型、设备名，以及 CAL/RES 等核间中断和 Hyper-V 中断；`softirqs` 按 SCHED、RCU、TIMER、NET_RX 等软中断类别列出计数。

**b. 最频繁的中断。** `interrupts` 中 CAL 最多，与 CPU 间函数调用有关；软中断中 SCHED 最多，说明调度活动较频繁。各 CPU 的计数合计如下：

| 类别 | 第二次快照累计 | 约 3 秒增量 | 解释 |
|---|---:|---:|---|
| interrupts 的 CAL | 1,099,564 | 2,304 | CPU 间函数调用 |
| interrupts 的 HVS | 703,003 | 1,920 | Hyper-V stimer0 虚拟定时器中断 |
| 数字设备 IRQ 25 | 8,236 | 0 | 设备队列中断，标签为 virtio0-virtqueues |
| softirqs 的 SCHED | 523,180 | 1,548 | 调度相关软中断 |
| softirqs 的 RCU | 292,807 | 899 | RCU 相关延迟处理活动 |

如果只比较数字设备 IRQ，累计次数最多的是 IRQ 25，但这约 3 秒内没有增长。WSL2 中无法获取宿主机物理设备的 IRQ 分布。

### (17) lstopo

![09-topology](images/09-topology.png)

```bash
lstopo --of svg > topo.svg
lstopo --of console
```

![WSL2 拓扑](images/topo.svg)

hwloc 2.10.0 的拓扑图中，Machine 的内存标为约 15GB；包含 1 个 Package、1 个 NUMA node 0 和共享的 24MB L3。共有 11 个 Core，每个 Core 下有 2 个 PU（逻辑处理器），合计 22 个 PU；每个核心有 2MB L2、48KB L1d 和 64KB L1i。图中的省略符和“11x total”表示重复的核心组。

### (18) Git 命令

![10-git](images/10-git.png)

**1. 用户名和邮件。** 为练习仓库设置用户名和邮件：

```bash
git init
git config user.name woobowen
git config user.email woobowen@gmail.com
```

不带 `--global` 时配置只对当前仓库生效，加上 `--global` 则作为当前用户各仓库的默认配置。

**2. 初始化与分支。** 练习仓库在 `git init` 后的分支名为 `master`。设置以后新仓库默认分支的命令是 `git config --global init.defaultBranch main`；修改当前分支名称是 `git branch -m main`。

**3. 首次 commit。** 空暂存区执行：

```bash
git commit -m 'chore: initial empty attempt'
```

提示 `nothing to commit`，未能提交。先创建文件并用 `git add` 加入暂存区，再提交：

```bash
printf 'A1 Git exercise\n' > hello.txt
git add hello.txt
git commit -m 'docs: add exercise note'
```

这样便创建了首次提交。

**4. 图片、忽略和取消跟踪。** 将图片 `test.png` 放入练习仓库后：

```bash
git add test.png
git commit -m 'test: add sample image'
printf 'test.png\n' > .gitignore
git ls-files test.png
git rm --cached test.png
git add .gitignore
git commit -m 'chore: stop tracking sample image'
git status --short --ignored
```

仅加入 `.gitignore` 不会停止跟踪已有文件，所以 `git ls-files test.png` 仍显示图片。`git rm --cached` 取消跟踪并保留本地图片，之后状态显示 `!! test.png`，表示它已被忽略；先前提交中的图片仍然保留。

**5. Conventional Commits。** 提交说明采用 `type(scope): description`，分别表示修改类型、可选的影响范围和简短说明，例如 `feat` 表示新功能，`fix` 表示修复问题；`!` 或页脚中的 `BREAKING CHANGE:` 表示不兼容变更。统一格式有助于快速理解提交意图，也便于生成变更记录。

**6. merge 与 rebase。** merge 保留原有提交关系，分支已分叉时通常生成合并提交，能够快进时只移动分支指针。rebase 把提交重放到新的起点，形成线性历史，同时改变提交 ID。merge 适合合并协作分支，rebase 适合整理尚未共享的本地提交；对已共享的历史使用 rebase 会影响他人的工作，需要先协调。

## 3. MIT 6.172 Homework 1

以下基于老师提供的代码完成。W2–W4 的命令在 `mit6172/c-primer/` 中执行，W5–W8 的命令在 `mit6172/matrix-multiply/` 中执行。

### Write-up 2

![writeup2-pointer](images/writeup2-pointer.png)

原始 `make pointer` 报出六条 const 相关编译错误。注释非法语句后，程序输出 `char d = 6`。[代码](mit6172/c-primer/pointer.c)。

`argv` 在函数形参中由 `char *argv[]` 调整为 `char **`。`&i` 取 i 的地址，`*pi` 解引用取得 5，所以 j 为 5。数组 c 在赋给 pc 时退化成指向 c[0] 的指针，`*pc` 是字符 `'6'`，不是数值 6。`pcp = argv` 两端都是 `char **`。

| 声明/语句 | 是否合法及原因 |
|---|---|
| `const char *pcc` / `char const *pcc2` | 同一种类型：指向只读 char 的可修改指针；限制通过该指针修改对象，不表示 c 本身成为 const |
| `*pcc = '7'` | 非法，通过 pcc 得到的 char 不可修改 |
| `pcc = *pcp` / `pcc = argv[0]` | 合法，指针自身可变；char * 可赋给 const char *，增加所指对象的 const 限定 |
| `char *const cp = c` | 指针自身 const，所指 char 可变 |
| `cp = *pcp` / `cp = *argv` | 非法，重赋值 const 指针 |
| `*cp = '!'` | 合法，c 是可写字符数组 |
| `const char *const cpc = c` | 指针自身和经其访问的 char 均不可修改 |
| `cpc = *pcp` / `cpc = argv[0]` | 非法，修改指针自身 |
| `*cpc = '@'` | 非法，通过 cpc 修改只读 char |

### Write-up 3

![writeup3-sizes](images/writeup3-sizes.png)

`PRINT_SIZE` 宏输出各类型及其指针大小，数组 x 和结构体 you 分别通过 `&x`、`&you` 取得地址。[sizes.c](mit6172/c-primer/sizes.c)。

```bash
make sizes
./sizes
```

在 x86-64 环境中，这些指针均为 8 字节。数组 x 含 5 个 int，大小为 20 字节；`&x` 指向整个数组，指针大小为 8 字节。student 的两个 int 共占 8 字节。

### Write-up 4

![writeup4-swap](images/writeup4-swap.png)

原程序输出 `k = 1, m = 2`，因为按值传参只交换了形参副本。改为传入 `k`、`m` 的地址后，`swap` 通过解引用修改原变量：

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

交换后输出 `k = 2, m = 1`，`verifier.py` 检查 sizes 和 swap 后输出 `LGTM`。老师的脚本使用 Python 2 语法，这里将打印、参数判断和子进程输出处理适配为 Python 3，保留原有预期值和检查规则。

### Write-up 5

将 `CFLAGS_RELEASE` 从 `-O1 -DNDEBUG` 改为 `-O3 -DNDEBUG` 后，`make clean` 删除旧构建文件，`make` 使用系统 Clang 18.1.3，以 `-O3` 分别编译两个 C 文件，再链接生成 `matrix_multiply`。

![writeup5-build](images/writeup5-build.png)

提高优化级别后，原程序仍发生 SIGSEGV。GDB 定位到原 `matrix_multiply.c:90`：A 为 4×5，B/C 为 4×4；当 `i=0, j=0, k=4` 时，访问 B 的第 5 行越界。

![writeup5-gdb](images/writeup5-gdb.png)

开启断言后提示 `A->cols = 5, B->rows = 4`。将 A 也改为 4×4 后，矩阵维度一致，越界崩溃消失。

### Write-up 6

修正矩阵维度后，ASan 检测到了内存泄漏：

![writeup6-asan](images/writeup6-asan.png)

使用 ASan 的命令为：

```bash
make clean
make ASAN=1
./matrix_multiply
```

关键错误信息为：

```text
ERROR: LeakSanitizer: detected memory leaks
Direct leak of 32 byte(s) in 2 object(s)
Indirect leak of 128 byte(s) in 8 object(s)
Indirect leak of 64 byte(s) in 2 object(s)
SUMMARY: AddressSanitizer: 224 byte(s) leaked in 12 allocation(s).
```

泄漏来自 `make_matrix` 中分配的矩阵结构体、行指针数组和行数据，它们在程序结束前没有释放。ASan 未报告未初始化值问题，随后由 Valgrind 定位。

### Write-up 7

![writeup7-result](images/writeup7-result.png)

Valgrind 提示 `Use of uninitialised value`，并指出条件分支依赖未初始化值。原因是 `make_matrix` 用 `malloc` 分配行数据，而 `C->values[i][j] += ...` 在首次累加前没有将 C 置零。将行分配改为 `calloc(cols, sizeof(int))` 后，矩阵乘法结果正确。

```bash
make
./matrix_multiply -p
```

例如 C[0][0] = 3×1 + 7×5 + 8×0 + 1×9 = 47。

### Write-up 8

![writeup8-valgrind](images/writeup8-valgrind.png)

修复初始化后仍存在内存泄漏：48 字节（3 块）直接丢失，288 字节（15 块）间接丢失，原因是 A、B、C 没有释放。在程序结束前分别调用 `free_matrix`，逐行释放数据，再释放行指针数组和矩阵结构体。

修复后 Valgrind 显示 `0 errors`，所有堆内存均已释放，无内存泄漏。
