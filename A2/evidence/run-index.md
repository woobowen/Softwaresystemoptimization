# A2 运行索引

当前状态：**BLOCKED_ENVIRONMENT_TIMING**。两次 Hyper-V clocksource 探针失败，原 clocksource 已恢复为 `tsc`。本次只整理和发布 [GitHub 诊断检查点](final/github-checkpoint.md)，没有新的 SPEC run ID 或 timing probe。当前没有正式 Base、repeat 或 parameter 结果目录。

| 探针 | 样本 | Python wall (s) | Python monotonic (s) | Python 差值 (s) | Java 差值 (s) | 前跳 / 后跳 | 门控 |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 601 | 639.180424 | 600.521209 | 38.659215 | 38.659787 | 16 / 0 | FAIL |
| 2 | 601 | 646.435680 | 600.148702 | 46.286978 | 46.287295 | 18 / 0 | FAIL |

第一轮和第二轮分别见 [gate-1](timing/gate-1/summary.json)、[gate-2](timing/gate-2/summary.json)。完整操作、诊断与恢复见 [恢复试验结论](timing/recovery-conclusion.md)。

旧实验索引保留在 [历史索引](timing/invalidated-derived/run-index.md)，其中的正式/完成用语仅描述旧阶段，所有性能分数均已作废。旧 .006、.007–.009、.011–.014 已移入 [归档目录](timing/invalidated-results/manifest.md)，旧 metadata 保持原样，路径变动由 manifest 追踪。

| 本阶段计划中的 SPEC 实验 | 执行状态 | 原因 |
|---|---|---|
| compress timing diagnostic | NOT_RUN | 两次时钟门控失败 |
| replacement Base | NOT_RUN | 不在已知异常环境继续计分 |
| FINAL-REPEAT-1/2/3 | NOT_RUN | 没有通过的 Base 和稳定环境 |
| FINAL-SERIAL-1/2/3 | NOT_RUN | 同上；参数仍固定为 -XX:+UseSerialGC |

[Runner 测试](final/runner-tests-stage5.json)、[parser 历史 fixture 测试](final/parser-tests-invalidated-fixtures-stage5.json)、[monitor 信号测试](final/monitor-signal-check.json)验证工具行为，不构成性能可信度通过。
