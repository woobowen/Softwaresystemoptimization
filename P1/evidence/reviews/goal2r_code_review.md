# Goal 2R 实现与原始证据独立审核

审核角色：`/root/reviewer`。本文件只记录实现、预算、生命周期及原始证据检查，不赋予最终 Engineering PASS。执行前的实际代码、完整数值与初始计时证据已复核，可在下述冻结条件下开展正式测量；正式实测及成品仍待复核。

## 已读材料与旧账复算

已完整读取实际根目录 AGENTS、Goal2R 提示词、老师 P1 PDF 的全部一页、老师 C 与两份目标 C、完整 report/README、autotuner、experiment_v2、summarize_v2、identity_quality、validate_target、host_clock_probe、clock_diagnostics、clock_followup、阶段交接/闭环/优化/协议和最新代码、结果、图片、发布审核。老师要求的 20 配置、六层计算循环及尾块仍保持；此次不操作其他作业或水杉。

使用独立 Decimal 算术逐条检查原 `measurement/resource_ledger.jsonl` 的 494 行：165 个唯一 task_start/task_end 全闭合，48 次 n4096，逐任务原三域最大值费用合计 **3713.432874365 秒**。不能把原费用换算为新 RAW 或重置预算。该轻量检查为 0 次矩阵/编译，RAW 受控耗时 0.009788893 秒，已交主控计账。

已从原始整数与 stdout 独立读取 RAW A/A 首项：C/CLI 退出 0、checksum=17180040496.458935、内核 RAW=40.539898 秒、进程 RAW=41.257334530 秒、REALTIME=40.960162684 秒。这说明数学/运行结果存在，原停止判定仍原样保存；辅助域关系变化不能自动证明 RAW 无效。

## 执行前需修正的实现问题

| 问题 | 实际代码依据 | 新路径要求 |
| --- | --- | --- |
| 正确性被性能前缀 guard 终止 | controlled 无诊断/完整 guard 时回落到 10 秒 RAW/MONO 历史比值硬门 | correctness 保留超时/资源/PID/输出安全，辅助比值只记诊断 |
| QPC 桥仍把辅助异常当主域失败 | sample 对所有 CLOCKS 判倒退；interval 用三域最大端点及所有宽度控制 usable | RAW/QPC 独立有效性；MONO/REALTIME 异常保留字段，不丢原整数 |
| 原分析拒绝所有不同身份 | decision 在实际退化/收益判断前读取 different_identity_risk_supported=false | 每个实际配对检查完整 G 样本，KEEP/REJECT/INC 分支真实可达 |
| 构建身份含 60/60.0 与非代码生成信息 | build 对完整 metadata fingerprint | 新构建身份仅源码/编译器/flags，恢复仍核对完整运行设置 |
| 共享面板过度包含基础算法 | panel 纳入全部四算法返回 | 等四搜索锁定，只测 Random/S3/参照身份并集，实际调用单计 |
| 原资源验证拒绝任一辅助负差 | elapsed/resource_span/validate_trace | 新记录明确 RAW 账 schema/basis；旧 max 账保持，不凭辅助跳变添几小时或记零 |

上述问题已发给文件 owner。新实现完成后，审核者将重新读取真实 diff、运行独立轻量反例并复核正式原始数据。实现测试成功本身不等于 T1/T2 与正式实验完成。

## 新执行路径的独立轻量核查

已重新读取 autotuner、C、experiment_v2、host_clock_probe 和 identity_quality 的实际修改。C 只改计时域、整数差和边界输出，原初始化、double、六层计算循环、尾块及 checksum 没有变化；新 kernel 秒由整数 ns 先相减再换算。当前目标会要求实际输出两整数内核端点，解析器检查唯一性、秒显示舍入及其被同域进程端点包围。

审核者在私有临时目录实际启动简短 Python 子进程，并给外层计时入口注入合成整数读数；没有编译或 n4096 调用。这些夹具只验证控制行为，不是计时诊断或性能证据：

