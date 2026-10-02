# Goal 2 方法与分析交叉审核

审核者：原生子代理 `/root/implementation`。该角色是搜索核心作者，但不是方法、协议、实验编排或 `summarize_v2.py` 的作者；本记录不作为搜索核心的唯一审核，也不授予最终 Engineering PASS。

开始记录：2026-10-02 22:26:56 Asia/Shanghai。当前状态为 **ANALYSIS_REGRESSION_PASSED_PERFORMANCE_GATE_PENDING**：分析修订及独立回归已完成，真实诊断未达到正式准入，最终图片也尚未完成。主控发现并纠正了审核产物路径重叠，本角色现唯一拥有 `goal2_method_analysis_review.md/json`；另一审核角色的 `goal2_analysis_review.*` 保留，不覆盖。

## 实际阅读范围

- 老师 P1 PDF、原附件 C、本地完整 Goal 2 提示词、根 AGENTS.md、Goal 1 报告及旧框架/实验/汇总代码。
- `measurement/design.md`、`protocol_diagnostic.json`、`protocol_v2.md/json` 草案。
- 完整 `scripts/summarize_v2.py`、`tests/test_goal2_summary.py`；为核对委托边界，阅读 `experiment_v2.py` 的资源账本、身份/轨迹验证、协议检查与共同面板锁定路径，以及相应 driver fixtures。
- 作者的已有测试日志仅作为来源记录。主控独占诊断结束后，另给本审核者短窗口；本审核者实际执行 37 项分析 fixtures，并独立从 raw 重算关键输出。没有编译、绘图或启动 n4096。

## 已核实的设计与代码关系

相同返回配置按同一参照表映射质量；`gain_bounds(..., same_config=True)` 返回零，独立 A/A 保留两个标签各自的真实样本、中位数和有方向差值。二者用途不同，没有用身份合并去宣称环境稳定。

在线分析从 raw stdout 和实际 trial 顺序重放四个策略，S3 读取新鲜分数重建前缀、冻结候选、两样本聚合与资格。共同面板的依赖搜索先完成，锁定文件保存依赖 journal SHA，面板配置去重后使用三个新轮次；面板不回填在线历史。失败、缺样本、缺留出、未冻结规则或未知成本不能使候选保留。

协议将 5% 质量目标、2pp 风险限、10% 实际搜索时间收益分别固定，rho 仅为所测两个诊断档位的有限描述尺度。端点范围明确不是 CI；它们不能提供总体噪声界、总体假阳性率或跨机器无退化保证。现阶段正式协议仍是草案，真实诊断结果、rho、身份及两类审核未冻结，不能据此开始正式优化。

