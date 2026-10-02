# Goal 2 方法与分析交叉审核

审核者：原生子代理 `/root/implementation`。该角色是搜索核心作者，但不是方法、协议、实验编排或 `summarize_v2.py` 的作者；本记录不作为搜索核心的唯一审核，也不授予最终 Engineering PASS。

开始记录：2026-10-02 22:26:56 Asia/Shanghai。当前状态为 **METHOD_ANALYSIS_CODE_GATE_REVIEWED_PROTOCOL_FREEZE_AND_REAL_EXPERIMENTS_PENDING**：联合分析、完整指定快照面板路径、无效搜索分类及两项数值时钟身份分别完成实际独立回归；测试目录/历史前缀的小修也完成独立相关回归。主控总回归有 174+4 项通过的实际日志，源码分析关可供精确协议冻结后准入有约束的粗粒度比较；正式数据、干净复现与最终图片仍待审核。主控发现并纠正了审核产物路径重叠，本角色现唯一拥有 `goal2_method_analysis_review.md/json`；另一审核角色的 `goal2_analysis_review.*` 保留，不覆盖。

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

## 追加诊断运行期间的新分析静态复核

2026-10-02 16:18:39 UTC，主控已启动冻结 checkpoint `09afaea660f5f9a62ddacd72dcca35b98f17dd1b` 的十二调用补诊断，持有全局性能锁。本角色只读源码、fixtures 与正文并写本审核记录；未执行测试/编译/图形命令。这里新增的第 38 项分析 fixture 尚未由本角色实际运行，不能沿用前面 37 项的通过状态。

新分析 SHA `5bebe99ecc4308eae8b70a5db51f0151920ee06ac6212fade31c22d0fb55de9b`，fixtures SHA `cc2899600152a850f621849f0a5767af264db88a5b7a2c402ee3e252f6ac78aa`。`search_tables:457` 仅在返回配置和共同参照配置的 panel 都完整时才生成确认范围；same-ref 的参照质量仍为零，但缺 panel 样本时 `quality_class=uncertain`、`confirmation_complete=false`。`panel_table:376` 检查三轮为 1、2、3；`baseline_confirmation:1072` 同时要求所有预定 seed 的搜索与共同确认完成。基础确认的 complete 表示样本收集完整，不能把 uncertain 分类解释为已证明近优。

| ID | 性质/位置 | 检查结论与交回建议 | 状态 |
| --- | --- | --- | --- |
| AS6 | 边界回归范围，`test_goal2_summary.py:211` | 新 fixture 覆盖 same-ref 仅 1/3 panel 的反例，静态逻辑正确。建议同一边界用例补 missing-reference-anchor、重复 round=(1,1,3)、所有基础搜索完成但 panel 未完成，分别核 `uncertain`/panel.complete=false/baseline.complete=false。没有发现这些路径已错误分类的证据。 | 设计建议/实际回归待授权窗口 |
| AS7 | 中，`summarize_v2.py:1025,1035` | ledger SHA 在 main 中先读取文件，cost_table 随后另读一次。若中间有实际 append，摘要的 SHA 可能不是计算那些行的快照；当前没有已发生错误证据。建议一次 bytes 读取同时 hash/parse，或前后 SHA 不变才写 summary；clock identity 也应对应实际采用的身份。 | 已交方法 owner，修复/反例待复核 |

正式完整 clock conflict 的后续语义仍待主控设计和实测。应将测量可用性与实际成本已知分开：即使目标返回 0、summary 齐全、调用数和 driver 成本已知，只要正式完整同来源 clock 检查冲突或必需字段缺失，仍不能 KEEP。diagnostic-only 的允许继续 flag 单列；不因它出现就抹去真实已知成本，也不让它伪装成正式成绩。成本 complete 不能充当 measurement health；只有匹配新冻结源码/协议的真实完整检查能够通过该关口。

完整 report/README 与上一阅读 SHA 相同。已交主控的四项新增实质建议：