| 独立反例 | 实际结果 |
| --- | --- |
| correctness 遇到旧 RAW/MONO=1 基线、新 RAW/MONO=0.6、REALTIME 倒退 | 子进程退出 0，数学夹具输出保留；辅助负差单列，新资源仅按 RAW 计 |
| correctness 的任务资源超时 | 保存 timeout，停止本任务精确进程组，wait 后记录的 PID 已不存在，非零 RAW 费用保留 |
| RAW 主域倒退 | 停止任务子进程，保存 actual_cost_unknown；未闭合账本阻止后续运行，没有记零 |
| 篡改 driver_raw_s 而不改整数边界 | usage 拒绝，不接受伪造费用 |
| 将目标源码两时钟边界改成 REALTIME，仍声明正式 RAW 协议 | freeze_check 拒绝，不允许 generic unknown/selfreported 目标进入固定 P1 正式批次 |

独立重跑作者的 9 项 core 与 11 项 method 轻量用例，20 项实际通过。上述进程与用例全过程真实受控 RAW 为 **0.732354030 秒**，0 编译、0 n4096，已交主控总账。夹具模拟的 24 秒 RAW 与 −20 秒 REALTIME 不进入正式账或报告。

通用三接口仍允许没有已识别 C 时钟的 selfreported 目标；其 timing_source_established=false 不能当成本任务主域建立。正式入口对固定 C 两 RAW 边界、源 SHA、协议与整数证据的检查承担任务范围内的严格限制，此兼容限定已向主控明确。

原先未闭合块恢复风险已交主控修正：QPC 块记录增加 boot_id 和 protocol_sha256；新 Goal2R 禁止 --max-jobs 留下开块；发现未闭合 before 就拒绝恢复旧 precheck。后续须用独立恢复夹具及实际数据复查。历史 CompleteClockGuard 保留以支持匹配历史记录的重生成，新 method=goal2r 执行没有把它或旧 first/previous 比值用于准入。

允许主控开展已预定的有限初始诊断。正式执行仍待完整集成回归、两项 n4096 数值抽查、实际 QPC/RAW 诊断、精确协议和代码身份冻结；此处没有宣告 T1/T2、正式实验或工程任务完成。

## 派生分析与恢复修复的独立复核

实际通读新 goal2r_analysis.py 后发现并交 owner 修复三项缺口：local driver 的相同 attempt 可以重复累加；项目成本没有重新核物理 journal starts；QPC 块原始读取没有全部绑定到其自身 driver 区间。修复后重新读取实现，并以不同于作者测试的私有 raw 夹具实际复核：

- 相同 local driver attempt 重复两行会被拒绝；实际两条 measurement_start 只收费一次调用会被全账 usage 拒绝。
- 共享面板只有一个物理 task，即使 REALTIME 倒退 −99 秒，仍从整数 RAW 2 秒计费一次。该 2 秒为合成字段，不是新实验测值。
- 同身份的三轮有效观测可得到 G=0，原三个不同耗时保留；少轮、非正 anchor 或重复同轮样本都使配对无效。
- 两个各自位于 driver 内的 QPC payload 成立；after 复用 before 的 payload，即使 SHA 已重新计算，也因实际 RAW 端点不在该 check driver 内被拒绝；boot 或 managed thread 改变被拒绝。
- 中断留下 open-before、或以 --max-jobs 拆开新块，都在安排目标前被拒绝，不能拿旧 precheck 跨恢复评分。

两组检查实际 RAW 分别 **0.003827491、0.004782767 秒**，实际整数 start/end、命令、结果保存在 [goal2r_review_control.jsonl](../measurement/goal2r_review_control.jsonl)。此前五组检查只保存了真实 RAW duration，没有保留端点；补账如实标注，未重造整数边界。审核者累计轻量受控 RAW **0.902452025 秒**、0 编译、0 n4096；主控将补账与主资源账分列并留预算，避免合成辅助时钟。

已实际读取 integration-repaired 的完整用例输出与末尾：244 tests、40.226 秒、OK；五种 native QPC cleanup 场景也在 host-bridge-tests 的 15 tests、4.769 秒、OK 中。第一次集成失败的原日志保留，没有改成成功。整数 driver 核查和追加入口的后续专项回归、新鲜数值运行及诊断仍由主控串行完成；以上只完成执行前代码与独立反例审查。

## 数值适配器首次构建失败

主控真实构建发现 numeric 适配顺序错误：先插入 REFERENCE 再替换首个 return 0，会误改 check_element 而没有改 main。审核者首次静态检查漏看这一匹配位置，随后复读修复和原 journal，确认 compiler 报 static declaration of verify follows non-static declaration，初次构建 returncode=1、measurement_start=0、summary.process_runs=0、failed_trials=1；这是适配器构建失败，没有发生大矩阵调用，也不是原计算内核错误。

