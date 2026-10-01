# 内部工具与历史探针入口

这些工具用于追溯已有实验和检查脚本。当前发布阶段不执行 clock probe、clock monitor、SPEC 或系统诊断；下一步环境方案待 GitHub 文件级检查后决定。

## Python / Java timing probe

| 已有输出 | 对应 Python 源码 | Java 源码 | 说明 |
|---|---|---|---|
| [tsc samples](../timing/probe-10min/samples.jsonl) / [summary](../timing/probe-10min/summary.json) | [原 clock-probe.py](../timing/probe-10min/clock-probe.py) | [原 ClockProbe.java](../timing/probe-10min/ClockProbe.java) | 原始版本保留，与后来 Hyper-V 版区分 |
| [gate-1](../timing/gate-1/summary.json)、[gate-2](../timing/gate-2/summary.json) | [clock-probe.py](clock-probe.py) | [ClockProbe.java](ClockProbe.java) | 增加 clocksource、interval、累计差和 gate 字段 |

以下命令按现有源码路径重建历史调用方式，只作复现说明，本次未执行。每次必须使用不存在的输出目录；JDK 路径可由 `--jdk` 显式提供。Python 使用标准库，Java 只需要该 JDK 的 `javac` 和 `java`，不依赖 SPEC 安装目录或本地隐藏辅助源码。

```bash
python3 -B A2/evidence/timing/probe-10min/clock-probe.py /tmp/a2-tsc-replay --seconds 600 --jdk /path/to/jdk
python3 -B A2/evidence/tools/clock-probe.py /tmp/a2-hyperv-replay-1 --seconds 600 --jdk /path/to/jdk
python3 -B A2/evidence/tools/clock-probe.py /tmp/a2-hyperv-replay-2 --seconds 600 --jdk /path/to/jdk
```

Python 调用 `javac -d <temporary-directory> ClockProbe.java`，再调用 `java -cp <temporary-directory> ClockProbe 600`。Java 实际 argv 保存在各自 summary 中；临时目录自动清理，`.class` 不上传。原始 shell 启动文本没有单独保存，以上不是伪造的原始 shell 日志。

Java 每秒输出 `currentTimeMillis nanoTime`；Python 收到一行后读取 `time.time()`、`time.monotonic()` 和 boottime。相邻增量差和首末累计差单位均为秒。两种时钟并非原子采样，接收缓冲、调度、float 精度及边界顺序需要结合 raw 审查，不能单凭进程退出 0 判断 timing gate 通过。Hyper-V 版 `clocksource_consistent` 只接受 `hyperv_clocksource_tsc_page`，在其他源上不能直接作为通用 gate。

[clock-monitor.py](clock-monitor.py)是旧的 15 秒轻量监视器，默认直到 SIGTERM 才写 summary；其 `timing_healthy` 同样限制 Hyper-V clocksource。本次不运行它。[collect-timing-diagnostics.py](collect-timing-diagnostics.py)保留受限 guest 日志和 host 事件元数据查询逻辑；已有输出不是 Windows event 全量导出。

## 其他工具

- [test-runner.py](test-runner.py)：临时假 Java 程序测试双日志、退出码、信号、互斥、防覆盖和启动失败，不运行 SPEC。默认会写历史 `runner-tests-stage5.json`，需要保留旧证据时应在临时副本中执行。
- [test-summarizer.py](test-summarizer.py)：通过 `--results A2/evidence/timing/invalidated-results --output <new-json>` 使用历史 timing-invalidated fixture。预期数值从 raw 字段重算，测试成功不恢复旧成绩的测量资格。
- [test-compress-regression.py](test-compress-regression.py)、[check-invalidated-experiments.py](check-invalidated-experiments.py)：历史数据回归检查；硬编码字段仅标识已 invalidated 的原始 fixture。
- [preserve-results.py](preserve-results.py)、[check-run.py](check-run.py)、[monitor-run.py](monitor-run.py)：历史结果复制、结构检查和进程观测。
- [FontProbe.java](FontProbe.java)、[read-adjtimex.c](read-adjtimex.c)、[capture-terminal.py](capture-terminal.py)：字体排错、只读时钟查询和终端截图辅助源码。
- [historical-run-three.py](historical-run-three.py)：旧实验驱动器，依赖历史冻结配置与当时 runner 哈希，仅供追溯，不作为本次或下一环境的执行入口。

旧 metadata 中的绝对路径和临时路径是当时记录；结果迁移参见 [manifest](../timing/invalidated-results/manifest.md)，工具迁移参见 [stage5-tool-moves.json](../final/stage5-tool-moves.json)。当前正式脚本目录只有 runner 和 parser。
