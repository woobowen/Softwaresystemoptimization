# Goal 2 派生分析与接受规则独立审核

审核者：`/root/review`；分析/方法作者：`/root/measurement`。完整读取 `scripts/summarize_v2.py`、`tests/test_goal2_summary.py` 和配套协议草稿；37 项专用 fixtures 已实际独立通过，初始诊断已独立重算。本记录尚不放行正式实验，时钟与完整 A/A 测量关仍未关闭。

## 独立检查的规则

- 新完整参照为所有算法提供相同配置身份的 `g_ref`；同时段面板先锁定块内全部搜索返回，按身份去重，仅作外部评价。独立 A/A 标签仍各保留真实进程时间，没有借身份合并掩盖漂移。
- 分析独立重放 Grid、Random、Greedy、S3；逐步在线样本和 `best_so_far` 不接受外部确认回填。S3 初测前缀、最多两个 finalist、成功复核资格、平局与预算和恢复有明确独立重算。
- 正收益定义为参照最优的百分比点；端点分子与锚点分母取四角最小/最大，保留负值和跨零方向。相同配置的配对选择收益严格零，不能用不同时段秒差判选择退化。
- 5% 目标、2pp 逐块风险、10% 实际 driver 节省分别冻结，不将诊断 rho 用于扩大退化容差。端点和 rho 为有限描述尺度，不是 CI、总体非劣或“没有负优化”证明。主实验和三个新 seed 的确认均通过才保留候选。
- 实际调用/搜索内复核与共同外部确认分账；内核、进程、编译为 full driver 子项，不能另加到 full driver 总额。全局唯一 attempt_id 是主账，batch driver 的副本必须一致，重复共享面板不能多计。

## 已发现并经静态复核修正的问题

| 位置/问题 | 严重性与影响 | 修正后的实际路径 | 状态 |
| --- | --- | --- | --- |
| `read_batch` 生成 panel 默认使用执行根 | 中：干净 clone 可能与原绝对 metadata 错配；分析还可能创建缺失 raw 面板 | `ex.panel(..., historical=True)`；runner 历史模式只读，缺失不写 | 实现及独立 fixtures 关闭；干净 clone 全重算待交付关 |
| `cost_table` 将 recovered `clock_elapsed_s=None` 当 dict | 高：恢复账无法汇总，或未知 driver/calls 被误叫完整成本 | None 保留为 null；unknown_calls/driver/bound 不成为实际完整成本；专用 recovered fixture 已读 | 修复与独立 fixtures 关闭 |
| 全局账不完整未影响候选接受 | 高：六个局部已知 pair 可能在仍有未知全局任务时 KEEP | CLI 明确把全局 ledger 存在且完整传入 `decision(project_cost_complete=...)`；未知或未结任务一律阻止 KEEP | 修复与独立 fixtures 关闭 |
| S3 曲线资格变化未可视标明 | 中：前六步临时首测 best 与后续成功 finalist-only 连成同样线型，读者可能误解上升 | 作者现保留原始在线值，以虚线/复核三角点和文字说明阶段；预算轴另由累计 `measurement_start` 计真实调用 | 静态修正与在线数据 fixtures 通过；最终图片实际查看待执行 |

## 正式协议关前的剩余检查

核对补诊断后的 A/A、M0/M1、rho 和可分辨两档门；冻结精确调用上界与按诊断更新的资源预测；读取正式协议 approved/frozen 的最终身份。任何未知成本、参照冲突或不能支持 2pp 风险均不能 KEEP。早期 26 项 fixtures 的作者执行不能替代审核者证据；最新 37 项独立执行记录见下节。

正式原始数据产生后还须独立重算全部 20×3、六块真实步骤、面板/参考来源、每个种子成本、起点面板、候选判定及必要新 seed 确认。代码规则通过不预先认定数据结论成立，也不授予最终 Engineering PASS。

交叉审核另见 implementation 角色独立持有的 `goal2_method_analysis_review.md/json`：AS1 原始成本边界/调用交叉核对、AS2 未传入的 raw 保护、AS3 曲线阶段、AS4 合法失败批次明细、AS5 不同目录相同搜索身份覆盖。作者已补充最小修复，诊断性能窗口内未改 frozen runner；全部仍需独立短测试复核。此次两条分析审核的文件分工已由主控明确，互不覆盖。

## 初始诊断原始数值独立重算