1. 三基础算法用六块的分布表展示近优/较差/不确定、返回配置分布、实际调用和 driver 中位数/范围，链接逐轮 CSV，并保留具体严重失败例。
2. Greedy 起点面板单列起点、路径/返回、停止原因和实际成本，不并入随机主实验 seed 数；用起点位置解释局部停止。
3. 主算法成本包含其真实搜索与内部复核；共同外部面板去重后单列实际一份成本，不能对每算法复制“搜索+三个确认”的项目总账。
4. 数值段保留小矩阵全元素/尾块与 sanitizer、大 n 抽查两层结论、容差和大 n 非全量限制；细分用例数/最大误差链接 evidence，正文突出配置与算法结果。

这些建议没有替代实际新成绩，也没有改动主控所有的报告或其他作者文件。

## 联合诊断的实际独立回归与重算

2026-10-02 16:37:28 UTC，在实际非阻塞全局 flock 下执行 `python3 -B -m unittest discover -s P1/tests -p test_goal2_summary.py -v`：43 项、0 failure/error，suite 0.014 秒，包含启动/导入的 MONOTONIC 0.115480693 秒。源码 `f1797c96a5d4e23a5bc5874f5911d3a8ac158846464bd936e498bcaedf8a8e43`、fixtures `e2818f35365c88c19d6c22332b0cb0688b8b7c3e0d1fea1b2d3c2f16b7235bf2` 前后不变。AS6 的缺锚点、重复 round 和基础确认未完成边界实际通过；AS7 的单次 bytes hash/parse 及文件随后 append 反例通过，均关闭。此前 37 项是旧分析阶段的执行记录，不能与这些重叠 fixtures 相加为 80 个不同测试。

16:47:32 UTC，另持锁直接读原始 JSON/stdout/ns 与固定 Git bytes 独立计算，没有导入作者分析函数。固定 `2fc0c334…` 的 32 个声明输入均与 Git 和哈希一致，匹配旧脚本 SHA 及两个实际重生派生文件 SHA 也一致。实际追加目录为 `results/clock_followup_v2_r1`、协议为 `protocol_clock_followup_r1.json`；旧无样本的初次目录不作为新数据。159 个所读 raw/协议/账本/声明文件前后哈希不变，原账本为当前账本的字节前缀。

| 部分 | 实际独立复核结果 |
| --- | --- |
| 初始普通矩阵 | 26 有效（22 A/A、4 anchor），1 interrupted，1 原计划未启动 |
| 初始内核诊断 | 2 有效，另计 |
| 追加有限批次 | 10 正式构建诊断样本、2 多时钟内核样本，全 12 完成 |
| 项目总账（复核时刻） | 57 唯一 attempt、41 n4096；MONOTONIC driver 2743.599047428 秒，逐任务 max 域资源 2755.910424768 秒；失败/预检/历史分析计入 |
| 完整同来源区间 | 80 个 driver/process/kernel 区间，分别 first/previous、同 boot 重算，0 个 >2% 冲突 |
| 追加 timeline | 360 个 start/约两秒/end 原始点、各自整份 SHA；新 prefix flag 为 0 |

成本和时钟的实际重算与作者联合输出一致。没有由新任务 counterfactual 地证明原 interrupted 程序会稳定结束；没有把 CPU 时间或 RAW 比例用于校准旧秒数。该阶段仍由成本已知和计算正确性分别判定，内核无效的原中断样本没有变成有效值。

| 独立 A/A | A 中位数(s) | B 中位数(s) | 标签有方向差(%) | 两对/三对有方向差(%) |
| --- | ---: | ---: | ---: | --- |
| 新 F | 39.054176 | 38.2221985 | -2.1303164 | +0.7388658，-4.6112186 |
| 新 M | 74.795742 | 83.716763 | +11.9271776 | +24.3516542，+1.5125433 |
| 含补标签的 M0/F | 58.778687 | 58.235882 | -0.9234725 | +3.5193216，-5.4362295，+46.9765216 |
| 含补标签的 M0/M | 86.904335 | 83.758797 | -3.6195410 | +0.9323079，-12.2102009，-25.0296536 |