修正为先替换原 main 中唯一 return 0，再插入 REFERENCE，使用 repair1 独立源路径、adapter、journal 和输出，不覆盖首次失败。validation_source 原路径也采用此正确顺序。原失败 [numeric-s24-O0.jsonl](../measurement/goal2r/numeric-s24-O0.jsonl) 与新 [numeric_adapter-repair1.json](../measurement/goal2r/numeric_adapter-repair1.json) 均保留；两项真正大矩阵还在执行，结果未提前标完成。

随后独立直接读取两份 repair1 完整 journal：各只有一次实际 measurement_start/measurement，correctness 退出 0、score_eligible=false、summary best=None、process_runs=1、failed_trials/runs=0。适配源 SHA 为 a1263e5f6e8de5bec01da3e46d612386a7906b6e308e421a335f8fd022809664，与 adapter 和 header 一致；老师 C、正式 C、适配 C 的 kernel 字符串相同。

| 真正新 n4096 数值运行 | 内核整数 RAW 秒 | 目标进程 RAW 秒 | 24 点结果 |
| --- | ---: | ---: | --- |
| s24/O0，PID 28363 | 241.589393717 | 242.377778311 | failures=0 |
| s128/O3，PID 30171 | 41.106274161 | 42.001869073 | failures=0 |

两者 max_abs=2.937539e−12、max_rel=2.814528e−15，满足独立 long-double 参考的 `atol=1e−12 + rtol=1e−11*abs(expected)` 条件；24 点是抽查，不是 4096² 全元素证明。两条内核整数端点都位于实际进程 RAW 端点内，显示秒与整数差在 0.5µs 舍入内一致。已逐条读取小矩阵 240 项和 sanitizer 5 项真实 check，均 returncode=0、failures=0、stderr 为空。这次审核只读消耗 RAW 0.003068368 秒，未重复目标调用；费用端点仍在 review_control。

## 正式测量前的实现结论

审核者已直接从 early/late 两个原 JSON、8 个 A/A journal、10 个物理 ledger task 重新核数；未只读 timing_result 或作者摘要。每个 QPC 事件的 Linux RAW 读取都在它对应 driver 整数区间内，PID/managed thread/Frequency 稳定，完整 Fraction 比界及括界均符合预定限制；8 次 A/A 有 8 个不同 run_id/PID，原初始化、源 SHA、编译器身份、共同 flags、O2 二进制、参数均一致。每条内核整数端点被目标进程包围，目标进程被真实外层 driver 包围。诊断实际 10 次调用、RAW 948.666897230 秒，与原账一致且低于预定 12 次/2700 秒上限。

旧账前 494 行的原字节 SHA 仍为 68861959f1e1e98b758f0c7143bb18683acb86ffe85f867e449ac84fc56f24e7；48 次、3713.432874365 秒未修改。新的 resource_reserve_s 先从剩余时间扣除，再用于所有正式主任务、QPC 块和追加面板；180 秒为 120 秒未精确测定辅助开销的保守上界加 60 秒余量，不伪装成实际测量，不冲销旧账。agent 的已测费用在独立真实日志，最终累计须同时列已知费用和保守上界。

正式前完整回归为 [goal2r-frozen-paths-integration.stderr.txt](../measurement/goal2r/goal2r-frozen-paths-integration.stderr.txt)：254 tests、39.376 秒、OK、0 skip；实际控制 RAW 42.350404318 秒。另 before-freeze-regression 是 26 项专项用例，不能混指两份记录。根路径的 kernel 整数核查、改变单位/时钟/解析/预算的真实源反例以及新增追加路径已有对应专项结果，不能以测试数量替代上述完整数值与原始计时依据。

**准许正式测量的条件已经具备：**主控将 protocol_goal2r.json 设为 approved/frozen，绑定以下实际身份与初始 timing_result，并持续采用预定块前后 QPC 检查；正式测量只有主控持锁，源码与判据停止变更，旧批次不续跑。共享面板只计一次，最终结论仍由实际新参考表、搜索和留出决定。此结论仅是实现可执行性与当前证据审查，不宣告 Goal2R COMPLETE 或最终 Engineering PASS。

