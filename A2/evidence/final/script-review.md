# 第五阶段脚本检查

连续阅读了最终 `scripts/run-spec.py` 与 `scripts/summarize-spec.py`。

- runner 只新增读取 Linux clocksource 的小函数，在 Popen 前和 wait 后记录 start/end；现有双时钟、argv、白名单环境、PID、退出码、结果路径、日志文件、互斥及防覆盖逻辑保留。六个执行场景覆盖正常输出、非零退出、SIGINT/SIGTERM、并发拒绝、防覆盖及启动失败；见 [runner-tests-stage5.json](runner-tests-stage5.json)。
- parser 未修改生产代码。使用真实但 timing-invalidated 的原生 fixture 运行 15 个用例，检查独立 raw/目录、全套 38 项、group/child/startup、重复输入/重复 workload、correctness、缺字段、非正分数、warmup 排除、单位、TXT 缺字段，以及两组均值、极差、百分比的直接 XML 复算。见 [测试记录](parser-tests-invalidated-fixtures-stage5.json)。这只证明解析行为；没有新正式 raw，不能声称完成了新结果验证。
- clock probe 的 Java 源与旧阶段逐字节一致。Python 保留接收同一 Java 1 秒样本时采集 wall/monotonic 的方式，补充 clocksource、interval、累计量和内部阈值。两组独立整数纳秒复算与汇总一致。
- clock monitor 每 15 秒只读取两种时间与 clocksource，SIGTERM 写最后一条样本后正常退出；短自检 CPU 时间分别约 0.000981 与 0.000705 s，未运行中采集其他指标。没有正式 benchmark，不能把自检当成运行期间 timing health。
- 内部工具集中到 `evidence/tools/`，历史三次驱动器和配置检查器的名称明确标识旧实验，正式 `scripts/` 仍只有两个 Python 文件。旧 parser fixture 的硬编码原始字段仅用于标明已作废的历史回归。

保留了直白的控制流，没有新增正式实验框架，也没有为了提高分数调整 Java 或 SPEC 参数。以上为本地代码检查记录，不是最终工程验收。
