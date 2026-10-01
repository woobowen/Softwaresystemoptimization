# 报告数值来源：尚无可采用的本机性能成绩

所有旧性能分数已从 A2/README.md 移除。下表只映射报告保留的身份、配置和官方资料；不授予性能测量通过。路径相对 A2。

| README 内容 | 数值或状态 | 精确来源 |
|---|---|---|
| 身份 | 10245102410 / 吴博闻 | 用户提供的项目身份要求 |
| OS / kernel | Ubuntu 24.04.2 LTS / 6.18.33.2-microsoft-standard-WSL2 | evidence/environment/stage5-environment.json → cat /etc/os-release、uname -srmo |
| CPU / 逻辑处理器 | Core Ultra 9 185H / 22 | 同文件 lscpu -J → Model name / CPU(s)；nproc |
| 内存 / Swap | 15.42 GiB / 4 GiB | 同文件 free -b → 16561393664 / 4294967296 bytes，除以 2^30 后显示两位小数 |
| SPEC 版本 / build | 1.01 / 20090519 | 同文件 spec_version；未修改安装目录 version.txt |
| 实验 JDK / VM | OpenJDK 1.7.0_75 / 24.75-b04 | 同文件绝对路径 java -version、javac -version |
| Java 21 / JDK 8 兼容经历 | 21 / 8 | evidence/compatibility/java21-preflight/；jdk8-startup-sunflow-threads.txt；decision.md |
| JDK 选择与环境变量 | JAVA_HOME、PATH、unset CLASSPATH 和三个 JVM 选项变量 | README 明示的命令；原实验环境 evidence/environment/formal-environment.json。第五阶段探针直接调用 JDK 7 绝对路径，未启动新 benchmark |
| FreeType | /usr/lib/x86_64-linux-gnu/libfreetype.so.6 | evidence/compatibility/font-probe/；历史 run.json 中 LD_PRELOAD 与进程映射 |
| 默认预热 / 测量 | 120 / 240 s | SPEC 官方 UserGuide.html §1.6–1.7；安装目录 props/specjvm.properties 的 Base 允许值。仅为运行配置，不是新的测量成绩 |
| 计时限制 | WSL2 计时异常，旧成绩不用于正式性能分析 | evidence/timing/probe-10min/、gate-1/、gate-2/ 的 raw samples 与 summary；clocksource-restored.txt。具体切换与探针数据集中在内部 checkpoint，README 仅简述限制 |
| 官方记录 ID | jvm2008-20150120-00018 | README 两个 SPEC 官方直接链接；evidence/environment/official-recheck-stage5.json |
| 官方成绩 | 853.15 ops/m | 官方 Summary → Base result；Base → Composite result；evidence/environment/official-result.json → base_ops_m |
| 官方 CPU / 频率 | 2 × Xeon E5-2660 v3；20 cores / 40 logical CPUs；2.60 GHz | official-result.json → fields 中 CPU name、# of chips、# of cores、# of logical cpus、CPU frequency=2600 MHz |
| 官方内存 | 256 GB；16 × 16 GB DDR4-2133 | 同文件 fields → Memory size / Memory details |
| 官方 OS / JVM | RHEL 6.5；JDK 1.7.0_45；VM 24.45-b08 | 同文件 fields → OS name、JVM boot class path 中版本目录、JVM version |
| 唯一待比较参数 | -XX:+UseSerialGC | 当前任务固定要求；README 第 7 题仅给出命令，没有新参数实验成绩 |
| Base / 三个分项 / 新 3+3 / 均值 / 极差 / 百分比 | 无 | Timing Gate 未通过，没有正式 raw。不得用 invalidated-results 代替 |

旧版映射保留在 [invalidated-derived/final-value-map.md](../timing/invalidated-derived/final-value-map.md)，仅用于历史追溯。