| 冻结文件 | 实际 SHA-256 |
| --- | --- |
| src/matrix_multiplication.c | aad89170e8d0ca80c1dbc8dc1d8d5e69bab354af86128021be163c91e5a72b50 |
| src/autotuner.py | e3a563264994f4875da955ad87ff4ce1dd0c6c180aad3da750e1ae7d5beb02ec |
| scripts/experiment_v2.py | 9d985ae01c24ad322bc4847772b082c425793e8758871feac1b8edc3cf9e41ee |
| scripts/goal2r_analysis.py | 5b125ad8b5a0fa068b52075ab6e063820ded27271ebcc0464ae49779a697a7ff |
| scripts/identity_quality.py | a5a94c084cd3998ec6e32ab70cad3d36f140a9bbdd83b81bed636662bc7d13a6 |
| scripts/host_clock_probe.py | 5ebcb21f709ab0f325855892aee2cdae349035fb808c45a20a61a357f288326c |
| scripts/goal2r_checks.py | 5e61cdae21b45dc2ea269e44e516c15b671db69a00b25e7d9de490de095c9b4b |
| evidence/measurement/goal2r_timing_plan.json | 0a72b98b97d1ac9ff789013664c4fe1ee74e33936a1253e3157520d7f2802c4d |
| evidence/measurement/goal2r/timing_result.json | 3a1d2089c187c86dab2b6797b0207f54a294b09becfd1608ec6b077855168f82 |

## 新参照完整执行后的阶段复核

直接读取 [goal2r_reference](../../results/goal2r_reference/) 的全部 64 份原 journal、原 plan、local driver 与六个 block check payload，以 stdlib Decimal/Fraction 独立计算，未调用作者的分析函数。逐条核实际输出、PID/run_id、参数、源/编译器/flags/binary、整数计时与封存全局账，不依据主控的配置进度标签。

- 60 个正式样本为 20 配置各三次，另有 1 次预热和 3 次锚点；64 次都各有一个独立新进程、不同 PID/run_id，退出 0、checksum=17180040496.458935。每轮完整配置次序都与 `Random(505063+r−1).shuffle` 的原 plan 相同。
- 每条内核整数区间在进程 RAW 内，进程在 driver RAW 内，driver 在其 round 前后 QPC 检查之间。输出第一行秒与整数内核差在显示舍入范围内；output_status、timing_status、source_established、score_eligible 均有效。没有读取旧参照分数或删除较慢样本。
- 所有 journal 与冻结源/框架/协议一致，四个 O 的构建键分别保留，缓存复用只复用构建产物；每个正式样本仍有实际 measurement_start。四个实际二进制 SHA 如下。

| O | 实际 SHA-256 |
| --- | --- |
| O0 | 1cb0987ef381ecb5526a1df53aeaa0221c849fed9e76d196fc3e5370ccd3044e |
| O1 | bb64f1ef2a1a927cec81d4a3dab01d0aa42cdb2536a7b269e31b2d247048cc77 |
| O2 | ed09737e4c5fc1502bba676bd34101ec490560242787aa71e36236f3e44291fe |
| O3 | cbffa4a612e473bfe56a098492f886082cce7f3916790caf4cef2f577ddbf13f |

64 个目标 task 的 local driver 调用/费用都等于 [reference-resource-ledger.jsonl](../measurement/goal2r/reference-resource-ledger.jsonl) 对应全局 task，没有重复 attempt 或重收费。其目标 driver RAW 合计 **7674.689111517 秒**：正式 60 次 **7488.687952861**、锚点 **143.720303007**、预热 **42.280855649**。六项 QPC 检查 **68.641425168 秒**，故参照阶段总受控 RAW 为 **7743.330536685 秒**。

另以独立 Decimal 重算封存全账 262 个闭合唯一 task，原 max（三域）与新整数 RAW 费用分别按各自真实 schema 检查。全账 **12834.711963283 秒、124 次 n4096**，其中旧 **3713.432874365 秒、48 次**不变，新增主账 **9121.279088918 秒、76 次**；124=48旧+2数值+10诊断+64参照。封存 SHA 为 `2d2384c1da2ad5553dc35288ee1e2b7c3d531c5172c70bf0422352053a09d0e1`，与派生 summary 和 live ledger 对应前缀一致。此数不包含另记的 agent 费用/未测定辅助开销上界，不把保守余量当已测费用。

独立重算每格 min/median/max/MAD 与全部 `g_ref`，均与 [grid_summary.csv](../../results/goal2r_reference_summary/grid_summary.csv) 一致。下表是三正式样本的中位数，单位秒；原各样本和离散值仍保留在 raw/CSV。