M1 的原完整样本 D=1.8442951、P=13.7846047，按预定规则得到 rho=14；含更长补测间隔的 M0 为 D=3.6195410、P=46.9765216。独立新 M 一对 +24.35% 已超过 rho，rho **不是噪声上界、总体误判界或 5% 分辨保证**；不能将补 M0 的大差值解释为测量安排本身因果降低方差。新两档仍维持 F 快于 M：按新 A/B 标签及配对中位数的差距分别为 91.52%、119.03%、110.49%、100.36%；原 M1 的对应排序检查差距约 44.68%—57.75%。这些支持区分大的档位差，不支持细排序。

实际测试/重算日志：[goal2_joint_independent_tests.log](../commands/goal2_joint_independent_tests.log)。只读重算第一次选择了没有实际样本的旧 plan 路径，按真实 CLI 定位 r1 后更正；没有因此重跑矩阵、改 raw 或改作者结果。

交还测试窗口后，主控追加一个实际截图工具测试的 0-call task：原始三域边界分别得 MONOTONIC 2.756714590 秒、资源 max 2.757842945 秒。主控在锁内重生联合派生，保留方法值/raw，更新成本快照至 ledger SHA `a59afd3fd4f1f46bcf148927589cd0e6197b263feeaa89c3ac1ba8e8b3386542`、summary SHA `5c446acce299d85d7bc13ea3d43df921263bca30636462c9ab828775f40d1a53`。这是合法追加成本，以上独立重算数值注明复核时刻；不能把它说成初始原始记录变动。

### 新正式方法的边界意见

独立原始证据支持继续新完整参照、三基础算法和 S3 的**粗粒度描述及真实成本比较设计**，但本记录不直接放行测量。正式前须实现并审核完整 process/full-driver 同来源守护，固定新源码/协议；原 2% 钟域门、5% 近优目标、2pp 风险限、10% 成本收益均不放宽。相同身份的配置选择质量差为零；不同身份且风险分辨不足者保留 uncertain/INCONCLUSIVE，不以 rho=14 提供总体非劣保证。

16:47 阶段提出 AS8 高优先级前置依赖：当时联合分析对 r1 有整份 trace 与 ns 的严格重算；普通 main 的 `not any(row.get('clock_conflict'))` 还会把缺字段看作健康，且按 task 标签选事件。正式新 schema 必须按实际 attempt/journal 核对每个必需完整区间、单位、调用和检查字段，缺失/冲突均不可 KEEP。已交 root/方法作者，作者认可须等 root 的明确字段契约后最小同步严格 reader；不能用 known-cost 或 rc=0/完整 summary 替代健康检查。该时刻没有实现/回归依据；17:29 的直接任务修订与仍待关闭的流程缺口见后文。

## 尚需完成

1. AS1/AS2/AS4/AS5/AS6/AS7/CF1 已关闭；AS3 的最终图片实际查看仍待完成。
2. 原 A/A partial、有限补诊断、完整同来源钟域与 M0/M1 描述已独立复算。AS8/AS9/AS10/AS11/AS12 均有独立回归，AS13 的 fixture 小修待主控最终/干净复现；冻结协议与 rho=14 的有限范围及不足以承诺 5% 分辨必须保留。
3. 正式数据产生后，独立重算 20 配置、六块算法/共同面板、S3 配对、必要确认及全部成本；连续阅读最终 report/README，逐图真实查看。这里的静态审核不代替这些工作，后续产物单独使用 `goal2_experiment_report_review.*`。


## 正式完整区间 reader 的独立回归（53 项）

2026-10-02 17:29:21 UTC，在真实 `P1/.cache/performance.lock` 非阻塞独占锁内独立执行 `/usr/bin/python3 -B -m unittest discover -s P1/tests -p test_goal2_summary.py -v`：53 项、0 failure/error，suite 0.026 秒；包含启动/导入的 MONOTONIC 0.093530103 秒、RAW 0.095111867 秒、REALTIME 0.093531528 秒。分析源码 SHA `7132888f230ef504fcd6d300a0390d906c920428a8c16f5288eca1bf553f8cbd`、fixtures SHA `f06a30eb44293c2ee3b8fe8519489a6afe6b7600b0e144688780992cf67f36ef`、driver SHA `138fad8839d7df5dde25eaeb11c255b9b45582e9121399194d71a5ef11b285fb` 均在执行前后不变。独立日志见 [goal2_formal_analysis_independent_tests.log](../commands/goal2_formal_analysis_independent_tests.log)。运行锁已明确交还主控，之后本角色仅阅读/编辑自己的文本记录，没有编译、绘图、GUI 或 n4096。

