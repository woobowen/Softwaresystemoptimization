# A2 运行索引

最终计时检查与七次测量均通过；timesyncd 已恢复 active/enabled。全部运行属于 `a2-formal-20261001T071902Z`，采用 tsc、同一 boot ID、相同 JDK 和环境。独立最终工程验收仍待进行。

| slot | native ID | ops/m | PID | Timing / correctness |
|---|---|---:|---:|---|
| base-1 | SPECjvm2008.015 | 604.34 | 210526 | PASS / PASS |
| repeat-1 | SPECjvm2008.016 | 667.24 | 254956 | PASS / PASS |
| repeat-2 | SPECjvm2008.017 | 663.45 | 257053 | PASS / PASS |
| repeat-3 | SPECjvm2008.018 | 711.79 | 259264 | PASS / PASS |
| parameter-1 | SPECjvm2008.019 | 698.80 | 261218 | PASS / PASS |
| parameter-2 | SPECjvm2008.020 | 728.66 | 263255 | PASS / PASS |
| parameter-3 | SPECjvm2008.021 | 737.95 | 265097 | PASS / PASS |

Base 为 Run is compliant、38 workload、violations 为空。六次单项为 Run is valid, but not compliant，唯一 violation 为未执行完整可发布序列；这些原生字段没有修改。每次均保存 stdout/stderr、runner wall/monotonic、Host Stopwatch、15 秒 monitor、进程 argv、完整原生目录与 SHA256。

[八次计时检查](formal-campaign/final-timing-audit.md) · [最终统计](formal-campaign/final-statistics.json) · [配置与副本检查](formal-campaign/final-data-audit.json) · [服务恢复](formal-campaign/restore.json)

Base compress 为 792.54，单项默认均值为 680.83（低 14.10%）。parser、JDK、环境与 compress 配置一致；全套中此前已运行其他 workload，而单项每次新建 JVM。保留这个上下文差异，没有根据分数补跑或断言具体机制。

准备阶段一次快照查询触发 timesync1 D-Bus 自动启动；修复 inactive 时跳过该查询后重新开始，未计为 Gate 或 benchmark 尝试。见 [原因与修复](formal-campaign/preparation/service-query-activation/cause-and-fix.json)。最终 Gate 和七个性能 slot 均一次通过。

历史隔离前计时问题和旧成绩仍保留在 [恢复结论](timing/recovery-conclusion.md)、[旧运行索引](timing/invalidated-derived/run-index.md)和 [invalidated-results](timing/invalidated-results/manifest.md)。这些旧结果不参与当前统计。
