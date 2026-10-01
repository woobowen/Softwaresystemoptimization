> 第五阶段更新：已授权并试验 Hyper-V runtime clocksource，两次 10 分钟探针均失败，已恢复 tsc。后续结论见 [恢复试验结论](recovery-conclusion.md)。以下保留第四阶段调查，其中的候选操作和授权状态属于历史；当前只发布 [GitHub 检查点](../final/github-checkpoint.md)。

# 470.629 秒差异：调查结论

结论为任务定义的 **C**：正式计分受时钟异常影响的风险不能排除。旧 `.006` 不能获得测量可信度通过；需要稳定时钟后的一次 replacement Base。原始结果、原生合规字段和分数均未修改。

## 实际计时间隔

历史 runner 源码见 [frozen-run-spec.py](../runner/frozen-run-spec.py)，SHA256 与 Base `run.json` 的 `runner_sha256` 一致。顺序为：

`获取锁 / 创建日志目录 / 检索原结果 / 记录环境 → wall start（秒精度） → 写元数据 → monotonic start → 打开日志 → Popen Java → 写 PID → wait Java → 关闭日志 → wall end → monotonic end → 查找结果 → 写元数据 → 外部复制结果`。

日期时间为 `2026-10-01T00:34:37+08:00` 到 `02:54:41+08:00`，差 8404 s；历史 `wall_seconds` 字段实际保存 monotonic 的 7933.371 s，差 470.629 s。开始处的元数据写入、打开日志等微小边界差异及秒级取整存在，但不能解释约 471 s。preserve 不在任一计时区间。没有单独记录 Popen 内部 exec 的精确时刻、退出瞬间或复制起止时间，不能事后补造。

Base stdout 的 check 开始为 00:34:49，最后测量后 02:54:36 的监视记录已经显示生成报告；runner 在 02:54:41 记录退出 0。127 个运行中样本的 wall 时间与 `ps` 进程 elapsed 对照，累计差从开始逐步增加到 469.258 s，见 [base-timeline.csv](base-timeline.csv)。因此差异不是集中发生在末尾的结果复制阶段。

新 runner 增加紧贴 Popen/wait 的成对 `clock_start`、`clock_end`，明确输出 `wall_clock_seconds` 和 `monotonic_seconds`。旧记录不覆盖；历史字段仅为兼容保留。

## SPEC 1.01 的计分

[本机源码摘录及源文件哈希](harness-excerpts.txt)：

- `ProgramRunner.java:469–495` 以 `System.currentTimeMillis()` 设置 start，stop=start+expectedDuration；计时线程 sleep(expectedDuration)，但写入 raw 的 end 固定为 stop。
- `BenchmarkThread.java:153,208` 用 `currentTimeMillis()` 记录每个 loop。结束时用末次 loop 越过 stop 的比例扣减 operations。
- `IterationResult.getScore()` 为 `operations * 60000 / (endTime-startTime)`。`BenchmarkResult.getScore()` 选择最好 iteration。
- startup 是固定一次操作，使用同一 loop 的 wall-clock 时间，等待子 JVM 完成；没有使用 `nanoTime()` 隔离 wall-clock 跳变。

Base 21 个吞吐项目的 raw 测量窗口均为 240000 ms，预热为 120000 ms；这只是计划窗口。七份原结果的 compress 中，每个测量线程均出现末次扣减比例大于 1；Base 记录 1535 个 loop，却扣减 89.9101235 个操作后报告 1445.0898765。细节见 [raw-duration-audit.json](raw-duration-audit.json)。不能把超出一个末次操作的扣减解释成正常末次操作裁剪，更不能人工改分。

## 系统记录和复现

按要求仅查询 2026-10-01 00:30–03:00 +08:00：Windows System 查询成功（China Standard Time），目标 provider/event ID 无匹配事件；Linux kernel 查询没有匹配记录。没有证据支持一次约 470 s 的宿主睡眠。systemd-timesyncd 在该窗口记录了时间服务器联系/超时/切换；日志没有记录每次校时，不能恢复所有历史 step 的精确时刻。

[10 分钟探针](probe-10min/summary.json)完成 601 次采样：Python wall 650.366261 s、monotonic 600.378370 s；Java wall 650.366 s、nanoTime 600.378267 s。两组差均约 **49.9879 s**。共 19 次大于 50 ms 的时钟跳变，18 次前跳、1 次后跳；最大单步差 +3.747466 s，最小 -1.086558 s。当前 timesync 报告的 +3.254952 s 与一次探针 step 数值相同，支持校时进入测量时间轴。

[Windows 独立探针](current-host-probe.json)的 wall 30.158 s 与 Stopwatch 30.1598493 s 接近。当前 WSL clocksource=`tsc`；只读查询还有其他可用源，并记录了 adjtimex 状态。尚未证明底层根因，尚未修改系统配置。

这不是“WSL 有差异但分数可以保留”的结论。新的独立 compress 诊断同样出现 wall 400.059095 s 对 monotonic 374.719365 s，说明直接重跑仍会遇到异常。下一步需先按 [恢复选项](recovery-options.md)取得系统运行时配置变更许可并验证稳定性；不在已知异常状态下消耗唯一 replacement Base。