| s | O0 | O1 | O2 | O3 |
| --- | ---: | ---: | ---: | ---: |
| 8 | 391.019060 | 101.839140 | 100.628924 | 101.957034 |
| 16 | 314.702166 | 63.628636 | 62.537484 | 64.712676 |
| 24 | 287.353034 | 65.436714 | 63.718468 | 63.927611 |
| 64 | 248.731089 | 55.894518 | 57.380079 | 57.015349 |
| 128 | 236.404080 | 47.395634 | 47.516251 | 47.007504 |

观测最优为 s128/O3；s128/O1 和 O2 的参照差分别 0.825676683%、1.082267631%，三者样本范围重叠，不能据此锁定唯一总体第一。较大波动仍保留，例如 s24/O0 的 238.978801、287.353034、291.588661 秒与 s24/O2 的 53.777253、67.582815、63.718468 秒。已核主控的进度标签纠正记录与对应 plan/raw；这是口头标签错误，原数据/顺序/判断未改写，不从其错误标签推断性能倍率。

**新参照阶段实现与原数据一致，具备继续六 seed 主实验的条件。**该阶段不构成整个 Goal2R 或成品完成；S3 真实配对、Greedy 起点、追加/留出、最终新鲜运行、报告/图片和远端发布还要逐项执行审核。完整参照独立核查受控 RAW 0.038806087 秒，另两项封存账只读/Decimal 复算分别 0.005236487、0.005076144 秒，均 0 次编译/目标调用，真实端点已写入 review_control。

## 六组主实验的原始轨迹与费用复核

中断前已直接读取 [goal2r_comparison](../../results/goal2r_comparison/) 全部 24 个搜索 journal、48 个单次共享面板 journal、原 plan/panel 身份和 12 个 QPC payload；本节在续跑后补录实际已经执行的检查，不将消息本身当作落盘产物。独立 stdlib 重放四算法，只使用各自实际反馈，没有调用作者分析函数或采用参考表预测搜索分数。

Random/Grid/S3 各 48 调用，Greedy 45 调用，共 **189 搜索调用**。六 seed 的 Random 与 S3 首六配置完全相同，随后 S3 确实各对自身首测最低两项进行一个新进程复核；更新分数为两样本平均，只有成功复核项可返回。各步 fresh_score/config_samples/score/best_so_far 与独立重算一致。四 seed 的 best 估计在复核后上升，例如 seed700001 从 57.251267 上升到 58.4419375 秒，没有保留偶然低值。Greedy 的 seed1118917、1223646 分别 6、7 调用后按自己的邻居和反馈达到 local_optimum，其余各 8 次；固定 Grid 八项和事前算法次序均与原计划一致。

每个共享面板等四个搜索 driver 都结束后才开始，锁定文件的四份依赖 SHA 与真正已结束 journal 相同。每轮只测 Random/S3/参照返回身份并集，按冻结种子打乱次序；六块分别 9、6、9、9、9、6 调用，共 **48 次**。相同身份只物理测一次，没有向在线反馈回填确认分数，没有把基础算法未做的面板虚构出来。所有 237 个目标 PID 不同，每个 physical start/measurement/trial/收费调用一一对应，完整数值输出与整数 kernel⊂process⊂session⊂driver⊂seed 块边界有效，冻结源/编译器/flags/四级产物一致。

逐条核 [main-resource-ledger.jsonl](../measurement/goal2r/main-resource-ledger.jsonl) 的 348 个闭合唯一 task，原 max（三域）和新整数 RAW 费用按各自 schema 独立 Decimal 检查。封存全账 **361 调用、41231.029911335 秒**，原 494 行 SHA 与旧 48/3713.432874365 不变。main local driver 与全局对应 payload 全部一致；各自 append 的 `at` 是两次写日志时间，可相差数毫秒，不当作计时边界。审核最初误要求这一字段完全相同，以及误设 Greedy stop_reason=exhausted；实际源码使用 local_optimum。两项审核断言已定位并更正，失败费用/现场保留，正式代码和 raw 无需修改。

| 主实验成本项 | 实际调用 | RAW driver 秒 |
| --- | ---: | ---: |
| 24 搜索 | 189 | 25425.234553621 |
| 共享外部确认 | 48 | 2835.260355315 |
| 12 QPC 检查 | 0 | 135.263648496 |
| 阶段合计 | 237 | 28395.758557432 |

