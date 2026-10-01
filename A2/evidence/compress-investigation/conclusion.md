> 后续状态：第五阶段两次 Hyper-V 探针均失败，没有可信 replacement Base 或新 3+3；[新的比较状态](final-comparison.md)。下文保留原调查结论。

# compress 361.27 与 800.59 的调查

结论：不是字段选择或统计错误。单项约 800 的水平已再次复现；完整 Base 的该次 compress 确实执行得更慢，同时旧 Base 存在计时完整性问题，需由稳定环境中的 replacement Base 替换。尚不能把 2.22 倍差异全部归因于某个硬件或 JVM 机制。

## 从 raw 确认

四份原始数据的字段都是 `benchmark-results/benchmark-result[@name='compress']/iterations/iteration-result`，单位 ops/m；不是 `startup.compress`，不是 warmup，也不是其他组分数。各自 start/end 相差 240000 ms。

| run | operations | operations × 60000 / 240000 |
|---|---:|---:|
| .006 | 1445.0898764644649 | 361.2724691161162 |
| .007 | 3204.9457923743635 | 801.2364480935909 |
| .008 | 3151.8509983379604 | 787.9627495844901 |
| .009 | 3250.3298662377665 | 812.5824665594416 |

[回归测试](../tools/test-compress-regression.py)使用人工逐项核对的 raw 操作数和起止时间作为预期值，确认 parser 分别选中 compress throughput；同时排除 startup 与 warmup。七个原结果均通过。

## 实际配置对照

完整逐 run 记录见 [configuration-comparison.json](configuration-comparison.json)。

| 项目 | Base .006 compress | repeat .007–.009 compress |
|---|---|---|
| JDK / VM | OpenJDK 7u75 RI / 24.75-b04 | 相同 |
| Java path / JAVA_HOME | `~/.local/opt/java-se-7u75-ri/bin/java` / 对应 JDK 根目录 | 相同 |
| JVM args | 无调优参数 | 无调优参数 |
| GC | 默认；同 JDK 独立 flags 检查为 Parallel GC | 相同选择方式 |
| heap | 无 -Xms/-Xmx；测量 PID 堆参数没有保存 | 相同；不能把独立 flags 当实时进程数据 |
| LD_PRELOAD | `/usr/lib/x86_64-linux-gnu/libfreetype.so.6` | 相同 |
| workload | `compress`，multi，runMode=2 | 相同 |
| benchmark threads | 22 | 22 |
| warmup / iteration | 120000 / 240000 ms | 相同 |
| iterations | minIter=maxIter=1 | 相同 |
| SPEC argv | `-jar SPECjvm2008.jar --base` | `-jar SPECjvm2008.jar compress` |
| 原生 result mode | SPECjvm2008 Base；Run is compliant | 标题沿用 Base；单项 sequence 不 compliant |
| runner | SHA256 `902363d62d17a109faefa3de3ba49d76203757e81c23b976e21b958b534b98f6` | 相同 |
| score field | compress measurement operations / elapsed | 相同 |

源码 `Launch.runBenchmarkSuite()` 在同一 harness JVM 中按顺序执行各项。Base compress 之前执行 startup、compiler.compiler 和 compiler.sunflow；单项只执行 check 后进入 compress。`ProgramRunner` 清理文件缓存但不重新启动 JVM，默认没有无条件强制 GC。因此 suite context 确实不同；这不等于已经证明某种 GC/缓存机制导致这次差异。

监视样本中 Base compress RSS 约 3.5–4.1 GiB，repeat-1 约 0.73–0.93 GiB；是进程驻留集，不是 Java live heap。原 Base 记录 1535 个测量 loop，中位耗时 3131 ms；三次 repeat 分别记录 3417/3427/3430 个，中位 1531/1518/1508.5 ms。差异已经存在于 loop 执行记录，不只是 reporter 四舍五入或 parser 运算。[loop-comparison.json](loop-comparison.json)

## 最小诊断

`.014` 沿用原 JDK、LD_PRELOAD、22 线程、120/240 秒和无 JVM 调优参数，单独运行 compress；仅 runner 新增双时钟字段。原生结果 **799.004529 ops/m**，checksum/check 正常，原生报告完整，副本 SHA256 一致。存放于 [standalone-diagnostic](standalone-diagnostic/)，不加入第 5/7 题。

同次 wall=400.059095 s，monotonic=374.719365 s；计时异常仍在。原 Base 与所有旧单项测量均无法据原生 validity 字段排除该风险，见 [计时结论](../timing/conclusion.md)。尚未运行 replacement Base：必须先恢复可测量环境；不能以“普通波动”“温度”“频率”补出根因，也不为得到更高分继续刷实验。
