# P1 Goal 1 证据入口

- [滚动计划与任务 owner](current_plan.md)
- [原题与 Goal 1 逐项矩阵](requirements.md)
- [共同基础版本快照](baseline_snapshot.json)
- [文献筛选、原文阅读范围与借鉴限制](literature.md)
- [两个单项的实测闭环与保留决定](optimization.md)
- [实际代理职责和阶段调用](agents.md)
- [测量协议](protocol_v1.md) / [机器可读协议](protocol_v1.json)（冻结状态以文件内容为准）
- [独立代码/正确性审核与修复](reviews/code_review.md)
- [独立实验设计、原始数据和报告审核](reviews/experiment_report_review.md)
- [初始真实环境](environment/initial_environment.txt)、[输入哈希与起始Git状态](environment/inputs.json)、[代理/工具能力](environment/capabilities.json)
- [局部工具与安装追踪](environment/dependencies.md)
- [目标精确语义差异](environment/target_adaptation.diff)、[高优化汇编实查](environment/kernel_assembly.txt)
- [旧计时异常、诊断与最小修复](environment/timing_issue.md)、[逐项异常数据](environment/timing_anomaly.json)
- [生成器marker失败与修复](environment/validation_generation_issue.md)

数值检查原始 JSONL 位于 environment/target_*，文件名的 monotonic 表示当前新目标。旧版的验证/预试保留为前期记录，不作为当前正式性能样本。旧异常预试位于 ../results/pretest/。

[完整20配置参照](../results/reference_v1/plan.json)、[在线选择与各轮返回确认](../results/selection_v1/plan.json)均已完成；原始 trial JSONL、CLI stdout/stderr、外部 driver 成本与计划在相应目录。数据行保留实际时基、完整命令和代码/协议哈希。[派生汇总](../results/summary/summary.json)、[20配置统计](../results/summary/grid_summary.csv)、[逐轮搜索表](../results/summary/search_summary.csv)、[真实在线轨迹](../results/summary/online_curves.csv)可从原始批次重生成。[九次参照冲突诊断](../results/conflict_selection_v1/plan.json)和[三留出seed](../results/holdout_v1/plan.json)均已实际结束并逐值独立审核。258有效目标测量、失败0；候选均INC无采用，基础Random留出近优0/3；原t_ref不替换。[完整成本](../results/summary/batch_costs.csv)与[有限诊断](../results/summary/reference_conflicts.csv)分开保留。

[实际执行命令与日志](commands/execution.md)、[真实截图来源](commands/screenshots.json)记录工程操作及截图方法；[源码/原始数据冻结快照](final_snapshot.json)，最后干净复现、完整产物终审与GitHub实查仍待结束。

编译缓存、可执行文件、临时下载及虚拟显示工具均在忽略的 .cache 中；测量结果与审核记录不依赖这些缓存。
