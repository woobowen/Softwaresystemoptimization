# 第三阶段脚本复查

完成时间：2026-10-01T04:05:09.765693+08:00。逐个阅读了下列源文件；Python AST 和 bash -n 最终检查见 [hygiene-check.json](hygiene-check.json)。正式 runner、parser 与截图工具当前哈希分别匹配其实际测试记录。没有在正式 Base 过程中改动 runner 或 JDK。

| 文件（相对 A2） | 用途 | 实际验证 | 必要性与保留位置 |
|---|---|---|---|
| scripts/run-spec.py | 直接记录 stdout/stderr、PID、命令、环境、结果路径、时间与退出码；锁和信号转发 | 输出两路各 307212 bytes，逐字节与尾部检查；退出 0/7、SIGINT/SIGTERM、并发与覆盖拒绝；真实 smoke、预检和全部正式实验 | 保留为两份正式辅助脚本之一；没有异步读取框架或 tee |
| scripts/summarize-spec.py | 解析 native raw、计算工作项 / 组 / 总分与重复统计、对照原生 TXT | 10 个真实 / 错误输入测试；完整 Base 与六次原生数据；均值与变化重新计算 | 保留为另一份正式辅助脚本；标准库实现，不改输入 |
| evidence/runner/test-runner.py | 针对 runner 的压力、退出码、信号与互斥测试 | 实际执行并生成 runner/test-results.json；对应冻结 runner 哈希 | 内部回归证据，不作为老师要求的源代码 |
| evidence/final/test-summarizer.py | 检查 parser 对真实数据与损坏副本的处理 | 10 项用例通过；临时副本位于仓库外且自动清理；parser-tests.json | 内部回归证据；未损坏或覆写任何原始 raw |
| evidence/compatibility/font-probe/FontProbe.java | 隔离 AWT 字体初始化与绘图问题 | JDK 7 javac 编译；默认 / headless 路径复现失败，系统 FreeType 预加载后绘图成功 | 保留最小诊断源码；class 与临时输出在仓库外 |
| evidence/final/preserve-results.py | 完整复制原生目录，核对 SHA256、格式与 HTML 资源 | 在真实预检、smoke 和全部正式目录执行；每次 copy-manifest.json 留证 | 内部结果保全工具，不改原生内容 |
| evidence/final/check-run.py | 按预检 / Base / 单项 / smoke 模式检查覆盖、正确性、报告、图片和时长 | 在对应真实结果上执行；各 assessment.json，Base 38 项与六次单项检查成功 | 内部验收辅助；不以 exit 0 单独判断成功 |
| evidence/final/monitor-run.py | 只读采集 PID、进程状态与输出进展 | Base 和三次运行序列的 monitor / 进程记录 | 内部运行观测；没有 attach、读取子进程管道或影响计分 |
| evidence/final/run-three.py | 依冻结环境串行启动三次独立 JVM，每次结束后保全和检查 | repeat 与 parameter 两组都正常结束，两个 sequence.log 均有完成记录 | 内部顺序驱动；只有一个明确的参数差异 |
| evidence/final/check-experiments.py | 检查六次命令、JDK、runner、环境、线程、时长和独立性 | 六个不同 PID / raw 哈希，时间不重叠；唯一改变的选项与 /proc 记录一致；experiment-comparison.json | 内部条件核对，不是新 benchmark 框架 |
| evidence/final/capture-terminal.py | 在真实 Zutty/Xvfb 运行命令并直接抓取显示 | 正式截图成功；新增退出码检查后，exit 7 用例拒绝生成成功图片并清理 display；capture-tests.json | 内部截图工具，图像不做像素编辑 |
| evidence/environment/04-jdk7-environment.sh | 展示正式 JDK 与关键环境变量 | 实际终端执行，截图 04 与 capture.json；bash -n | 内部截图命令来源 |
| evidence/base/05-base-running.sh | 显示正在运行的 Base 命令、PID 与输出 | 00:36:18 真实 PID 16566，截图 05；bash -n | 内部运行时截图来源；进程已结束，不能重现当时 PID 状态 |
| evidence/base/06-base-summary.sh | 展示完整 Base 的原生 TXT | 实际 sed 读取 .006 TXT，截图 06；bash -n | 内部截图命令来源 |
| evidence/repeat/08-repeat-results.sh | 从三份原生 raw 重新解析并展示统计 | 实际 parser 输出与 statistics.json / 图 08 一致；bash -n | 内部截图命令来源，无硬编码实验分数 |
| evidence/parameter/09-jvm-parameter-results.sh | 展示 flags、六个 raw 分数、均值和变化 | 实际 parser --compare 与 selection.json，命令 exit 0，图 09；bash -n | 内部截图命令来源，无硬编码实验分数 |

本阶段脚本复查的实际修正是截图工具对子命令失败的处理：增加真实退出码检查，失败时不写出看似成功的图片；成功和 exit 7 两条路径都实际执行。runner / parser 的最终源码保持在已测试版本。所有脚本都具有本任务中的具体用途；未加入通用配置、日志框架、抽象层或无关功能。

根因边界：旧 Python runner 已经写文件，JDK 8 阻塞发生在 SPEC startup 内部的未读取 stderr 管道。新 runner 保证自己的输出不依赖人工读取，不声称能够修改 SPEC 的内部进程行为。见 [runner/review.md](../../runner/review.md)。
