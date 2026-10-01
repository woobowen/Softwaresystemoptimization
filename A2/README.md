# 上机作业 A2：SPECjvm2008 基准评测

学号：10245102410

姓名：吴博闻

## 系统信息

| 系统信息 | 配置 |
|---|---|
| 操作系统 | Ubuntu 24.04.2 LTS，WSL2；Linux 6.18.33.2-microsoft-standard-WSL2，x86_64 |
| CPU | Intel Core Ultra 9 185H；WSL2 中可用 22 个逻辑处理器 |
| 内存 | WSL2 中显示 15.42 GiB；Swap 4 GiB |

## 1. SPECjvm2008 的用途与测试类别

SPEC（Standard Performance Evaluation Corporation）制定标准化性能基准。SPECjvm2008 衡量 Java 运行环境执行单个应用时的性能，也反映 CPU、内存和操作系统的影响；它对文件 I/O 的依赖较低，不包含跨机器网络 I/O。成绩以每分钟完成的操作数（ops/m）表示。[官网](https://www.spec.org/jvm2008/)、[FAQ](https://www.spec.org/jvm2008/docs/FAQ.html)

| Workload | 主要工作与特点 |
|---|---|
| compiler | 用套件自带的 javac 编译编译器自身和 Sunflow 源码，尽量减少文件 I/O 的影响 |
| compress | 对真实文件数据进行 LZW 压缩和解压，包含字符串查找和位操作 |
| crypto | 对称加解密、RSA 加解密及签名验证，使用 JRE 的加密实现 |
| derby | Java 数据库与 BigDecimal 运算，涉及数据库逻辑、锁和高精度计算 |
| mpegaudio | 用 JLayer 解码 MP3，浮点运算较多 |
| scimark | FFT、LU、SOR、稀疏矩阵和 Monte Carlo；大小数据集分别考察内存访问与计算表现 |
| serial | 对象序列化和反序列化，通过同机 socket 连接生产者与消费者 |
| startup | 新建 JVM 并完成一次工作负载，衡量 JVM 与应用的启动开销 |
| sunflow | 多线程全局光照渲染，每个渲染实例内部使用多个线程 |
| xml | XML 样式转换与模式校验，使用 JRE 提供的 XML API |

各项的具体定义见[官方 workload 说明](https://www.spec.org/jvm2008/docs/benchmarks/index.html)。

Base 各项采用统一的默认 JVM 配置，不允许手工调整 JVM 或规定运行时间；Peak 允许按测试项调优 JVM，并可延长运行时间。[User's Guide](https://www.spec.org/jvm2008/docs/UserGuide.html)、[Run and Reporting Rules](https://www.spec.org/jvm2008/docs/RunRules.html)

## 2. 安装、环境配置与完整 Base

SPECjvm2008 1.01（20090519）从[官方网站](https://www.spec.org/jvm2008/)下载，使用 JDK 8 安装到 `~/.local/opt/specjvm2008/`。实验选用[官方 OpenJDK 7u75 RI](https://jdk.java.net/java-se-ri/7)，位于 `~/.local/opt/java-se-7u75-ri/`。Java 21 的功能检查出现模块访问错误，JDK 8 的 compiler 启动测试也遇到兼容问题；相关限制见 [FAQ Q4.8](https://www.spec.org/jvm2008/docs/FAQ.html#Q4.8)和 [Known Issues](https://www.spec.org/jvm2008/docs/KnownIssues.html)。

`JAVA_HOME` 指向该 JDK，`PATH` 将其 `bin` 放在首位；`CLASSPATH`、`JAVA_TOOL_OPTIONS`、`_JAVA_OPTIONS` 和 `JDK_JAVA_OPTIONS` 均不设置。JDK 7 自带 FreeType 与系统 fontconfig 不兼容，运行时通过 `LD_PRELOAD` 使用系统库，使报告图像正常生成。

![JDK 与实验环境](images/04-environment.png)

```bash
export JAVA_HOME="$HOME/.local/opt/java-se-7u75-ri"
export PATH="$JAVA_HOME/bin:$PATH"
export LC_ALL=C.UTF-8
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libfreetype.so.6
unset CLASSPATH JAVA_TOOL_OPTIONS _JAVA_OPTIONS JDK_JAVA_OPTIONS
cd "$HOME/.local/opt/specjvm2008"
java -jar SPECjvm2008.jar --base
```

Base 使用默认 JVM 配置，properties 未修改。普通吞吐项目预热 120 秒、测量 240 秒。

环境搭建已完成，但 WSL2 出现计时异常，已有 Base 成绩不能用于正式性能分析。完整 Base 将在计时环境稳定后重新测量。

## 3. 总体结果与测试项分析

尚未得到可靠的总体成绩和分项成绩，不能进行数值比较。计划分析以下三个具体测试项：

| Workload | 主要特点 |
|---|---|
| compress | 对真实文件数据进行 LZW 压缩和解压，涉及字符串匹配、整数运算和数组访问 |
| derby | Java 数据库逻辑、锁与 BigDecimal 高精度计算 |
| crypto.aes | 使用 JRE 实现的 AES、DES 加解密，包含不同输入大小和加密模式 |

各项操作的定义不同，ops/m 的比例不能直接解释为同一任务的加速比。[compress](https://www.spec.org/jvm2008/docs/benchmarks/compress.html)、[derby](https://www.spec.org/jvm2008/docs/benchmarks/derby.html)、[crypto](https://www.spec.org/jvm2008/docs/benchmarks/crypto.html)

## 4. 与官方结果比较

选用 Sugon I620-G20 的记录 `jvm2008-20150120-00018`，Base 成绩为 **853.15 ops/m**。[Summary Report](https://www.spec.org/jvm2008/results/res2015q1/jvm2008-20150120-00018.html)、[Base Report](https://www.spec.org/jvm2008/results/res2015q1/jvm2008-20150120-00018.base/SPECjvm2008.base.html)

![官方 Summary Report](images/07-official-result.png)

| 配置 | 官方记录 | 本机 |
|---|---|---|
| 操作系统 | Red Hat Enterprise Linux 6.5，64 位 | Ubuntu 24.04.2 LTS / WSL2 |
| CPU | 2 × Xeon E5-2660 v3，20 核、40 逻辑处理器，2.60 GHz | Core Ultra 9 185H，WSL2 中 22 个逻辑处理器 |
| 内存 | 256 GB，16 × 16 GB DDR4-2133 | WSL2 中 15.42 GiB |
| JDK/JVM | Red Hat OpenJDK 1.7.0_45，64-Bit Server VM 24.45-b08 | OpenJDK 1.7.0_75 RI，64-Bit Server VM 24.75-b04 |
| Base 总体结果 | 853.15 ops/m | 尚无可靠成绩 |

两台机器的处理器、内存、JVM 和操作系统均不同，后续比较应考虑软硬件的共同影响。目前不能计算本机与官方结果的性能差距。

## 5. 单项三次独立运行

选择 compress，保持 JDK、环境变量、线程数和预热/测量时间一致，每次新建 JVM：

```bash
java -jar SPECjvm2008.jar compress
```

旧三次结果受时钟异常影响，不能用于计算正式均值和波动范围；三次测量将在计时环境稳定后重新完成。即使计时正常，JIT 编译、垃圾回收、操作系统调度和缓存状态也可能造成运行间差异，WSL2 还与宿主共享资源。

## 6. 运行体会与问题处理

全套短测先暴露了兼容问题。JDK 8 的 startup.compiler.sunflow 因套件未读取子进程的大量 stderr 而阻塞，改用 Java 7 后启动测试正常；报告字体库冲突则通过预加载系统 FreeType 解决。只看退出码容易漏掉报告错误，因为字体故障时 Java 进程仍返回了 0。

时钟问题说明，计算结果正确并不代表性能计时可靠。更换运行时 clocksource 后异常仍未消除，需要先在稳定环境中重新测量，再比较重复运行的波动和参数变化；单次小幅变化不足以证明优化有效。

## 7. 修改一个 JVM 参数

固定选择 **`-XX:+UseSerialGC`**，比较默认收集器与 Serial GC，其他实验条件保持一致：

```bash
java -XX:+UseSerialGC -jar SPECjvm2008.jar compress
```

Serial GC 改变垃圾回收的并行程度和线程协调开销，可能影响创建对象和数组的 compress 工作负载。[Java 7 GC Ergonomics](https://docs.oracle.com/javase/7/docs/technotes/guides/vm/gc-ergonomics.html)

两组三次测量将在计时环境稳定后重新完成。旧数据不用于正式性能结论，因此目前不能给出均值变化百分比，也不能判断该参数是否改善性能。
