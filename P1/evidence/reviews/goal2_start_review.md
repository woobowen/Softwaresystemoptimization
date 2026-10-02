# Goal 2 起点、历史与安全独立审核

审核角色：`/root/review`；作者范围仅为 `evidence/reviews/goal2_*.md/json`。
本记录不是最终 Engineering 判断，未启动 compiler、target、unittest 或绘图。

首命令为 `ls -la`。实际目录包含 `A1/`、`A2/`、`P1/`、根 `AGENTS.md`、老师 P1 PDF/C 与两份任务提示词；首读时分支为 `main`、HEAD 为 `3ac0c4688b964c873379d012cbcf09afb7ed0937`。用户未跟踪输入为两份提示词和根 C，不移除或提交它们。适用规则为根 AGENTS，P1 下未发现覆盖文件。

已读老师完整一页 PDF、原始及适配 C、完整 report/README、core/experiment/summarize/validate_target 与两组旧 tests，以及 v1 协议、优化/文献/计时/截图/审核与复现证据。老师要求与提示词一致：三接口、原 Matrix Multiplication、s=8/16/24/64/128、O0/O1/O2/O3、完整 Grid、另两算法、report.md 与环境信息。水杉 `project01` 仅为后续提交目标。

## 历史原文核对

独立标准库脚本读取四个 v1 plan 的全部 journals 和 driver，逐份重算 fingerprint、原 stdout/checksum、rc/spawn、唯一 start/completion、trial 中位数与 best、真实次数及完整 driver 成本。258 次有效调用、20 配置各 3 次，无失败；所得数值见 [goal2_start_review.json](goal2_start_review.json)。未通过当前工程分析函数取得这些结论。

| 交接项 | 原文复核及影响 | Goal 2 必须关闭的依赖 |
| --- | --- | --- |
| C1 | Random/S1 seed130363 都返回 128/O2，binary SHA 一致，确认 33.191216/36.206318 秒。holdout229939 的 64/O3 按身份参照差距为 4.0830%，跨时段确认差距为 7.5880%。 | 使用统一配置身份参照映射与全部返回锁定后的共同面板，独立 A/A 单列。不能沿用专属确认差当策略收益。 |
| C2 | 128 的 O1/O2/O3 第三轮均更快；旧五探针 RAW/MONO=1.09100945–1.09100975。 | 检查原始 ns、边界、同域 guard 与时间域稳定性；只读服务信息不能证明根因。M0/M1 实测决定分辨范围。 |
| C3 | v1 固定门为 5.6 秒；三个 Random 返回在旧共同参照中的改善余地为 4.826466、0、3.001831 秒。 | 新正式数据前冻结可达的质量/成本双轴规则，5%目标与测量分辨力分开，不修改旧判定。 |
| C4 | 旧 Greedy 起点确为 16/O2、128/O3、64/O3。 | 六个新种子、平衡算法顺序、独立结构覆盖起点面板。固定 B8 Grid 次序保留，不能泛化到所有枚举。 |
| C5 | 完整读旧正文，恢复叙述、批次名、负结果审核过程与重复截图区分较多。 | 作者按题号精简后需整篇连续复读，而非词表筛查。 |
| C6 | 旧 screenshots.json 含 Xvfb `-listen tcp`、`-ac`，不能复用。审核者独立只读检查没有 Xvfb/xterm/ffmpeg 或 6000 段 TCP，根主控环境记录一致。 | 最终截图使用自己授权的 Unix display，实际检查启动/清理与每张图；未发现外部访问证据，不声称曾遭攻击。 |
| C7 | v1 task_status 的 historical_only 仍核当前 target/framework SHA；修改 core 后当前 HEAD 不能直接重算 v1。 | 使用匹配固定旧提交的隔离 checkout 及旧脚本，核数值相同；不删 hash guard、不改 header。 |

主控 `history_goal2.json` 中 431 份保护文件独立检查无一变化；两个作业 tree 分别为 A1=`e2e8fd3c3d04f98ea7d16a05ee3126adbf9a47b0`、A2=`139b6e7469d63b27cfa100d1e005061548d36ce8`。一个历史清单足以记录依赖，避免重复全仓清单。

## 诊断与实现审核条件

1. 初始两档配置、A/A 标签及 M0/M1 完整次序须在运行前写明；每个标签有多个真实独立样本。比较排序、A/A 原秒差和新增实际成本，不把去重身份评分当环境稳定证据。
2. 正式 C 继续 MONOTONIC；process 新增多时间域须保存调用顺序和单位。MONO kernel/process 的大小 guard 不能混用 RAW 或 CPU，资源保护需真实计入所有已启动 n4096 与必要构建/等待。
3. 6+2 finalist-only S3 可作为一个机制：六个 Random 前缀探索、两个候选各新进程复核；固定 R8，成功 finalist 的两个样本 median 后返回。复核变慢必须使 best 上升，不能返回历史 trial 的单次最小值；失败不能免费补调用；候选不足、预算耗尽与恢复需实测。
4. 所有搜索返回先锁定，再生成去重共同面板，锚点及面板样本只能事后评价。共享运行项目账只记一次，算法内复核全计搜索成本。
5. 正式入口前需要独立代码测试、诊断结果审核、新协议目标/编译/源码/规则身份及精确调用上限。批准初始有限诊断不等于批准正式优化。

起点与历史保护关口可继续；C1–C7 尚未在本记录中关闭。最终代码、实测、报告、图片、干净复现和发布审核均等待真实产物。
