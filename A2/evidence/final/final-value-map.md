# 最终报告数值来源

完整路径相对 A2；未写目录前缀的测量 JSON 路径相对 evidence/formal-campaign/，official-result.json 相对 evidence/environment/。成绩保留两位小数，统计由未四舍五入的 raw 数值计算。全部正式性能数值与配置已映射；逐项核对没有不一致。

| README 内容 | 数值或状态 | 精确来源 |
|---|---|---|
| 身份 | 10245102410 / 吴博闻 | 用户提供的项目身份要求 |
| OS / kernel / 架构 | Ubuntu 24.04.2 LTS / 6.18.33.2-microsoft-standard-WSL2 / x86_64 | evidence/formal-campaign/campaign-environment.json → commands 的 /etc/os-release、lscpu；state_before_stop.kernel_release |
| CPU / 逻辑处理器 | Intel Core Ultra 9 185H / 22 | 同文件 commands → lscpu -J 的 Model name、CPU(s)；nproc |
| 内存 / Swap | 15.42 GiB / 4 GiB | 同文件 free -b → 16561393664 / 4294967296 bytes，除以 2^30 |
| SPEC 版本 / build | 1.01 / 20090519 | 同文件 spec_version；安装目录 version.txt |
| 实验 JDK / VM | OpenJDK 1.7.0_75 / 24.75-b04 | evidence/environment/stage5-environment.json 中 java -version；新 Base raw 的 jvm-info 中 version=24.75-b04 mixed mode、boot class path 指向 java-se-7u75-ri |
| Java 21 / JDK 8 兼容经历 | 21 / 8；JDK 8 安装器 -i console | evidence/compatibility/java21-preflight/、jdk8-startup-sunflow-threads.txt、decision.md；evidence/environment/installation-log.md 与 spec-install.log |
| JDK、环境变量与库 | JAVA_HOME / PATH / unset CLASSPATH 和三个 Java option 变量 / LD_PRELOAD | evidence/formal-campaign/base-1/benchmark/run.json → environment、command、proc_cmdline；其余六次保存相同字段 |
| 默认预热 / 测量 / threads | 120 / 240 s / 22 | evidence/formal-campaign/base-parsed.json → runs[0].measurements.compress.configuration；warmup/iterations.expectedDuration = 120000 / 240000 ms；单项 raw 相同 |
| Base 命令 / 总体 / workload 数 | java -jar SPECjvm2008.jar --base / 604.34 ops/m / 38 | base-1/benchmark/run.json → command；base-parsed.json → composite_ops_m = 604.3409299339644；workloads_ops_m 38 项；原生 TXT/HTML/summary/sub 同为 604.34 |
| Q3 compress | 792.54 ops/m | base-parsed.json → workloads_ops_m.compress = 792.541566625533；Base raw compress/iterations 的 operations × 60000 / (endTime−startTime) |
| Q3 derby | 1148.35 ops/m | 同字段 derby = 1148.3477284471596；同一份 Base raw 对应 iteration |
| Q3 crypto.aes | 397.00 ops/m | 同字段 crypto.aes = 397.0042943643131；同一份 Base raw 对应 iteration |
| 官方记录 / 结果 | jvm2008-20150120-00018 / 853.15 ops/m | evidence/environment/official-result.json → base_ops_m；evidence/formal-campaign/official-source-resumed-check.json 的实际 HTTP 获取与 SHA256；README 两个 SPEC 原站链接 |
| 官方 CPU / 频率 | 2 × Xeon E5-2660 v3，20 核 / 40 逻辑处理器，2.60 GHz | official-result.json → fields 的 CPU name、# of chips、# of cores、# of logical cpus、CPU frequency=2600 MHz |
| 官方内存 | 256 GB；16 × 16 GB DDR4-2133 | 同文件 fields → Memory size / Memory details |
| 官方 OS / JVM | RHEL 6.5；OpenJDK 1.7.0_45；VM 24.45-b08 | 同文件 fields → OS name、JVM version、JVM boot class path |
| 默认三次 | 667.24 / 663.45 / 711.79 ops/m | evidence/formal-campaign/repeat-statistics.json → statistics.scores = 667.2396182333354 / 663.4490414990454 / 711.793800775323；原始 results/repeat/ 中 SPECjvm2008.016、SPECjvm2008.017、SPECjvm2008.018 的 .raw → compress iteration |
| 默认均值 / 最小 / 最大 | 680.83 / 663.45 / 711.79 ops/m | repeat-statistics.json → statistics.mean = 680.8274868359013；min / max |
| 默认极差 / 相对极差 | 48.34 ops/m / 7.10% | 同文件 range = 48.344759276277614；relative_range_percent = 7.100882413099469 |
| 独立运行间隔 | 约 1 分钟 | run-formal-campaign.py 在每次检查和复制完成后等待 60 s；相邻 benchmark/run.json 的起止时间及最终数据检查记录实际区间 |
| 唯一改变参数 | -XX:+UseSerialGC | 三次 parameter-*/benchmark/run.json → command 与 proc_cmdline；gc-flags/summary.json 为独立 diagnostic JVM 的 flag 检查，不是正式进程的实时 flag 读取 |
| 计时条件 | WSL2 / tsc / 测量期间 timesyncd inactive | evidence/formal-campaign/timesync-stop.json；final-gate/timing-review.json；逐次 run.json、monitor samples 与 timing-review.json |
| Serial 三次 | 698.80 / 728.66 / 737.95 ops/m | evidence/formal-campaign/final-statistics.json → modified.statistics.scores = 698.7995745066894 / 728.6564481714678 / 737.9519700738621；results/parameter/ 的 SPECjvm2008.019、.020、.021 原始 compress iteration |
| Serial 均值 / 最小 / 最大 | 721.80 / 698.80 / 737.95 ops/m | 同文件 modified.statistics.mean = 721.802664250673；min / max |
| Serial 极差 / 相对极差 | 39.15 ops/m / 5.42% | 同文件 modified.statistics.range = 39.152395567172675；relative_range_percent = 5.424252016001916 |
| 均值变化 | +6.02% | 同文件 percentage_change = 6.018437593523296；(721.802664250673 / 680.8274868359013 − 1) × 100 |
| 测量后恢复 | active / enabled；持久配置无变化 | evidence/formal-campaign/restore.json → state、checks 全部 true；clocksource、boot ID、内核、Linux/WSL 配置哈希、Windows 时间服务、电源方案与开始前一致 |

新 Base 原始文件：[SPECjvm2008.015.raw](../../results/base/SPECjvm2008.015/SPECjvm2008.015.raw)。旧成绩继续仅保存在 [invalidated-results](../timing/invalidated-results/manifest.md)，未用于上述计算。