本段为合成 fixtures 的代码回归，不是新增正式测量。53 项与此前 37/43 项有重叠，不能相加为不同测试数。目录扫描仍含 A1、A2、P1 与老师材料；本角色未修改其他作业或安装依赖。

静态逐行核对 `formal_clock_health:872–1042` 与实际 driver 字段契约：clock_spans 只接收恰好三个整数 ns 域（bool/float 不算 int），按物理 run/trial/repeat/PID、attempt 起止和 journal 精确归属重算完整时长、q、首个/前一个同 boot 基准及保存检查。每个目标进程单独判定，不用整个 driver 平均掩盖单进程冲突；失败整个 attempt 不进入以后基准。已知成本与测量健康分开，missing guard、unknown 或未覆盖物理启动不能使样本有效或通过 KEEP；直接任务读入先做冻结 metadata/轨迹/在线重放，再由一次读取的指定 ledger 决定健康。`main:1512–1519` 将 clock_conflict/unverified 状态传给有效样本计数；`decision:1093,1099` 分别阻挡时钟无效以及缺不同身份风险分辨依据的候选。相同返回身份的选择质量严格为 0，10% 实际 driver 节省路线的边界 fixtures 可达，缺三个新留出则不能保留。

上述 AS8 的直接任务/schema 路径获得独立回归依据；**完整分析流程仍因以下两项被阻断**，没有把“53 PASS”写成全部面板链通过：

| ID | 严重性/路径（该测试版本） | 具体缺口 | 修复与复核要求 | 状态 |
| --- | --- | --- | --- | --- |
| AS9（另一审核角色 S4） | 高，`summarize_v2.read_batch:331` → `experiment_v2.panel:765,774` → `validate_task:524` / `reference_best:748` | 保存的共同面板仍由 runtime `panel`/`reference_best` 重建，间接读取实时 `ex.LEDGER`。53 项的禁止 runtime mock 仅覆盖直接 task，未覆盖真实 panel/reference 入口，因此指定快照尚未贯穿整个流程。 | 分析侧只读重建完整 20×3 参照、锁定依赖返回、去重及三轮顺序/指纹，不调用 runtime 恢复/实时 ledger；新增保存面板+真实参照且 runtime 入口抛错仍可分析的 fixture，再独立回归。 | OPEN；作者已确认，暂停正式 gate |
| AS10 | 高，`summarize_v2.search_tables:502–524` | clock_conflict 搜索的 summary.best 仍参与 `classify`；若健康完整参照和共同面板存在，同 identity gap=0 可令这次无效搜索被标 near_optimal_observed。样本有效数及 KEEP 已挡住，但近优标记仍违背本关约束。 | 可保留返回身份/g_ref 的描述，非 complete 搜索不能有近优/有效确认分类；新增无效 clock 搜索+完整健康参照/面板的反例。 | OPEN_STATIC；已交作者，未跑新反例 |

这些是代码路径缺口，没有证据表明尚未开始的正式结果已经被错判。不同身份的 2pp 风险分辨不足仍固定为 INCONCLUSIVE；原 2%/5%/2pp/10% 均未放宽。候选是否保留仍须真实六块主比较、必要三个新种子确认及原始成本/质量审核，合成边界通过不授予实际性能 KEEP。


## 完整面板与数值时钟范围的独立复核（59 项）

2026-10-02 18:01:40 UTC，主控授权后在真实全局性能锁内独立执行上述分析测试命令：59 项、0 failure/error，suite 0.345 秒；另外实际 `py_compile` 分析、测试与 driver 三个源文件，退出 0，输出 pyc 仅在忽略缓存。分析 SHA `3e528fe3fcf6e7c3e185800816483ffe4a40229d9557d4d92cdac170e89f1cfb`、测试 SHA `044eac327e7874e926638717896fdfb2f8ac66c3c47ffcb9beed9d57d186fb8b`、driver SHA `b1b5028c29236788796bfad5059fa35cd34a65566a89d6f73eb100cb502ac23f` 执行前后不变。

