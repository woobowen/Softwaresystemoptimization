# 运行索引

第四阶段状态：旧七份结果的配置、解析和文件完整性已核对，但发现影响计分的时钟风险，尚无可信 final Base。下方第三阶段“正式实验”表是历史记录，不能作为测量可信度通过。见 [计时结论](../conclusion.md) 与 [compress 调查](../../compress-investigation/conclusion.md)。

SPEC 许可与 JDK 7 路径均已由用户确认。诊断结果不参与正式统计。以下原有 Java 21 / JDK 8 记录保留；第三阶段完整 Base、三次原配置与三次修改配置均已完成；各次元数据见对应目录的 `run.json`。

## JAVA21-COMPAT（诊断，不计入正式实验）

- command: `/usr/lib/jvm/java-21-openjdk-amd64/bin/java -jar SPECjvm2008.jar -wt 5s -it 5s -bt 2 compiler.compiler compiler.sunflow xml.transform xml.validation`
- cwd: `/home/addaswsw/.local/opt/specjvm2008`
- JDK: `/usr/lib/jvm/java-21-openjdk-amd64`
- start: 2026-09-30T15:47:27+08:00
- end: 2026-09-30T15:47:36+08:00
- exit: 0
- PID: 10691
- original result: `/home/addaswsw/.local/opt/specjvm2008/results/SPECjvm2008.001`
- preserved result: `compatibility/java21-preflight/native-results/`
- metadata: `compatibility/java21-preflight/run.json`

Java 21：checksum 通过，check 因模块访问错误失败，尽管退出码为 0。完整输出见 `compatibility/java21-preflight/console.log`。

## JDK8-DIAGNOSTIC（诊断，不计入正式实验）

- command: `/home/addaswsw/.local/opt/java-se-8u41-ri/bin/java -jar SPECjvm2008.jar -wt 5s -it 5s -bt 2`
- cwd: `/home/addaswsw/.local/opt/specjvm2008`
- JDK: `/home/addaswsw/.local/opt/java-se-8u41-ri`
- start: 2026-09-30T15:48:34+08:00
- end: 2026-09-30T15:55:35+08:00
- exit: 0
- PID: 11051
- original result: `/home/addaswsw/.local/opt/specjvm2008/results/SPECjvm2008.002`
- preserved result: `compatibility/jdk8-preflight/native-results/`
- metadata: `compatibility/jdk8-preflight/run.json`

JDK 8：startup.compiler.sunflow 的 stderr 写满；通过诊断性读取管道解除阻塞后完成全套短跑。所有数值均排除出性能分析。完整 console 经无损压缩为 `compatibility/jdk8-preflight/console.log.gz`；可读摘要为 `console-excerpt.log`。

## 第三阶段诊断

| 记录 | JDK / 命令参数 | 结果 | 元数据 |
|---|---|---|---|
| runner 输出与信号测试 | 本地测试程序；stdout/stderr 各 307212 bytes | 输出完整；正常/非零退出与信号转发符合预期 | runner/test-results.json |
| runner SPEC smoke | JDK 8；`-jar SPECjvm2008.jar -wt 1s -it 1s -bt 2 compress` | 计算与报告成功，仅诊断 | runner/spec-smoke-jdk8/run.json |
| JDK 7 全套预检 1 | `-jar SPECjvm2008.jar -wt 5s -it 5s` | 38 项计算结束；字体库冲突造成报告图片失败 | compatibility/jdk7-preflight/run.json |
| JDK 7 全套预检 2 | 同上；进程级预加载系统 FreeType | 38 项、checksum、correctness、报告及 79 张原生图片通过 | compatibility/jdk7-preflight-fixed/run.json |

字体问题的动态加载器证据、最小绘图程序和修复见 `compatibility/font-probe/`。SPEC 内部 startup 管道问题与 Python runner 分开说明，见 `runner/review.md`。

## 正式实验（全部完成）

日期均为 2026-10-01，时区 +08:00。每行对应一次独立 JVM；完整 Base 不计入单项统计。`wall_seconds` 是 runner 历史字段名，实际使用 CLOCK_MONOTONIC，因此同时列出起止日期时间。