原始文献已由本审核者在线核对相关正文，不仅查看作者的摘要：2021 论文 §III-C/§VI-C 确认正态近似、默认两次与部分平台提高最低重复数的限制；项目没有实现或借用其 CI 保证。[原文](https://arxiv.org/pdf/2103.08716v2)

2024 论文 §3.2—3.4 确认需要说明预算、区分测量噪声与算法随机性、记录 wall 成本、注意非 iid 和早停展示；项目没有用该文计算的 Random 期望替代真实在线 Random，也没有对可上升的 S3 估计作单调回填。[原文](https://pure.uva.nl/ws/files/182730825/A_methodology_for_comparing_optimization_algorithms_for_auto-tuning.pdf)

2023 论文 §3.3/§4.3 的成本摊销依赖后续调用与编译/慢变体开销，项目未虚构后续调用次数。[原文](https://arxiv.org/pdf/2309.06414v1) 2026 补查的题名、作者、v1 日期及重复消耗固定预算的前言也经原始页面/正文核对，未因此引入其进化搜索、残差池或切换机制。[原文](https://arxiv.org/pdf/2606.06555v1) 本审核者没有声称逐页阅读全部论文或核实论文所有实验。

## 具体问题及闭环要求

| ID | 严重性 | 路径/位置（初审时） | 发现与影响 | 交回 owner / 必要复核 | 状态 |
| --- | --- | --- | --- | --- | --- |
| AS1 | 高 | `summarize_v2.py:628`，`cost_table` | 初稿缺原始 ns/真实调用交叉核对；第二次静态复核又发现有 raw 启动但成本整条缺失可误叫完整。 | 重算三域成本/逐 job 多 attempt；missing_jobs 阻止 complete，缺实际总数/上界时为 null。actual global start.journal 精确匹配处理 guard 无副本及部分副本恢复，仍严格核对现有副本/启动数，不写 raw。全部对应反例实际通过。 | CLOSED_REGRESSION；初始缺口没有导致已观察的真实成本错记 |
| AS2 | 高 | `summarize_v2.py:739`，`safe_destination` | 初稿只保护传入 raw，遗漏历史/其他 raw 根。 | 同时保护传入目录及解析路径的所有 `plan.json` 祖先；未传入 raw 反例实际通过，clocks 输入也受输出保护。 | CLOSED_REGRESSION；未实际写入任何 raw |
| AS3 | 中 | `summarize_v2.py:748`，`plot_results` 的 progress 图 | 初稿未标 S3 provisional 最优切换为成功复核资格集合，曲线可上升。 | 修订版 `plot_results:878` 使用累计 measurement_start 作为实际调用横轴；S3 虚线、复核三角点及标题说明资格更新与上升。正式图片仍须实际打开。 | STATIC_FIX_VISUAL_PENDING |
| AS4 | 中 | `experiment_v2.py:298`，`validate_task`；`summarize_v2.py:270`，`read_batch` | 初稿合法失败 summary 无法派生失败样本/成本表，不会错误 KEEP，但交接可能缺失败明细。 | 合法失败分支核对冻结 job metadata/fingerprint、driver 轨迹与独立原始重放后保持 failed；无 summary 的真实 interrupted 保持 partial。失败保留/伪造 metadata 反例与真实 partial 派生均通过，未修改冻结 driver。 | CLOSED_REGRESSION |
| AS5 | 高 | `summarize_v2.py`，`paired_rows` 的 `run_index` 与面板索引 | 初稿不同目录同真实身份可被静默覆盖，形成挑选批次风险。 | 拒重复 stage/algorithm/seed 及 stage/block/config；不同 batch 的搜索/面板重复身份反例实际通过。 | CLOSED_REGRESSION；没有证据表明发生过重跑挑选 |

以上问题通过代理消息交给原作者和主控，本审核者没有修改其文件。修复后完整读实际改动，并在非阻塞全局 flock 下执行相关全部 37 项 fixtures：2026-10-02 15:22:52 UTC，退出 0，suite 0.011 秒、包含启动/导入的 MONOTONIC 0.095770353 秒。实际命令为 `python3 -B -m unittest discover -s P1/tests -p test_goal2_summary.py -v`；日志见 [goal2_method_analysis_tests.log](../commands/goal2_method_analysis_tests.log)。分析源码 SHA 为 `96352437a0e9b76e3ccd709d048736721a0e7359ad238fdef89033aff9ad624f`，测试 SHA 为 `421acfa96fbd46ead6bcf5bce89ef34cae401a04f190144a5b4490c864c0f3d7`，执行前后 unchanged。

AS4 涉及已经冻结并开始诊断的 driver。不在运行中更换其 bytes；若后来改 driver，旧诊断需由匹配固定提交/源码只读重算，不得改旧 plan/hash。

## 真实中断诊断的独立重算

2026-10-02 15:24:52 UTC，在全局性能锁下直接读 JSON/原始 stdout/ns 重算，没有调用待审分析函数来替代独立算术。107 个诊断/时钟 raw 文件前后 SHA 不变。28 个普通计划任务实启 27 次：26 个有效样本（22 个独立 A/A、4 个锚点），1 个 interrupted，最后 `diagnostic-b4-06-F-A3` 未启动；另有两个内核诊断，总 n4096 调用 29 次。global 40 个唯一 attempt 的成本逐项从原始三域边界重算，MONOTONIC driver 合计 2053.667427729 秒、max 域资源合计 2057.203209297 秒，与派生账一致。

| 安排/档位 | A 有效数 | B 有效数 | A 中位数(s) | B 中位数(s) | 有方向标签差(%) | 完整 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M0/F | 2 | 3 | 60.1812005 | 58.235882 | -3.2324355 | 否 |
| M0/M | 3 | 2 | 86.904335 | 84.6577495 | -2.5851248 | 否 |
| M1/F | 3 | 3 | 55.668694 | 56.695389 | +1.8442951 | 是 |
| M1/M | 3 | 3 | 84.139397 | 84.750038 | +0.7257492 | 是 |

两个 M0 单元未完成，不能由上述较小 M1 标签差断言安排胜出。派生输出准确保留 `arrangement=null`、`resolution_pp=null`、`performance_gate=false`，未填入 rho 或追认原计划连续完成。中断的完整进程/driver 三域成本和实际调用已知，内核时间 null；未用 CPU 时间替代等待时间。

补读 [clock_followup_design.md](../measurement/clock_followup_design.md)：这一次十二调用区分短前缀 q 与完整同来源 q，阈值仍 2%，有限诊断 flag 例外不成为正式准入。支持执行设计等待独立代码审核，**不批准正式性能实验**。补 M0 两标签包含 guard 后文档/测试中断，打断原连续平衡顺序；需分列未补齐、补齐与四对新 A/A，不能因标签差缩小宣称 M1 降低总体方差。

## 十二调用追加诊断的代码交叉复核

2026-10-02 15:52:38 UTC，完整只读检查 `clock_followup.py`、其十二项 fixtures、`experiment_v2.py` 相对初始 checkpoint 的 observer 差异和追加协议草案。本审核者没有在该阶段执行测试、编译、绘图或 n4096；另一审核者持有短测试窗口，代码 gate 及实际回归见 [goal2_followup_code_review.json](goal2_followup_code_review.json)。本方法意见仅支持冻结后这一次十二调用诊断，不批准正式成绩实验。

`Observer.validate` 将例外限制在 approved、formal_admission=false、十二项冻结列表中的精确 job/command、call_upper=1 和新 trace。普通 `controlled` 调用仍执行原 2% 前缀守护；没有把例外放进正式 CLI。完整 driver、正式目标进程和独立诊断内核使用各自来源的首个/前一个完整区间，失败、中断、unknown 和异 boot 不进入完整基准；局部两秒比例仅为时钟时间线，不能计作新增矩阵重复。ns 原始起止和单位可重算，CPU 时间保留用途区别，未用 RAW 替换正式秒数。

只读 `QUERY` 的零初始化使 modes=0；offset 的单位由 STA_NANO 指示，tick/precision 为微秒，frequency_scaled_ppm 保留原始 16 位小数 ppm。它没有设置时间参数；这些字段的变化也不能单独证明本机根因。[Linux adjtimex 手册](https://man7.org/linux/man-pages/man2/adjtimex.2.html) MONOTONIC 可受渐进调整，RAW 的接口语义不赋予其虚拟环境中绝对真值地位。[Linux clock_gettime 手册](https://man7.org/linux/man-pages/man3/clock_gettime.3.html)

| ID | 严重性 | 位置 | 发现、修复与复核 | 状态 |
| --- | --- | --- | --- | --- |
| CF1 | 中 | `clock_followup.py:201`，`completed_job` | 最初只重算 ns/ratio 并检查 readonly 标记，单改 timex 内容或 sample phase/task 仍可能被称为未变 raw。该风险没有发生于真实数据。owner 在完成 trace append 后将整份 SHA 写入 global end，恢复核对规范路径/SHA 并继续独立重算；反例覆盖 phase、timex、重填 hash 后仍不一致的比例。 | CLOSED：本角色静态复核，另一审核者在实际锁内复测最终十二 fixtures，0 失败；不计入本角色的 37 项执行数 |

最终复核源码 SHA：`clock_followup.py=6c0283cbba357ff7027091ad1ed2f157d2b7ad17443da150694654a576c00221`，`experiment_v2.py=7fa4c97cac4b749ef249489d909cb79f7c8021f6bdfc1e5e1ea486c2ead5e439`；fixtures SHA `d2c2f1f21dc41d882c4f7772467f2aa31dbcef092892281d40d1277b9a80181d`。追加协议当时仍是 draft，SHA `ea1984ec01549b15188c9de4b02b68cdc905821233246a761aa4e2186db642bd`；冻结后执行必须记录新协议 SHA。

独立逐文件比对初始 checkpoint `2fc0c334039bb6696c4d83acbe029ce65ca66ab9`：初始普通 raw、初始派生表、原诊断协议、clocks 证据共 115 个跟踪文件字节不变。global ledger 原前缀字节不变，只新增 read-only query 构建的 start/process/end 三条，其 n4096 调用为 0；该构建已知成本另计。当前源码的修改不迁移初始 batch identity，初始数据仍用该匹配 checkpoint 重生成。

即使十二次只发现短前缀超限，正式改成 complete-versus-complete 仍需另行审查最小语义修订、新协议与源码冻结，2% 不放宽；若任何完整同来源比例超限，不能由末次较稳或最后几对 A/A 放行正式实验。补齐的两个 M0 标签仍明确含中断间隔，不能恢复为原连续安排或宣称因果方差收益。

## 当前完整报告与入口的连续阅读意见

该阶段连续读完整 `report.md` 与 `README.md`，没有以禁用词搜索替代阅读。正文保留老师 1—4 顺序、目标/参数与完整旧结果，仍待主控在新数据形成后更新。以下意见已交 owner，本角色不改正文：

| ID | 位置（此次阅读时） | 需要的修改 | 状态 |
| --- | --- | --- | --- |
| CR1 | `README.md:28–37` | 旧 raw 的当前 HEAD 汇总命令在 core SHA 已变后不能直接重现。Goal 1 分析须用固定受审 `3ac0c4688b964c873379d012cbcf09afb7ed0937` 的只读 checkout；初始诊断另用 `2fc0c334…`，新派生用本阶段脚本/输出。不要放宽旧哈希。 | owner 已确认，交付前待修复/实际干净复现 |
| CR2 | `report.md:36,111–131,148` | 恢复细节移到 evidence；旧分层/patience 的五段与留出表缩为无确认收益及必要原因，并链接历史证据；截图读取/未回填等重复说明集中为一处短图注。 | 建议待最终正文修订/连续重读 |
| CR3 | `report.md:76,87–107,127` | 内部批次名称改简短来源链接；同配置的选择质量用共同表身份映射，时段确认独立列；旧 0/3 等混合判定保留为历史结果，不作为新种子结论。 | 新成绩尚未产生，待真实新数据后修订 |
| CR4 | `report.md:27–34` | 该代码片段仅适用于三基础算法；如果新正文纳入 S3，说明其评价路径内部 observe(fresh_score)，不能把聚合 score 再 observe 一次。 | owner 修订时需保持与最终代码一致 |

## 尚需完成

1. AS1/AS2/AS4/AS5 已经独立回归关闭；AS3 的最终图片实际查看仍待完成。
2. 原 A/A partial 已独立重算；有限补诊断后仍须核对完整同来源钟域、M0/M1 与可用 rho，再审核正式协议冻结值及收益门可达性。
3. 正式数据产生后，独立重算 20 配置、六块算法/共同面板、S3 配对、必要确认及全部成本；连续阅读最终 report/README，逐图真实查看。这里的静态审核不代替这些工作，后续产物单独使用 `goal2_experiment_report_review.*`。
