# 内部工具与历史探针入口

这些工具用于内部计时诊断、正式测量的外围证据记录和追溯已有实验。历史 probe 和 raw 保留原样。本次准备工作与实际执行状态见 [formal-campaign](../formal-campaign/)。

## 本次正式测量入口

- [run-formal-campaign.py](run-formal-campaign.py)：检查同步前置条件，临时停止 timesyncd，settling 75 秒，复用 1800 秒 Host-reference Gate；通过后依次调用 Base、compress 三次及 Serial GC 三次。每次先检查计时，再检查 SPEC 正确性、复制完整原生结果。`finally` 恢复 timesyncd，保存配置对照；遇到错误停止驱动，供检查后决定是否按授权上限重试。
- [compare-host-current-time.ps1](compare-host-current-time.ps1)：六次直接比较 Windows UTC 与 Linux CLOCK_REALTIME，同时记录 Host Stopwatch 调用时间、midpoint 偏差和调用不确定性。NTP offset 只作背景；是否继续由直接对齐观察及后续停止 timesyncd 的 elapsed-time Gate 决定。
- [run-host-formal.ps1](run-host-formal.ps1)：复用已测 wrapper 的 Stopwatch 和临时防休眠方式，包围单次 Linux launcher。它属于证据层，未将 Windows 逻辑加入 runner。
- [measure-formal-run.py](measure-formal-run.py)：启动 15 秒采样 monitor，调用正式 shell launcher，再结束 monitor。信号和异常均有清理路径。
- [review-formal-timing.py](review-formal-timing.py)：读取实际 host ticks、guest raw samples，检查 elapsed、step、clocksource、boot ID、服务状态及 Windows sleep/resume 事件。`REVIEW_REQUIRED` 表示需要检查边界或异常，不自动把临界差值判为真实时间故障。

正式环境入口为 [run-formal.sh](../../scripts/run-formal.sh)，仅设置 JDK、SPEC、locale 和 FreeType，并清除 Java option 环境变量后调用 runner。运行前需要完整同步/停止/计时门控条件；直接执行 launcher 不代表计时可靠。

## Windows Host Stopwatch 联合探针

- [run-host-reference-gate.ps1](run-host-reference-gate.ps1)：在 Windows 上用 Stopwatch 完整包围一次 WSL 调用，输出 host JSON；也支持 sleep、空调用和退出码边界检查。
- [host-reference-probe.py](host-reference-probe.py)、[HostReferenceClock.java](HostReferenceClock.java)：约 1 Hz 读取四种 Linux clocks 和 Java 7 两种 clocks，以 monotonic 控制采样时长。
- [capture-isolation-state.py](capture-isolation-state.py)：读取环境、服务状态、配置 SHA256 和 `adjtimex(modes=0)`。服务 inactive 时跳过 `timedatectl timesync-status/show-timesync`，避免 D-Bus 查询重新启动服务；该准备阶段问题与修复保存在 [cause-and-fix.json](../formal-campaign/preparation/service-query-activation/cause-and-fix.json)。
- [recalculate-host-reference.py](recalculate-host-reference.py)：从 raw samples 和 host ticks 独立复算，不启动 probe 或修改服务。

测量边界、运行记录及结果均见 [timesyncd-isolation](../timing/timesyncd-isolation/README.md)。这些工具不自动停止或恢复 timesyncd；对应操作保存在该目录的 `stop.json`、`start-control.json` 和 `restore.json`。

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

[clock-monitor.py](clock-monitor.py)沿用 15 秒轻量监视器，增加 raw、boottime、boot ID 和样本序号；默认期待 `tsc`，支持显式指定历史 clocksource。SIGTERM 会追加末尾样本并写 summary。[collect-timing-diagnostics.py](collect-timing-diagnostics.py)保留受限 guest 日志和 host 事件元数据查询逻辑；已有输出不是 Windows event 全量导出。

## GitHub 文件与页面检查

[verify-github-files.py](verify-github-files.py)实际下载指定提交的 README、脚本、证据和全部原生结果资源，比对 SHA256 与链接；[verify-github-readme.cjs](verify-github-readme.cjs)使用本机已有缓存中的 Playwright/Chromium，检查 GitHub 原生渲染、七题、表格和六张图片。两者从仓库根运行，参数均为 `<commit-sha> <output-dir>`；浏览器工具保留本机已用的缓存路径，不安装依赖。

## 其他工具

- [test-runner.py](test-runner.py)：临时假 Java 程序测试双日志、退出码、信号、互斥、防覆盖和启动失败，不运行 SPEC。可将新输出 JSON 路径作为第一个参数，避免覆盖历史测试。
- [test-summarizer.py](test-summarizer.py)：通过 `--results A2/results --output <new-json>` 检查最终结果，覆盖 38 个 workload、group/startup 分离、报告一致性和 3+3 统计。也可显式指定历史 fixture；历史测试成功不恢复旧成绩的测量资格。
- [audit-final-campaign.py](audit-final-campaign.py)：仅在七次测量完成且服务恢复后运行，交叉检查新 JVM、配置、argv、运行间隔、完整副本及计时边界，生成最终统计和八行计时表。
- [show-final-results.py](show-final-results.py)：调用正式 parser，再将选定字段显示于真实终端，供截图；不含固定成绩。
- [test-compress-regression.py](test-compress-regression.py)、[check-invalidated-experiments.py](check-invalidated-experiments.py)：历史数据回归检查；硬编码字段仅标识已 invalidated 的原始 fixture。
- [preserve-results.py](preserve-results.py)、[check-run.py](check-run.py)：完整原生结果复制、逐文件 SHA256、HTML 资源、正确性和默认运行配置检查；[monitor-run.py](monitor-run.py)保留历史进程观测入口。
- [FontProbe.java](FontProbe.java)、[read-adjtimex.c](read-adjtimex.c)、[capture-terminal.py](capture-terminal.py)：字体排错、只读时钟查询和终端截图辅助源码。
- [historical-run-three.py](historical-run-three.py)：旧实验驱动器，依赖历史冻结配置与当时 runner 哈希，仅供追溯，不作为本次或下一环境的执行入口。

旧 metadata 中的绝对路径和临时路径是当时记录；结果迁移参见 [manifest](../timing/invalidated-results/manifest.md)，工具迁移参见 [stage5-tool-moves.json](../final/stage5-tool-moves.json)。正式脚本目录为 runner、parser 和简单 shell launcher。
