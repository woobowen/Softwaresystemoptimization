# README 数值来源映射

状态：映射已核对，性能数据仍是旧结果；时钟风险未解除。若重跑，必须同步更新此表、README 和截图。数值可追溯不等于测量可信度通过。路径相对 A2。

| 内容 | 值 | source file / field |
|---|---|---|
| 身份 | 10245102410 / 吴博闻 | 用户给定项目身份要求 |
| OS / kernel / arch | Ubuntu 24.04.2 LTS / 6.18.33.2-microsoft-standard-WSL2 / x86_64 | evidence/environment/formal-environment.json → commands: os-release、uname -srmo |
| CPU / threads | Intel Core Ultra 9 185H / 22 | 同文件 lscpu -J → Model name / CPU(s)；raw numberBmThreads=22 |
| memory / swap | 15.42 GiB / 4 GiB | 同文件 free -b → Mem=16561393664 / Swap=4294967296 bytes，除以 2^30 |
| SPEC version / build | 1.01 / 20090519 | 同文件 spec_version；evidence/environment/spec-installed.txt |
| JDK / VM | 1.7.0_75 RI / 24.75-b04 | evidence/environment/formal-environment.txt；raw jvm-info version |
| Java 21 / JDK 8 兼容历史 | 21 / 8 | evidence/compatibility/java21-preflight/console.log；jdk8-startup-sunflow-threads.txt、stderr.txt |
| JAVA_HOME / PATH / unset | java-se-7u75-ri，bin 在前；CLASSPATH 和三个 JVM 选项变量 null | evidence/environment/formal-environment.json → environment；七个 run.json |
| LD_PRELOAD | /usr/lib/x86_64-linux-gnu/libfreetype.so.6 | 各 run.json → environment.LD_PRELOAD；Base process-observations.jsonl 实际映射 |
| warmup / measurement / threads | 120 / 240 s / 22 | 各 raw compress configuration；expectedDuration=120000/240000 |
| Base overall | 482.49 ops/m | A2/results/base/SPECjvm2008.006/SPECjvm2008.006.raw → 子项最好 iteration → 组几何平均 → 全组几何平均；TXT Composite result |
| local date | 2026-10-01 | A2/results/base/SPECjvm2008.006/SPECjvm2008.006.raw → run-info/spec.jvm2008.report.run.date |
| official ID / publish date | jvm2008-20150120-00018 / 2015-02-23 | 官方 Summary Report；evidence/environment/official-result.json 与 official-recheck-stage4.json |
| official score | 853.15 ops/m | 官方 Summary/Base Report → Base result / Composite result；README 的两个直接 URL |
| official machine | Sugon I620-G20；2×Xeon E5-2660 v3；20 cores / 40 logical CPUs；2.60 GHz | 官方 Summary/Base Report → Hardware Model / Chips / Cores / Logical CPUs / MHz |
| official memory | 256 GB / 16×16 GB DDR4-2133 | 官方 Base Report → Memory / Memory Details |
| official OS / JVM / date | RHEL 6.5 64-bit / 1.7.0_45 / 24.45-b08 / 2014-12-25 | 官方 Base Report → OS / JVM / Test date |
| parameter | -XX:+UseSerialGC | evidence/parameter/parameter-{1,2,3}/run.json → command；process-observation.json → cmdline |
| collector and heap defaults | UseParallelGC=true → UseSerialGC=true；独立检查的堆默认值相同 | default-flags.json / modified-flags.json → selected_flags；InitialHeapSize=258771776 / MaxHeapSize=4141875200 bytes；不是测量 PID 的实时 heap |
| native command field | n/a | 各 raw → jvm-info/spec.jvm2008.report.jvm.command.line；未修改 |
| Base compress | 361.27 ops/m | A2/results/base/SPECjvm2008.006/SPECjvm2008.006.raw → benchmark-result name=compress / iterations：operations=1445.0898764644649，elapsed=240000 ms |
| Base derby | 362.70 ops/m | A2/results/base/SPECjvm2008.006/SPECjvm2008.006.raw → benchmark-result name=derby / iterations：operations=1450.8075665626218，elapsed=240000 ms |
| Base crypto.aes | 184.65 ops/m | A2/results/base/SPECjvm2008.006/SPECjvm2008.006.raw → benchmark-result name=crypto.aes / iterations：operations=738.6016929670345，elapsed=240000 ms |
| repeat SPECjvm2008.007 | 801.24 ops/m | /home/addaswsw/lab/Software_system_optimization/A2/results/repeat/SPECjvm2008.007/SPECjvm2008.007.raw → compress/iterations operations=3204.9457923743635；×60000/240000 |
| repeat SPECjvm2008.008 | 787.96 ops/m | /home/addaswsw/lab/Software_system_optimization/A2/results/repeat/SPECjvm2008.008/SPECjvm2008.008.raw → compress/iterations operations=3151.8509983379604；×60000/240000 |
| repeat SPECjvm2008.009 | 812.58 ops/m | /home/addaswsw/lab/Software_system_optimization/A2/results/repeat/SPECjvm2008.009/SPECjvm2008.009.raw → compress/iterations operations=3250.3298662377665；×60000/240000 |
| repeat mean | 800.59 | scripts/summarize-spec.py 对 results/repeat 未舍入数计算；evidence/final/experiment-comparison.json |
| repeat min | 787.96 | scripts/summarize-spec.py 对 results/repeat 未舍入数计算；evidence/final/experiment-comparison.json |
| repeat max | 812.58 | scripts/summarize-spec.py 对 results/repeat 未舍入数计算；evidence/final/experiment-comparison.json |
| repeat range | 24.62 | scripts/summarize-spec.py 对 results/repeat 未舍入数计算；evidence/final/experiment-comparison.json |
| repeat relative_range_percent | 3.08 | scripts/summarize-spec.py 对 results/repeat 未舍入数计算；evidence/final/experiment-comparison.json |
| parameter SPECjvm2008.011 | 800.08 ops/m | /home/addaswsw/lab/Software_system_optimization/A2/results/parameter/SPECjvm2008.011/SPECjvm2008.011.raw → compress/iterations operations=3200.319708847233；×60000/240000 |
| parameter SPECjvm2008.012 | 804.42 ops/m | /home/addaswsw/lab/Software_system_optimization/A2/results/parameter/SPECjvm2008.012/SPECjvm2008.012.raw → compress/iterations operations=3217.662311895002；×60000/240000 |
| parameter SPECjvm2008.013 | 806.48 ops/m | /home/addaswsw/lab/Software_system_optimization/A2/results/parameter/SPECjvm2008.013/SPECjvm2008.013.raw → compress/iterations operations=3225.929600735713；×60000/240000 |
| parameter mean | 803.66 | scripts/summarize-spec.py 对 results/parameter 未舍入数计算；evidence/final/experiment-comparison.json |
| parameter min | 800.08 | scripts/summarize-spec.py 对 results/parameter 未舍入数计算；evidence/final/experiment-comparison.json |
| parameter max | 806.48 | scripts/summarize-spec.py 对 results/parameter 未舍入数计算；evidence/final/experiment-comparison.json |
| parameter range | 6.40 | scripts/summarize-spec.py 对 results/parameter 未舍入数计算；evidence/final/experiment-comparison.json |
| parameter relative_range_percent | 0.80 | scripts/summarize-spec.py 对 results/parameter 未舍入数计算；evidence/final/experiment-comparison.json |
| mean change | +0.38% | (803.659301789829/800.5938880791742−1)×100 = 0.3828924697401037%；parser --compare |

十类 workload 定义与 Base/Peak 规则见 README 逐段链接的 SPEC 官方文档。当前限制见 [计时结论](../conclusion.md)。