账快照 SHA 为 `b4f56a0242b17012e7d95edc2378493a9e84dbf8280f28f3f221a4944913abb0`，与派生 summary 一致。十二项原整数 Fraction 全比界合并范围 [0.999947198685,1.000059918695]，最大端点 0.723585ms，相对宽全部低于 0.011%；均满足预定阈值且对应实际同 boot/bridge 身份与自身 driver。237 个真实目标的 RAW/MONOTONIC 比约 0.998014–1.090586，辅助关系变化保留，没有重新成为全局否决门。

逐轮 G 与实际搜索成本重算支持 **S3 主实验 REJECT**，详细反例和分流见 [方法挑战](goal2r_method_challenge.md)。该决定来自完整新测数据，而非身份不同预先否决。候选留出可以按规则 NOT_REQUIRED，三个 Random 新 seed 仍须执行；固定起点、最终新鲜运行和成品不因候选失败而跳过。此次实现/数据阶段未发现需要更改冻结代码的问题，不授最终 Engineering PASS。

## 四个固定 Greedy 起点的独立复核

已逐条读取 [goal2r_starts](../../results/goal2r_starts/) 原 plan、四 journal/driver 和八 QPC payload，独立从明确起点和各自实际反馈重放邻居移动、停止与返回；没有调用框架策略类或使用别的搜索分数。四条 header 的 greedy_start 与冻结计划相同，四独立 run_id、28 个不同目标 PID，数值输出/score/binary 身份、整数 kernel⊂process⊂session⊂driver 与各自 start 块均有效。

| 明确起点 | 实际返回 | 调用 | 停止原因 | driver RAW 秒 | 共同参照 g_ref % |
| --- | --- | ---: | --- | ---: | ---: |
| 8/O0 | 16/O2 | 8 | budget | 1277.002441539 | 33.037236 |
| 16/O1 | 16/O2 | 8 | budget | 890.195976976 | 33.037236 |
| 24/O2 | 24/O2 | 5 | local_optimum | 337.953658469 | 35.549567 |
| 128/O3 | 64/O2 | 7 | local_optimum | 497.373088907 | 22.065785 |

后两搜索的完整邻居已测且没有更低观测，所以提前停止与实现吻合；前两在第八调用用完预算。质量从同一新参照表按身份评价，上表不把这些结构起点并入六个随机主 seed，也不把四次运行混为多起点重启策略。目标费用 **3002.525165891 秒**、八 QPC **89.856559178 秒**，阶段合计 **3092.381725069 秒、28 调用**，local/global 各 payload 除独立写入时间 at 外相同。

八项原整数 Fraction 全比界合并范围 [0.999942022934,1.000049698928]、最大端点 0.688385ms、相对宽最大 0.0107635885%，均符合预定限制，读数在自身 physical check driver 内且 host thread/frequency/PID 稳定。冻结源与协议 SHA 没有变更。

读取 live 全账的 **截至 qpc-start-4-after task_end** 前缀，1088 行、363 个唯一闭合 task，独立 Decimal 合计 **389 调用、44324.958273927 秒**；前缀 SHA 为 `cb3e7bb4fe93825a13cd66ad7e3e3509a9ab9e831cd135ce01b7642ab65a4d02`。这是明确旧/新 schema 的闭合时间点，不把正在进行的 Random 留出开块算作零费用或已结束。旧原始 494 行 SHA 未改。此次直接复算 RAW **0.029088730 秒**，整数端点已记 review_control；仅补审核文件，不编译/测目标/改冻结代码。

主数据与起点阶段已复核。Random 留出、最终完整运行、干净检出、报告/图片与远端实物仍待审核；本文件没有授整个 Engineering PASS。

续跑后另直接将 24 行 search CSV 和六行 paired CSV 与各自 raw 返回、调用、实际费用、共同参照差、三个 G 及极值/中位数对照，全部一致；两个审核文件的 main/starts 节也已实际读取确认落盘。这项 RAW 0.043828036 秒仍为 0 编译/目标调用。至此 reviewer 独立受控已知 RAW 合计 1.231833090 秒；另三次很短只读入口未保留 RAW 端点，review_control 的单独 note 保留未知状态和 3 秒保守预留，不重造端点、不宣称该 3 秒为实测、不填零费用，主控从既有 supplementary reserve 覆盖。

