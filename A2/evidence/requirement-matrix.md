# A2 逐题要求表

依据：老师 A2 PDF 第 1–7 题及最终执行要求。30 分钟 Gate、完整 Base 与 3+3 单项均通过计时检查，服务已恢复。本表的 PASS 表示具体要求已有可检查的交付物，不代替独立最终工程验收。

| 要求 | 状态 | README | 对应文件与依据 |
|---|---|---|---|
| Q1：用途、workload、特点、Base/Peak、四份官方文档 | PASS | 1、2 | 官网、FAQ、User's Guide、Run Rules、Known Issues 及 workload 原站说明；[资料检查](formal-campaign/official-references.json) |
| Q2：安装、环境变量、完整 Base/results | PASS | 2 | `.015`，604.34 ops/m，38 workload；[正确性](formal-campaign/base-1/benchmark/assessment.json)、[完整原生目录](../results/base/SPECjvm2008.015/) |
| Q3：总体和至少三个分项、特点比较 | PASS | 3 | 同一个 Base：compress 792.54、derby 1148.35、crypto.aes 397.00；[提取记录](formal-campaign/base-q3-q4.json) |
| Q4：官方结果与本机比较 | PASS | 4 | 官方 853.15；CPU/内存/JVM/OS 与本机表格比较；[原站重新获取](formal-campaign/official-source-resumed-check.json) |
| Q5：同配置三个新 JVM、均值、范围 | PASS | 5 | `.016–.018`；均值 680.83，极差 48.34，相对极差 7.10%；[统计](formal-campaign/final-statistics.json) |
| Q6：运行体会、问题处理 | PASS | 6 | JDK 兼容、FreeType、计时可靠性和重复测量；两段直接说明 |
| Q7：只改变一个 JVM 参数、三次比较 | PASS | 7 | `.019–.021`，仅 -XX:+UseSerialGC；均值 721.80，变化 +6.02%，相对极差 5.42%；保留区间重叠的限制 |
| 计时完整性 | PASS | 2 简述条件 | [八个计时条目](formal-campaign/final-timing-audit.md)、[Gate 独立复算](formal-campaign/final-gate/independent-calculation.json) |
| 配置与文件完整性 | PASS | results/ | [最终数据检查](formal-campaign/final-data-audit.json)：七个新 JVM、相同环境和 compress 配置、exact argv；144 文件、109 JPEG、95 HTML 本地资源链接；逐文件 SHA256 等于安装目录原件 |
| 环境恢复 | PASS | 2 | [restore.json](formal-campaign/restore.json)：active/enabled，boot/kernel/clocksource/config/Windows 时间服务/电源方案均恢复或保持 |
| 正式图片 | PASS | 2、3、4、5、7 | 六张均打开检查；[来源、SHA256 与视觉检查](formal-campaign/screenshots/visual-review.json) |
| README 与数值来源 | PASS | 全文 | [四轮检查](formal-campaign/readme-review.json)、[数值映射](final/final-value-map.md)；无旧性能值、TODO 或内部工作流用语 |
| 正式脚本与测试 | PASS | scripts/ | runner 六场景、最终 raw 十五个 parser 用例、计时十场景、源码语法；[源码检查](final/script-review.md) |
| 旧结果保全 | PASS（文件保全） | 不采用旧分数 | [invalidated-results](timing/invalidated-results/manifest.md) 保留原始内容；不混入新 results/ |
| 独立最终工程验收 | PENDING | — | 需独立读取 GitHub 实际文件；本地自查不授予 Engineering = PASS |
| 水杉 | NOT_READY / 禁止 | — | 未准备提交包，未访问或提交 homework02 |

[运行索引](run-index.md) · [最终候选检查记录](final/final-review.md)
