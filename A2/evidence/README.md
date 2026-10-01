# A2 工程证据索引

当前状态为 **BLOCKED_ENVIRONMENT_TIMING**。此次 GitHub 提交是供诊断的 checkpoint；[当前说明](final/github-checkpoint.md)与[要求表](requirement-matrix.md)列明未完成项。没有可信 replacement Base、final 3+3 或水杉提交。

| 内容 | 入口 |
|---|---|
| 三次长探针、原始样本与恢复记录 | [timing 调查](timing/conclusion.md)、[恢复结论](timing/recovery-conclusion.md) |
| 旧 Base、repeat、Serial GC、timing diagnostic | [invalidated manifest](timing/invalidated-results/manifest.md) |
| 源码、依赖和历史调用方式 | [tools](tools/README.md) |
| runner / parser 当前检查 | [runner 测试](final/runner-tests-checkpoint.json)、[parser 历史 fixture 测试](final/parser-tests-checkpoint.json)、[语法/编译](final/checkpoint-syntax-checks.json) |
| 本次保全、链接、文件卫生检查 | [本地验证记录](final/checkpoint-local-validation.json) |
| JDK / 字体兼容性 | [决策经历](compatibility/decision.md) |
| 环境与历史安装记录 | [安装日志](environment/installation-log.md) |

`base/`、`repeat/`、`parameter/`、`compress-investigation/` 里的日志、assessment 和派生统计属于历史运行；`final/*stage*.json`、`final/stage*-review.md` 等保留当时检查结果。它们出现的“正式”“完成”或 `passed` 不是当前性能资格，也不表示最终工程验收。所有旧性能值都不能进入当前报告的正式结论。

历史 `run.json` 的绝对路径和原始 `copy-manifest.json` 不改写，路径迁移由 invalidated manifest 解释。SPEC 原生 validity 字段仍是当时 harness 的判断；后发现的系统计时异常是另一个限制。失败输出、空 stderr 及 `.004` 字体故障的 79 个空 JPEG 均保留；单独的 `console.log.gz` 是 JDK 8 诊断日志，不是软件安装包。