## 三个新 Random seed 留出与性能任务闭合

逐份读取 [goal2r_confirmation](../../results/goal2r_confirmation/) 原 plan、18 journal、锁定 panel、local driver 与六 QPC payload。三个 Random 均从自己的反馈完成冻结 seed 打乱顺序的前八项，面板在各搜索返回锁定后开始，三块只测返回/参照最优身份并集，各轮顺序和依赖 SHA 与冻结规则匹配；共享物理调用仅收费一次。

| 新 seed | 真实返回 | 搜索调用 | 搜索 driver RAW 秒 | 三轮面板调用 | g_ref % |
| --- | --- | ---: | ---: | ---: | ---: |
| 1328375 | 128/O3 | 8 | 1015.683529980 | 3 | 0 |
| 1433104 | 64/O3 | 8 | 1085.925406830 | 6 | 21.289888 |
| 1537833 | 128/O2 | 8 | 572.052479823 | 6 | 1.082268 |

39 个实际目标 PID 不同，18 独立 run_id，完整数学输出、源/编译器/flags/binary 身份、整数 kernel⊂process⊂session⊂driver⊂seed 块均有效。24 搜索调用 **2673.661416633 秒**，15 新面板 **993.042573040 秒**，六 QPC **67.268916050 秒**，阶段 RAW 合计 **3733.972905723 秒、39 调用**。原整数 Fraction 六项全界合并 [0.999950164472,1.000047643260]、端点最大 0.650018ms、相对宽最大 0.0096564109%，符合预定限制且范围/bridge 身份有效。

第二 seed 的 r2 s128/O3 锚点没有删除：PID256193、内核 **148.733579 秒**、进程 RAW **149.964161500 秒**、driver RAW **150.267133404 秒**。它退出 0、边界/输出有效，慢观测留在原 journal、正式 CSV 和统计。审核脚本最初把口头“约150秒”误要求内核>150，随后误猜 task 总数388；实际内核如上、全账387闭合task，已更正审核断言，不修改任何正式记录。一个 reviewer result 句子误写了 driver 数字，原控制行保留并追加 correction note，实际费用字段、原 raw 和结论始终按真实字段计算。

独立全账重算 [final-results-resource-ledger.jsonl](../measurement/goal2r/final-results-resource-ledger.jsonl)：387 个唯一 task 全闭合，**累计428调用、48058.931179650秒**，旧48/3713.432874365及494行SHA不变；封存 SHA 为 `48285ab3b1caa9fd387ac93fefbb08e2b174ec03310b5b9a6253eb6cb81943fd`。与 [goal2r_summary](../../results/goal2r_summary/) 成本、三行新seed CSV、baseline_confirmation.complete=true逐项一致。完整主实验仍 REJECT/noextra，S3 候选留出 NOT_REQUIRED，三个 Random 留出已经实际完成；没有因不保留候选而漏执行基础确认。

上述只是预定性能任务闭合；最终新鲜 n4096、干净检出回归及完整成品仍需审核。干净 export 首次回归真实 254 tests/23.912s、13 errors 都出在 test_clock_followup.setUp 临时目录父 `.cache` 不存在，0正式矩阵调用。已直接读原失败日志和 owner 的一行 `(P1 / ".cache").mkdir(exist_ok=True)` 准备修复；没有依据归因为数值或主计时错误，原失败不覆盖。修复后完整回归/四级构建/最终新鲜运行仍等真实结果，不能用此静态读数替代完成。

## 最终实现、原始数据与成品结论

最终审核直接读取原 journal、四个实际冷构建二进制、前后 QPC payload、截图原图、完整报告/README 和历史重生成的两侧文件；没有编译、测试或启动矩阵目标。冻结协议 SHA 仍为 `6aa610244e3268fa6e315925c56a32634ca7aca27e14e52abd9c01661da7eb9c`；框架、C、driver、分析、判定、宿主桥、诊断与汇总入口的实际 SHA 均符合协议，第二全新 staged export 中相应文件逐字相同。最终 C 的原初始化、double、六层计算循环、尾块语义和20配置空间没有改变，修改集中于计时/输出边界和必要执行规则；没有新策略组合或大型通用平台。