该检查经实际 `controlled` 记入 primary ledger：task `goal2-formal-panel-independent-59`，attempt `3cd71d353fc9427fb6916d7d498b0403`，0 n4096、退出 0，MONOTONIC driver 0.505287850 秒，逐任务 max 域 0.516258607 秒。日志见 [goal2_formal_panel_independent_tests.log](../commands/goal2_formal_panel_independent_tests.log)，窗口结束立即交还。以下静态审查/只读算术没有另跑目标、编译、测试或图形程序。

| 项目 | 本审核者具体复核及实际证据 | 状态 |
| --- | --- | --- |
| AS8/AS9（S4） | 连续阅读 `locked_panel:316–353`、`read_batch:356–419`。所有同块搜索依赖按计划顺序先核 metadata/轨迹/原始返回，再核整个保存面板的依赖 journal SHA、参照 plan SHA、配置集合、三轮平衡访问及指纹。分析不再调用 runtime `panel/reference_best/validate_task`。一个实际存盘的 60 个合成参照样本、1 搜索、3 共同面板样本走完整 CLI，三条 runtime 入口设为抛错仍通过，指定 ledger SHA 与实际使用快照一致；多个保存字段伪造和缺参照轮数反例被拒。64 是该 fixture 的样本数，不是本机新增矩阵运行数。 | CLOSED_INDEPENDENT_SCHEMA_AND_CLI_REGRESSION |
| AS10 | `search_tables:568–581` 仅对 complete 搜索作近优/确认分类。坏 clock 搜索+完整健康参照和面板反例保留返回身份及描述 g_ref=0，但 quality_class=uncertain、point_near=null、confirmation_complete=false；panel_complete 单列为 true。在线 CSV 保留原始轨迹和状态，图只纳入有效轨迹。 | CLOSED_INDEPENDENT_REGRESSION；最终图仍待实际看 |
| AS11（实际协议路径） | `read_batch:360–365` 从实际 CLI 路径解析 P1 相对位置，先与 plan.protocol 比较，不再把计划中的 protocol 值注入期望后自比。只改 manifest.protocol 的反例实际被拒。 | CLOSED_INDEPENDENT_PROTOCOL_PATH_REGRESSION |
| AS12（数值适配只供时钟） | 连续阅读 `numeric_clock_baseline:928–987` 与 `formal_clock_health:1053`，仅允许声明绑定的 O0/s24 和 O3/s128 两个已发生的 numerical job，严格核对唯一 attempt/role/命令、journal SHA、原源/适配源码/六层 kernel hash、编译器/附加校验链接参数、24 元素 CHECK。它们仅在非 owned 历史提供 clock；owned 正式分数遇适配目标仍拒绝。实际两项 raw 的 role/task/attempt 或 CHECK count 伪造、缺声明反例通过；与全部先前健康 history 的后续合成 task 只有一份原正式目标 scoring sample。 | CLOSED_INDEPENDENT_NUMERIC_SCOPE_REGRESSION_AND_RAW_RECOUNT |

18:06:13 UTC，从一次 ledger bytes 快照和原始 journal 独立重算，没有导入作者函数。39 个所读 identity/raw 文件前后哈希不变；snapshot SHA `c4b4ae3fed2c689d6bc8278b75bb1c2bcf6fba6f500239731650e5e07df1d683`。两项数值实际原始 CHECK 都为 count=24、failures=0，max_abs=2.937539e-12、max_rel=2.814528e-15（绝对/相对混合容差）；这是抽查，不是全矩阵验证。完整进程与 driver 三域 ns、q、首个/前一个同 boot 的实际 identity 与保存 guard 一致：

| 配置（数值检查） | 进程 MONOTONIC(s) | 进程 RAW(s) | 进程 REALTIME(s) | 进程 q | driver MONOTONIC(s) | driver q |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| s24/O0 | 225.600983835 | 229.561414750 | 229.547167149 | 1.0175550250 | 225.843456469 | 1.0175543829 |
| s128/O3 | 40.114005628 | 40.818841643 | 40.711662383 | 1.0175708211 | 40.571010017 | 1.0175726206 |

