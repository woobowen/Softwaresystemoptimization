# 本次 WSL2 计时观察

本页为第三阶段记录。第四阶段已复现进入计分机制的时钟跳变，不能继续仅以“比较精度限制”处理。最新结论为 [C：需稳定环境后重测](../timing/conclusion.md)。

`clock-observation.json` 中同一次等待，CLOCK_MONOTONIC 增加约 30.00057 秒，CLOCK_REALTIME 增加约 32.21427 秒。完整 Base 的日期时间差为 8404 秒，runner 的单调时钟差为 7933.371 秒。原始观测和系统时间服务状态分别保留在 `clock-samples.jsonl`、`timekeeping.txt`。

runner 的 `start` / `end` 使用系统日期时间；历史字段名 `wall_seconds` 实际由 `time.monotonic()` 得出。最终报告区分二者，不把这两个数写成同一种计时。

已实际阅读未修改的 SPEC 源码：

- `src/spec/harness/ProgramRunner.java:469–495` 使用 `System.currentTimeMillis()` 设置测量起点和计划终点，然后按 expectedDuration 休眠，记录的 iteration 终点为计划终点。
- `src/spec/harness/BenchmarkThread.java:153,208` 使用 `System.currentTimeMillis()` 记录每次 loop 起止时间。
- `src/spec/harness/results/IterationResult.java` 和 `LoopResult.java` 保存这些时间与操作数。

因此 raw 中精确的 120000 / 240000 毫秒表示套件的规定窗口，不能据此证明当前系统两种时钟的速率一致。这一现象是跨机器成绩和参数效果解释中的剩余不确定性，不能仅靠 native compliant 标记排除。未确定其系统级根因，也未测得可用于校正分数的可靠系数。

没有改动 Windows/WSL 配置、系统时间服务、benchmark、properties、原生时间戳或分数。保留套件生成的原始成绩与两种经过时间；课程实验的实际运行、计算正确性与 SPEC 官方发表审核分别说明。