| ID | PID | start | end | 单调时钟秒数 | exit | Score（ops/m） | 完整原生目录 | 元数据 |
|---|---:|---|---|---:|---:|---:|---|---|
| BASE-1 | 16566 | 00:34:37 | 02:54:41 | 7933.371 | 0 | 482.49 | [../results/base/SPECjvm2008.006/](../invalidated-results/base/SPECjvm2008.006/) | [base/base-1/run.json](../../base/base-1/run.json) |
| REPEAT-1 | 57549 | 02:56:22 | 03:02:59 | 374.153 | 0 | 801.24 | [../results/repeat/SPECjvm2008.007/](../invalidated-results/repeat/SPECjvm2008.007/) | [repeat/repeat-1/run.json](../../repeat/repeat-1/run.json) |
| REPEAT-2 | 58638 | 03:02:59 | 03:09:43 | 375.866 | 0 | 787.96 | [../results/repeat/SPECjvm2008.008/](../invalidated-results/repeat/SPECjvm2008.008/) | [repeat/repeat-2/run.json](../../repeat/repeat-2/run.json) |
| REPEAT-3 | 59662 | 03:09:43 | 03:16:27 | 376.291 | 0 | 812.58 | [../results/repeat/SPECjvm2008.009/](../invalidated-results/repeat/SPECjvm2008.009/) | [repeat/repeat-3/run.json](../../repeat/repeat-3/run.json) |
| PARAMETER-1 | 61762 | 03:22:34 | 03:29:15 | 374.342 | 0 | 800.08 | [../results/parameter/SPECjvm2008.011/](../invalidated-results/parameter/SPECjvm2008.011/) | [parameter/parameter-1/run.json](../../parameter/parameter-1/run.json) |
| PARAMETER-2 | 62879 | 03:29:15 | 03:36:03 | 375.693 | 0 | 804.42 | [../results/parameter/SPECjvm2008.012/](../invalidated-results/parameter/SPECjvm2008.012/) | [parameter/parameter-2/run.json](../../parameter/parameter-2/run.json) |
| PARAMETER-3 | 63833 | 03:36:03 | 03:42:41 | 375.343 | 0 | 806.48 | [../results/parameter/SPECjvm2008.013/](../invalidated-results/parameter/SPECjvm2008.013/) | [parameter/parameter-3/run.json](../../parameter/parameter-3/run.json) |

三种启动命令均在 `/home/addaswsw/.local/opt/specjvm2008` 执行：

```text
/home/addaswsw/.local/opt/java-se-7u75-ri/bin/java -jar SPECjvm2008.jar --base
/home/addaswsw/.local/opt/java-se-7u75-ri/bin/java -jar SPECjvm2008.jar compress
/home/addaswsw/.local/opt/java-se-7u75-ri/bin/java -XX:+UseSerialGC -jar SPECjvm2008.jar compress
```

正式 JDK 冻结为 OpenJDK 7u75 RI（24.75-b04），进程环境见 [environment/formal-environment.json](../../environment/formal-environment.json)。全部正式运行使用同一个 runner、JDK、系统 FreeType 兼容设置；properties 未改动，Base 没有 JVM 性能参数。Java 21 和 JDK 8 安装保留，未修改全局 Java 选择。

Base 覆盖全部 38 个计分 workload，checksum、correctness 通过；原生报告为 `Run is compliant`，没有 violations。84 个原生文件全部复制，79 张 JPEG 可读，77 处 HTML 资源链接存在。Base 起止日期时间相差 8404 秒，单调时钟为 7933.371 秒，见 [base/base-1/assessment.json](../../base/base-1/assessment.json)。

compress 的六次单项均为 22 个基准线程、120 秒预热 / 240 秒测量，exit 0，checksum/correctness 通过。每次有 10 个原生文件、5 张 JPEG 和 3 处 HTML 资源链接。原配置均值 800.59、极差 24.62（3.08%）；修改后均值 803.66、极差 6.40（0.80%）；均值增加 0.38%，不足以认定明显提升。完整数据与条件一致性见 [final/experiment-comparison.json](experiment-comparison.json)；统计见 [repeat/statistics.json](../../repeat/statistics.json) 和 [parameter/comparison.json](../../parameter/comparison.json)。

参数只增加 `-XX:+UseSerialGC`。选择前读取实际默认 flags，修改后核对 flags；所有修改配置还在运行时采集 `/proc` argv、exe、environment。正式三次之前的 5/5 秒 smoke（SPECjvm2008.010）仅保存在 [parameter/smoke/](../../parameter/smoke/)，不参与成绩；完整时间与命令见其 run.json。

六次单项原生状态都是 `Run is valid, but not compliant`，唯一报告的违规项是未构成完整套件的发表顺序。未启用自动参数采集 `-pja`，原生 JVM command line 字段为 `n/a`，类别均沿用 `SPECjvm2008 Base`；没有修改这些原生字段。修改配置的身份依据实际 argv、PrintFlagsFinal 和 `/proc` 记录，不将它称作完整默认 Base。详见 [parameter/metadata-note.md](../../parameter/metadata-note.md)。

七次正式结果共 144 个文件、109 张 JPEG、95 处 HTML 资源链接；来源与副本逐文件 SHA256 一致。任务结束时再次检查套件 777 个原始文件与 JDK 关键文件未改动，见 [final/hygiene-check.json](hygiene-check.json)。

WSL2 中 CLOCK_REALTIME 与 CLOCK_MONOTONIC 的经过时间存在差异，原始分数和两种计时均保留，未校正或重新归一化。此现象限制性能解释；原生 compliant 不代表通过 SPEC 官方发表审核。见 [environment/timekeeping-analysis.md](../../environment/timekeeping-analysis.md)。

## 第四阶段诊断

- 时钟探针：Java 7 与 Python，601 个样本，约 600.378 s 单调时间对应 650.366 s wall 时间，差约 49.988 s；[记录](../probe-10min/summary.json)。
- `.014`：独立 compress，22 线程，120/240 s，799.004529 ops/m；wall 400.059095 s、monotonic 374.719365 s。仅诊断，不计入第 5/7 题。完整原生报告见 [目录](../invalidated-results/diagnostic/SPECjvm2008.014/)，[命令和环境](../../compress-investigation/standalone-diagnostic/run.json)。
- replacement Base 与新的 3+3 尚未启动；时钟源变更尚待用户授权。没有 stage/commit/push。
