# A2 最终候选检查记录

完整测量、报告、结果目录、图片和本地检查已完成。最终工程验收仍待独立读取 GitHub 实际文件；本记录不授予 Engineering = PASS。Submission = NOT_READY；未操作水杉。

起始本地及远端 main：`764cc9055782463cb8f15495cdebb2af55ac5229`。目标仓库：[woobowen/Softwaresystemoptimization](https://github.com/woobowen/Softwaresystemoptimization)。发布后的 commit SHA、远端读取及渲染结果见最终发布回执。

- [执行记录](../formal-campaign/campaign.json)：最终 Gate 和七次性能运行均首次通过。Base `.015` 为 604.34 ops/m、38 workload、Run is compliant、无 violations。
- [Pre-sync 决策](../formal-campaign/pre-sync-decision.json)：六次 Windows/Linux 直接对齐样本均满足偏差加不确定性小于 0.5 秒，结论 PRE_SYNC_ALIGNED；停服务后静置 76.146 秒进入 30 分钟 Gate。
- [计时检查](../formal-campaign/final-timing-audit.md)：Gate + Base + 3 default + 3 Serial；区分 runner、launcher 和采样边界，不把外围开销混作漂移。
- [最终统计](../formal-campaign/final-statistics.json)：默认均值 680.83，Serial 均值 721.80，变化 +6.02%；相对极差 7.10% / 5.42%。报告保留区间重叠、三次不足以确认稳定提升的限制。
- [恢复记录](../formal-campaign/restore.json)：timesyncd active/enabled，boot、kernel、tsc、配置哈希、Windows 时间服务和电源方案不变。
- [完整数据检查](../formal-campaign/final-data-audit.json)：七个新 JVM、exact argv 与 /proc cmdline 一致；只增加 -XX:+UseSerialGC；同一环境、22 线程、120/240 秒。144 个原生文件、109 张 JPEG、95 条 HTML 本地资源链接，副本与源 SHA256 一致。
- [图片检查](../formal-campaign/screenshots/visual-review.json)：六张正式图均已打开；五张来自真实终端，官方图沿用原始网页截图并重新核对来源。旧环境图迁移见 [artifact-moves.json](../formal-campaign/artifact-moves.json)。
- [README 四轮检查](../formal-campaign/readme-review.json)、[数值来源](final-value-map.md)、[逐题要求](../requirement-matrix.md)、[脚本检查](script-review.md)均已更新。
- [新 raw 回归](../formal-campaign/parser-tests-final.json)十五用例通过；[runner](../formal-campaign/runner-tests-final.json)六场景通过；[计时检查器](../formal-campaign/tool-self-check/timing-fault-tests.json)十场景通过。故障输入中的非零退出码是预期结果，不是实际 benchmark 失败。

准备阶段发现 `timedatectl timesync-status` 会通过 D-Bus 启动 inactive 的 timesyncd，已改为先读服务状态并在 inactive 时跳过相关查询，保存 [根因与修复](../formal-campaign/preparation/service-query-activation/cause-and-fix.json)。没有新增失败 Gate 或失败性能 slot。Base stderr 仅含 compiler.sunflow 两类 javac Note，详见 [stderr-review.json](../formal-campaign/base-1/stderr-review.json)，原日志保留。

旧 `.006`、`.007–.009`、`.011–.014` 继续仅为 [invalidated evidence](../timing/invalidated-results/manifest.md)。未修改旧原生成绩或有效性字段，也没有重新使用旧分数。新增包、工具链和持久配置均为零，见 [安装记录](../formal-campaign/installation-log.json)。

独立审阅需关注：最终源码是否简洁易解释、README 的回答与文风是否合适，以及对 +6.02% 变化的克制结论。另保留 Base compress 与默认单项均值相差 14.10% 的上下文差异；配置和 parser 检查一致，没有将差异归因于未测量的具体机制。

[文件检查](../formal-campaign/file-hygiene-final.json)：Markdown 与原生 HTML 本地资源链接正常，未发现敏感凭据、安装器、缓存或空目录。超过 10 MiB 的只有原样保留的新旧 Base raw（12.40 / 12.07 MiB），无 50 MiB 以上文件；A1、materials、AGENTS.md 和旧原生结果未修改。

完整暂存 whitespace 检查对原生报告、Java 原始输出和原始 PowerShell CRLF JSON 返回 2；正式源码与编辑的 Markdown 检查为 0。原始字节保留，未修改 Git whitespace 配置。逐文件统计及首次检查工具分类修正见 [staged-review.json](../formal-campaign/staged-review.json)。
