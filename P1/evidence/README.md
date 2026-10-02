# P1 证据入口

本阶段为 Goal2 PARTIAL：测量跨时段可比性受阻。当前 report 保留真实历史结果，按配置身份统一评价；新正式参照、六组在线比较、S3选择/确认及起点面板未执行。Engineering 等待外部实际 GitHub 终审，未提交水杉。

## 本阶段

- [完整阶段交接事实](goal2_stage_result.md)、[滚动事实及资源边界](current_plan.md)、[逐项要求状态](requirements.md)、[C1—C7闭环](goal2_review_closure.md)
- [431历史保护清单与起始A1/A2 tree](history_goal2.json)、[实际多代理和文件owner](agents_goal2.md)
- [只读环境](environment/goal2.json)、[复用工具/零新增依赖/精确局部清理](environment/goal2_dependencies.json)
- [初始诊断协议](protocol_diagnostic.json)、[有限追加设计](measurement/clock_followup_design.md)、[实际联合分析](measurement/clock_followup_analysis.md)
- [正式MONO协议](protocol_v2.md) / [JSON](protocol_v2.json)：仅启动预热，完整时钟门停止，不可恢复为有效成绩
- [RAW有限A/A冻结协议](protocol_raw_aa.json)、[新timer设计](measurement/raw_timing_design.md)、[未放行的正式设计](measurement/raw_formal_design.md)
- [所有受控任务唯一成本账](measurement/resource_ledger.jsonl)、[RAW停止407行闭合快照](measurement/raw_timing/aa_ledger_snapshot.jsonl)、[精确资源安排](measurement/raw_timing/resource_plan_aa.json)
- [RAW失败实际原始日志](../results/raw_aa_v3/raw-aa-01-F-A1.jsonl)、[派生停止汇总](../results/raw_aa_summary_v3/summary.json)、[实际重算命令及10输入/7派生哈希](measurement/raw_timing/aa_analysis_execution.json)
- [RAW完整时钟/真实退出独立复算](reviews/goal2_raw_aa_result_review.md)、[默认恢复后的最终代码审核](reviews/goal2_final_code_review.md)、[完整实验/报告独立审核](reviews/goal2_experiment_report_review.md)
- [S3有限重复设计及未执行结论](optimization_goal2.md)、[原文实际阅读范围](literature_goal2.md)
- [历史共同配置评分](../results/identity_quality_v2/summary.json)：不改旧秒数/旧判定，不把确认差当同配置选择差
- [固定版本重生成与干净复现](reproduction/goal2/)、[当前恢复源码全测试](commands/goal2_restored_integration.json)

原始时钟单位、调用顺序、目标/编译器/源码/二进制身份、stdout/stderr、实际退出及成本都保存在相应 JSONL 与 commands 目录。Linux探针、WindowsQPC核对仅支持有限区间的相对关系；[最终只读服务日志](measurement/formal_clock_drift/system_readonly_final.json)没有提供漂移根因或修正量。没有更改任何服务、时间设置或全局配置。

## 先前成果（保持不变）

[协议说明](protocol_v1.md) / [JSON](protocol_v1.json)、[原20配置完整60样本](../results/reference_v1/plan.json)、[先前三seed真实在线搜索](../results/selection_v1/plan.json)、[独立确认冲突诊断](../results/conflict_selection_v1/plan.json)、[先前三新seed](../results/holdout_v1/plan.json)。[原派生表](../results/summary/summary.json)及[原优化判定](optimization.md)按原方法留存；当前报告采用新的同身份解释，旧gap/近优标签不作为新可比性结论。

[原代码审核](reviews/code_review.md)、[原实验/报告审核](reviews/experiment_report_review.md)、[原正确性与实际环境](environment/initial_environment.txt)、[目标适配](environment/target_adaptation.diff)、[旧计时诊断](environment/timing_issue.md)、[原汇编](environment/kernel_assembly.txt)、[原文献](literature.md)、[原截图来源](commands/screenshots.json)均作为历史记录，不能冒称当前图片/计时器或本阶段终审。

固定提交3ac、2fc、c247的只读重生成分别见 reproduction/goal2/*-comparison.json；RAW停止采用匹配5c78049，详细命令见[README](../README.md)。所有新增输出写到新派生目录或忽略缓存，身份检查保留，不覆盖 raw。[最终三张安全终端截图](commands/screenshots_goal2.jsonl)与[六图SHA/内容/实际视觉记录](commands/images_goal2.json)已保存；旧不安全启动记录不删改。干净复现221/19通过、四冷构建通过，唯一大矩阵复现被原保护中止，见[实际检查](reproduction/goal2/clean-fresh-n4096-check.json)。RAW七派生及历史各版本数据实际重算见对应comparison；MONO停批十CSV全等、JSON仅中间分析源码身份差已说明。完整受控成本见[costs_goal2.json](measurement/costs_goal2.json)。