这两条不进参照、搜索或确认分数，也没有因本审核再调用矩阵。原始每域秒数保留，没有按比率校准 MONOTONIC。

### 仅测试复现的小修及状态界限

独立 59 对应 `044eac…`，其 numeric 正例使用 `TemporaryDirectory(dir=P1/.cache)` 前未创建缓存目录；Git 不跟踪 `.cache`，当前工作区存在不代表干净 clone 可运行。作者随后加入测试局部的 `(P1 / '.cache').mkdir(exist_ok=True)`，并实际再次 59/59、py_compile 0，测试 SHA `d92fc6a530de3eef7b2b9a693041a0c74b2b75384f4fecf09a3d49085733fe9b`，该次属于作者回归。

另外，正例读取增长的完整总账却固定以最后 numeric 为 previous，未来正式 attempt 加入会使 fixture 的预设 previous 过期。作者随后将测试 ledger 固定为 `ledger[:ledger.index(last) + 1]`，本审核者纯读确认两行合理；最新测试 SHA `32826fa75cd3eaa25e1a7c680da822ed3a69f99b494cb94165efd1c90bccf41d`。生产分析/driver 不变，raw 不变；**没有把旧独立 59 移记到这个新测试 SHA**。AS13 为低影响测试复现项，主控已接管一次全套真实回归与后续干净 clone 流程，本角色没有再次抢锁重复 59，也没有声称已在干净 clone 跑过。

当前生产分析代码的 AS8–AS12 缺口已关闭，可供主控完成全套回归、匹配代码/协议冻结后进入有约束的粗粒度比较。different_identity_risk_supported=false 保持；任一不同返回身份的候选风险结论仍 INCONCLUSIVE。同身份质量 0 的实际效率路线仍须六块与三个新留出、实际成本、独立实验审核。此代码意见不等于正式成绩完成、实际候选 KEEP 或最终 Engineering PASS。


### 最后 fixture 的实际独立相关回归与关口结论

2026-10-02 18:10:14 UTC，经主控单独授权，在真实全局 flock 下仅执行 `test_goal2_summary.Goal2FormalClockTests.test_numeric_baselines_match_runtime_history_and_never_enter_score_samples`：1 项通过，suite 0.010 秒。分析 `3e528fe3…`、最终测试 `32826fa7…`、driver `b1b5028c…` 三个完整 SHA 与上一段静态身份一致，执行前后不变；没有再次重复完整 59。primary ledger 实记 task `goal2-numeric-fixture-independent-final`、attempt `10b40859670948f7ae6b126422640863`、0 n4096、退出 0，MONOTONIC 0.265324297 秒、max 域 0.269485125 秒。日志追加到同一独立面板测试日志，锁已交还主控。AS13 的两行 fixture 修补获得独立相关回归依据，clean clone 尚待最终真实复现。

本审核者另实际读取主控总回归原始输出：`goal2-all-nongui-tests.stderr.txt` 为 174 项、11.514 秒、OK；`goal2-all-native-screenshot-tests.stderr.txt` 为 4 项、2.685 秒、OK；作者最终 fixture 原始输出为 1 项、0.010 秒、OK。16 个 Python 语法检查由主控报告退出 0；这些实际执行角色仍标为主控/作者，没有冒充本角色独立跑了 178。

**方法/分析生产代码关口的意见：已审、未发现仍开放的 AS8–AS12 依赖；允许在主控完成精确协议/源码冻结后进入所述粗粒度真实比较。** 签名身份为分析 `3e528fe3fcf6e7c3e185800816483ffe4a40229d9557d4d92cdac170e89f1cfb`、最终分析测试 `32826fa75cd3eaa25e1a7c680da822ed3a69f99b494cb94165efd1c90bccf41d`、driver `b1b5028c29236788796bfad5059fa35cd34a65566a89d6f73eb100cb502ac23f`。协议状态仍待冻结；改变影响测量的这些身份需重新检查相关关口。不同配置身份风险支持 flag 保持 false，5%/2pp/10% 标准不放宽，真实实验最终判定、全部图片和干净复现另审。没有授予整个阶段/项目最终 Engineering PASS。
