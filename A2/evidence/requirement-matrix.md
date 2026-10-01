# A2 逐题要求表

依据：老师 A2 PDF 三页、第 1–7 题及 GitHub Engineering Checkpoint Publish 要求。A2 状态仍为 **BLOCKED_ENVIRONMENT_TIMING**。tsc 探针及两次 Hyper-V clocksource 探针均出现严重时间跳变；原 clocksource 已恢复。GitHub 本次只发布诊断检查点，下一步环境方案尚未决定。下表的工具和文件检查不构成最终工程验收。

| 要求 | 状态 | README | 实际依据与缺项 |
|---|---|---|---|
| Q1：用途、主要 workload、特点、Base/Peak、四份官方文档 | PASS | 1 | 四份 SPEC 官方文档已重新访问；报告回答保留 |
| Q2：安装、环境变量、完整 Base/results | BLOCKED | 2 | 安装/JDK/FreeType 资料与新环境截图齐全；两次 timing gate 失败，无 replacement Base 或正式 results |
| Q3：总体结果和至少三个分项成绩及分析 | BLOCKED | 3 | 仅保留 compress/derby/crypto.aes 特点，缺可信新分数与基于新成绩的比较 |
| Q4：官方结果与本机比较 | PARTIAL | 4 | 官方 853.15 与软硬件配置已重新获取，内容 SHA256 与历史一致；缺本机新 Base |
| Q5：同配置三个独立 JVM、原始值、均值、范围 | BLOCKED | 5 | 新三次未启动；旧结果全部归档作废，不给出正式统计 |
| Q6：体会、问题与处理 | PARTIAL | 6 | 保留实际 JDK 兼容、FreeType 和计时问题经历，尚非完整实验总结 |
| Q7：固定一个 JVM 参数并比较 | BLOCKED | 7 | 参数仍为 -XX:+UseSerialGC；新 3+3 未执行，不能给出变化率与性能结论 |
| 旧文件保全 | PASS（文件完整性） | 不引用旧性能图 | invalidated-results/integrity.json：8 目录、154 文件、114 JPEG、98 HTML 本地资源链接，副本等于源目录 |
| 脚本行为 | PASS（工具测试） | scripts/ | runner：输出/退出/信号/互斥/防覆盖/启动失败；parser：15 用例及直接字段/统计复算，明确使用 invalidated fixtures；新结果测试 NOT_RUN |
| 时钟探针与 monitor | PASS（工具运行）；Timing FAIL | 2 | Java 源未变，两轮各 601 样本，整数纳秒复算一致；monitor CPU <0.001 s/短自检，SIGTERM 收尾成功 |
| 文档与图片整理 | 完成失败状态整理 | 1–7 | 旧性能值已移除，无 TODO；两张当前图片均实际打开。没有生成不存在的新成绩截图 |
| Final Value Map | 完成失败状态映射 | 全文 | final/final-value-map.md 仅映射当前报告保留的配置和官方数值，正式性能字段为空缺而非旧值 |
| GitHub 发布 | 仅诊断检查点 | — | 本提交保全真实工程供远端文件级诊断；见 final/github-checkpoint.md。推送后的 SHA 对照及远端读取结果在发布回执中记录 |
| 水杉 | NOT_READY / 禁止 | — | 未访问、打包或提交 |

[时钟失败结论](timing/recovery-conclusion.md)；[当前运行索引](run-index.md)；[旧数据清单](timing/invalidated-results/manifest.md)。