2026-10-02 15:26 UTC，以 stdlib 单独解析原 plan、全部 27 个已启动普通 journal 和共享资源账本，不导入项目分析函数、不运行目标或编译。每条 measurement 的三域整数边界、输出首行、同域内核/进程保护与唯一二进制身份均核对；每个 task_end 的三域差和 max 资源成本从对应 task_start 重算。结果保存于同名 JSON 的 `initial_diagnostic_independent_reparse`。

原普通 28 任务为 27 次真实启动、26 个有效完成、1 次中断、1 未启动；两次内核诊断另计。全 Goal 29 次 n4096，受控资源总计 2057.203209297 秒，按已关闭任务的三个正域差最大值加总，与作者派生一致。共享实际调用没有重复计账。

四个 A/A 单元的原标签中位数与配对百分差均独立重算一致：M0/F −3.2324355%、M0/M −2.5851248%，二者因缺第三有效标签仍不完整；M1/F +1.8442951%、M1/M +0.7257492%。M1/F 的第三对差 +13.7846047% 留存，不能从较小标签中位数差声称单对稳定。26 个有效目标进程 q 范围 0.9981160–1.0096709，原中断前缀未混入该完整范围。

`initial_diagnostic.md` 和 `diagnostic_summary_v2/summary.json` 的数量、A/A 表、成本与 arrangement/rho=null、performance_gate=false 均有原始记录支持。会计成本已知与测量完整严格分开；这次原始重算通过不授予正式性能准入。专用分析 fixtures 的独立执行仍等待主控窗口。

## 分析专用 fixtures 独立执行

2026-10-02 15:32:12.938–15:32:13.054 UTC，主控授权纯 fixtures 空闲窗口，实际取得 `.cache/performance.lock` 非阻塞独占锁后执行 `python3 -B -m unittest discover -s tests -p test_goal2_summary.py -v`。37 项全部通过、exit 0、无 skip；unittest 报 0.012 秒，外层 MONOTONIC/RAW/REALTIME 分别 0.115351367/0.115581514/0.115351347 秒。锁已释放，n4096=0，无编译；它是工程测试成本，不补记成受控目标成本。

分析源码 `96352437a0e9b76e3ccd709d048736721a0e7359ad238fdef89033aff9ad624f`、专用测试 `421acfa96fbd46ead6bcf5bce89ef34cae401a04f190144a5b4490c864c0f3d7` 与 runner `22a839…` 执行前后不变。完整输出、三域整数边界和身份保存同名 JSON 的 `independent_analysis_regression`。恢复未知成本、同身份零选择收益、回填/缺失/重复数据、非法字段、失败批次、A/A 原标签、原始成本边界和 partial 闭环的 fixtures 经独立执行通过。上述 A1–A3 与 AS1/AS2/AS4/AS5 的相关代码修复回归关闭；A4/AS3 最终图像仍须实际查看，干净克隆全重算与正式原始结果审查仍待后续。

## 初始阶段代码的固定 Git 身份

主控在新 driver 改动前创建普通本地检查点 `2fc0c334039bb6696c4d83acbe029ce65ca66ab9`。审核者实际读取该提交 blob 并重算 SHA，确认 runner `22a839…`、analysis `963524…`、诊断 protocol `8c0d51…`、原 plan `cbfc028…` 与账本 `9812d4…` 均已保存在 Git。158 个差异路径全部位于 P1；此次尚未 push，不算远端发布完成。后续干净复现可从该固定提交取匹配脚本重算初始诊断，不必放宽哈希检查或修改旧 header；README 的真实固定版本入口和全重算仍须交付关实测。

## 固定版本历史重生成的实际产物复核

2026-10-02，独立读取主控两个忽略 detached worktree 的真实 HEAD，分别为 `3ac0c4688b964c873379d012cbcf09afb7ed0937` 与 `2fc0c334039bb6696c4d83acbe029ce65ca66ab9`；对 summarize/experiment/autotuner 的实际源码 bytes 与各固定 Git 对象逐一比较，全部一致。直接计算实际重生成文件 SHA：Goal1九个数据文件和两张图片共11项、初始诊断七个数据文件，全部与保存的原始派生 SHA 一致，stderr均为空、实际作者日志退出0、两个任务 n4096调用均0。此复核不重复启动作者分析，也不取消任何身份检查。证据入口 `../reproduction/goal2/goal1-comparison.json` 和 `initial-comparison.json`；独立检查结果在配套 JSON。最终还需README的固定版本入口和全431历史保护项核对。