首次干净检出回归的13个 `.cache` 父目录错误和原日志保留；一行 test setup 修复后，[clean-full-tests-repaired.stderr.txt](../reproduction/goal2r/clean-full-tests-repaired.stderr.txt) 实际 **254 tests/25.354s/OK/0skip**。四级 [clean-build.jsonl](../reproduction/goal2r/clean-build.jsonl) 各 `cached=false`、编译退出0、共同 flags 相同；实际 ELF SHA 与正式实验四级 binary 全部一致。直接从四 ELF 的 PT_LOAD 字节独立提取时钟调用之间区间核 SHA：O2/O3 同地址471字节完全相同，但整 binary 身份不同，正式配置/样本没有合并；已保存反汇编与声明 SHA 相符，报告没有把它们解释成SIMD或O3必然更快。一次审核脚本误把已经带P1的 disassembly 路径再加P1，失败与费用保留；按原记录真实路径读取后核对完成，不改产物。

[clean-fresh-n4096.jsonl](../reproduction/goal2r/clean-fresh-n4096.jsonl) 是唯一新的最终目标，PID266400、s128/O3、n4096、退出0、失败0、数学输出/主域/评分分别正常，checksum=17180040496.458935。整数差精确内核 **63.327071117秒**（输出63.327071）、进程 **64.048500793秒**、搜索窗口 **64.074271398秒**，严格嵌套于原始外层 capture **66.262831551秒**；全局仅收费1次，子区间不另叠加。最终完整运行不是读取旧viewer，旧130/中断证据没有改成成功；两项此前独立24点长双精度抽查仍提供数值依据，checksum不被当全元素证明。

最终两项 QPC 用原整数和 Fraction 独立复算，查询频率各10MHz且host PID/thread身份稳定，RAW/QPC完整比界为 **[0.999963413081,1.000026444193]**、**[0.999955635893,1.000037965459]**，最大端点0.526799ms、宽0.0082290108%，符合冻结筛查。读数在各自实际clock driver内，整个冷构建/目标/捕获在前后check之间，同boot且宿主bridge均退出0/按PID及StartTime清理为absent。MONO/QPC前约1.0132、后约0.9867只保留作辅助诊断，不否决有效RAW区间。这些是有限阶段一致性支持，不是独立物理校准或绝对准确性/环境根因证明。

完整 report.md 按老师1—4题连续阅读，20格数值/样本波动、18条三基础算法结果和汇总、固定起点、留出、六组S3真实退化理由与本角色原始重算一致，解释有必要限制且无内部任务/代理叙述；README入口与所有本地Markdown链接存在。六正式图片已逐张实际打开：框架SVG保留、其余五图均对应新数据/最终代码/完成运行。六图实际 SHA-256、Git blob SHA 与 [images.json](../reproduction/goal2r/images.json) 一致；uncropped终端原图也实际打开，正式build-run的top450区域逐像素相同，裁下部分只有空白/光标，没有删数字、命令或失败。两次真实截图使用私有授权Unix socket、无TCP、shell/Xvfb/authority/socket/lock全部按归属清理；五项宿主异常清理及12份截图清理fixture的实际记录同样无遗留。

匹配五个历史commit重生成的**45份**两侧实际派生文件逐字相同；新干净export重算的九份数据文件字节相同，summary.json唯一差为未要求plot时无images元数据，数据/决定完整相同。本地正式图片ZIP（`P1/.cache/P1-Goal2R-formal-images.zip`） 实际705638字节，仅六个正式文件，成员逐字同images，SHA-256 `119a22d63a2e3b672dcfb90fc2d8d953b98b673e959890888208aca850f52603`；ZIP在忽略的本地缓存，待主控关联发布commit与交接位置。

截至formal-image-zip的当前全账**403个唯一task全部闭合、429次累计调用、48209.511946584秒**，其中旧48/3713.432874365及原494行SHA完全保留，新381个有矩阵调用的task均退出0；剩余调用91。该数是有明确截止点的主账，agent实测和未知费用保守补账仍单列，不能冒充最终总成本。自己的所有已测只读/读图端点在review_control，另旧三次短读3秒与末期边界外开销5秒为独立保守上界，不是假造实测或0费用。

**实现、实际数值/有限计时、预定实验、派生结果和本地成品未发现未解决的核心问题，支持主控完成费用/文件卫生关口后正常发布。**本次结论依据完整实测与具体反例，而非测试数量/代理一致。最终总账、commit对应图片清单与实际远端SHA/文件核对由主控继续；本文件不授整个Engineering PASS，不把GitHub发布当水杉提交完成。
