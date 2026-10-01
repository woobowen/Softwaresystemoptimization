# Base 与单独 compress：重测比较状态

**NOT_RUN / BLOCKED_ENVIRONMENT_TIMING**。Hyper-V clocksource 下的两次 10 分钟探针仍存在约 38.659 和 46.287 秒累计 wall/monotonic 差异，因此没有启动 replacement Base 或新三次单项，也没有新的分数、比值或差异成因结论。

不能用旧 Base 或旧 3+3 回填比较。旧数据及对 parser、benchmark 名称、JDK、线程、时长、suite context 的调查仍作为历史证据保存，见 [原调查](conclusion.md)。是否在稳定环境中继续存在 Base/single 差异，必须等待后续可信测量。

本任务没有为了缩小差距或追高分追加 benchmark。时钟试验详情见 [恢复结论](../timing/recovery-conclusion.md)。
