# P1 Goal 1 实验与报告审核

审核角色：`/root/framework`。实验脚本和文献由 `/root/literature` 编写，报告由主控编写；本审核者未编写这些产物。此前参与框架实现，因此不承担框架的最终独立代码审核，该职责由 `/root/code_review` 承担。

本文件是内部审核记录，不是老师报告或最终工程验收。唯一写入权限为本文件。正式性能测量由主控串行执行。

## 1. 第一轮：测量锁期间的静态设计审核

时间：2026-10-01 19:36 UTC 起（北京时间 2026-10-02 03:36）。输入为老师一页 PDF、`literature.md`、`scripts/experiment.py`、`scripts/summarize.py` 和 `protocol_v1.json/md` 草稿。未编译、未执行实验或绘图，未读取正式网格数据；下面涉及数量的说明来自代码和静态计数，尚不是动态测试结果。

老师原题再次核对：目标为老师提供的矩阵乘法，五个 s 为 8/16/24/64/128，四个 O 为 O0/O1/O2/O3；必须有三个接口、完整 Grid、另外两种搜索、框架图、配置差异分析、软件硬件信息与 `report.md`。水杉 project01 是后续提交事项，不属当前发布。

记录时文件 SHA-256（作者仍在修改，不代表冻结稿）：

| 文件 | SHA-256 |
| --- | --- |
| `scripts/experiment.py` | `8681e4efb47899d9de502fb645ff15c7d24167b73c7c824284a08a1eead22fc6` |
| `scripts/summarize.py` | `f628f2d5b0bcbe2903a8d11ee61028e7be61c4dd862020938c3d13c5f97338e4` |
| `evidence/protocol_v1.json` | `70af47d84750d1ebe457f381e1dc1f107f3e69b83893039ebc8333674a46a0e1` |
| `evidence/protocol_v1.md` | `12e5418f848707cd0934ca24c0182f18cfefcd26cbcf499310e42c0a1891b86c` |

定位以函数名为准，作者修改后行号可能改变。P1 表示影响设计批准、测量或结论的必要修复；P2 表示复核强度或可复现性需补足。当前不能批准正式设计：新预测试和量化阈值尚未完成，下列已接受的修复也未在独立短测试窗口确认。

### ER-01：质量收益单位必须是百分点

严重性：P1。位置：`summarize.compare` 原第 156/171 行，协议指标与接受阈值。

代码计算 `gain = g_random - g_candidate = 100*(t_random-t_candidate)/t_ref`，单位是 g 的百分点差，不是 `100*(1-t_candidate/t_random)`。例如 t_ref=50、t_random=100、t_candidate=95，前者为 10 个百分点，后者为 5%。原 `quality_gains_pct/quality_gain_pct/quality_loss_pct` 命名容易让阈值和正文误用。

作者已接受统一为 `gain_pp/quality_gain_pp/quality_loss_pp`，并明确 epsilon、η_quality、Δ_allow 对应 g 的百分点，δ 为 [0,1) 的相对改善比例。状态：修复中，待重读稳定稿和等值/比例夹具验证。

### ER-02：预热被混入网格排序

严重性：P1。位置：`experiment.plan` 的 warmup job、`summarize.sample_rows/grid_table` 原第 65–98 行。

reference 阶段先创建 `role=warmup` 的 s128/O3 job；`grid_table` 只以 `stage == reference` 过滤。因此预热与三轮正式样本合并，s128/O3 用四个样本，其余配置用三个；图例却固定写 3 runs。预热必须保存原文、计入真实成本，但不进入正式配置排序。

作者已接受保留 role 并排除 warmup 的排序/质量用途。状态：修复中。短测试应构造极端快/慢 warmup，确认该配置仍恰为三份正式样本，且总实际运行数包含预热。

### ER-03：单候选留出确认没有轮换顺序

严重性：P1。位置：`experiment.plan` 原第 79–82 行，协议次序表。

`offset=(2*index)%len(names)` 用在两个版本的 holdout 时恒为零，导致 Random 每次在候选前。selection 五版本的 offset 0/2/4 能让 Random/S1/S2 的相对首中尾各出现一次；这个性质不适用于两个版本。

作者已接受 holdout 改用 index 轮换，并列出 selection/holdout 的实际完整顺序及紧随搜索的共同确认。状态：修复中，待计划夹具验证。三个 seed 对两个版本只能做到先后次数相差一，不能表述为完全对称。

### ER-04：driver 截断尾行不能直接追加

严重性：P1。位置：`experiment.read_records/recover/execute` 原第 32–47、230–263、281–286 行。

reader 允许最后一行没有换行且无法解析时返回此前记录；但 recover/execute 直接以 append 打开同文件，新的 JSON 会接到残片后，形成无法读取的完整坏行。恢复不能丢失残片，也不能让可恢复日志变成中间损坏日志。

作者已接受 recover 保留残片并修复尾行、execute 拒绝未诊断的 torn tail。状态：修复中。待夹具验证恢复记录能完整再次读取、原残片仍可追溯，且 execute 不启动测量。

### ER-05：恢复任务的资源预留重复包含已运行部分

严重性：P1。位置：`experiment.execute` 原第 297–301 行。

`used_runs` 包含 partial job 已有的 measurement_start；随后又加完整 `job.repeats*job.budget`。例如总上限剩一个进程、八步任务已完成七步，则合法的第八步仍被八个进程的预留拒绝。应按本任务尚可能启动的运行数预留，已经运行部分只计一次；硬退出无法明确的运行数应单独说明或保守计费，不能作为免费运行。

状态：已向主控报告，待作者处理。应以预算恰够剩余 repeats/配置的夹具覆盖；已失败任务不因此自动重试。

### ER-06：参考冲突的有限复核尚未定义

严重性：P1，设计冻结前置项。位置：`protocol_v1.md` 指标段、`protocol_v1.json`。

草稿只写“冲突时复核双方”，尚未规定触发条件、对哪些配置各跑几次、运行次序、上限、采用哪个 t_ref、如何重新判定所有配对，以及额外运行的注册目录与资源计费。当前 stage 只有 reference/selection/holdout，不能自动解释这项要求。

应在任何正式候选结果产生前冻结一个有限、可执行的规则，保留原始网格/原始分数，复核单独存放；冲突持续时不得无上限追加或强行 KEEP。状态：待补。

### ER-07：现有完成任务仍须核对实际环境与参数

严重性：P1。位置：`experiment.task_status/check_frozen` 原第 116–132、169–198 行。

现有检查覆盖 target/framework/protocol hash、n、action、seed、repeats、budget 和运行配置；但完成文件的实际 compiler identity、公共 flags、runtime_affinity 和 patience 参数没有与冻结协议比较。protocol hash 表示传了哪个文件，并不自动证明命令中的实际设置相同。应直接核对 header 中这些实际字段，不能只要求 compiler_identity 非 null。

状态：待补。短夹具应使错误 affinity/flags/compiler/δ 的完成日志被拒绝，而兼容的已完成任务不重复执行。新运行时同样应在计时前核对协议指定的 compiler。

### ER-08：原文与成本的重新计算强度不足

严重性：P2，最终原始数据审核前必须补证据。位置：`summarize.valid_measurement/check_trials/run_tables`。

统计重算使用 record.kernel_s，尚未重新解析 stdout 首行和唯一有限 checksum，也未核对 returncode、trial/repeat 唯一性及 summary 的真实进程计数。图线已使用当时 trial 的 best-so-far，没有把全网格中位数回填，这一点符合要求；但成本表仍直接采用 summary counters。

应补充自动检查或最终独立重算，拒绝 stdout 与 kernel_s 不一致、重复 repeat、退出状态矛盾及改错的 process_runs。硬中断 wall=null 与 recorded lower bound 必须继续分开，不能将恢复等待计入实际调优收益。

### ER-09：接受计算不能只凭有数值忽略完成状态

严重性：P2。位置：`summarize.compare` 原第 151–154 行。

INCONCLUSIVE 的理由称“complete paired searches”，实际条件只检查 gap 和 total_wall 非 null，没有明确检查 search/confirmation state。正式 driver 正常路径会在失败处停下，但汇总入口应拒绝带 failed/partial 状态的配对被判 KEEP。状态：待补状态夹具。

### ER-10：协议和图像输出边界需一致

严重性：P2。位置：协议 clock tolerance、`summarize.main/plots`。

初读 JSON 的 clock tolerance 为 0.01s，框架固定 0.005s；作者已接受同步。派生 CSV 目录目前只禁止等于读取的 batch 根目录，plots 目录无同等检查；应确认输出不会落入注册 raw batch 内，也不能覆盖其来源文件。状态：clock 同步修复中；输出边界待静态复查/短夹具。

### ER-11：干净副本的历史重算与继续测量应有不同路径约束

严重性：P1，主控新增的明确复现边界。manifest 将保存原 `measurement_root`。`task_status` 的普通路径及 execute/resume 必须在当前原测量根严格匹配实际路径和完整 fingerprint；不允许换目录后延续测量。

纯读汇总可显式调用 `historical_only=True`，仅将 metadata 的 target.source/cache_dir 按原 measurement_root 重建；compiler、flags、affinity、协议和全部参数仍严格相同，完整 fingerprint 仍须验证，当前目标与框架文件也须匹配 manifest 的 SHA。这个标志不可进入任何调度入口。

状态：作者实现中，尚未实测。短窗口将以 relocated 临时副本确认重算允许、继续测量拒绝；再篡改 source/hash/fingerprint/affinity 验证不会借历史模式绕过条件。

### ER-12：诊断噪声门槛不能替代小退化风险的可分辨性

严重性：P1，正式数据产生前新增明确设计边界。主控与作者拟定 relative range=0.18、reference/confirmation conflict=0.12，它们只能标记诊断异常；在约 17% 的样本范围内，仅凭中位数差不超过 2pp 不能解释为确认了小幅不劣。

主控在候选数据产生前接受以下固定规则：每个 Random/Candidate 配对以三个新确认样本的端点形成描述性收益范围 `[(min Random−max Candidate)/t_ref×100, (max Random−min Candidate)/t_ref×100]`，同时保存对应秒差端点。这是样本端点敏感性范围，**不是置信区间、真实参数界或显著性结论**。

任何 risk upper < −2pp 为明确坏侧并 REJECT；risk lower < −2pp ≤ upper 为跨界并 INCONCLUSIVE。KEEP 须全部三个 risk lower ≥ −2pp。S1 还须至少两个 robust gain pair，其 lower 同时 ≥12pp、≥5.6 秒；第三配对仅跨收益门且风险安全，不额外否决。中位数收益门已达而 robust pair 不足为 INCONCLUSIVE；连 upper 可能达收益的 pair 也不足两个，则 REJECT。明确成本不满足可优先 REJECT，unknown wall 不能用于成本接受。epsilon=5% 仍是观测近优目标、δ=0.06 是停止启发式。

主控进一步明确判定优先级：processes/wall 的明确 REJECT 保留并附诊断备注；质量相关 REJECT 遇到相关参照最优/返回配置噪声超 18% 或原参照与确认冲突超 12%，保守降为 INCONCLUSIVE，因为此时质量判断受参照/时漂影响。上面的 risk 坏侧 REJECT 以相关参照诊断门未失败为前提。降级不能形成 KEEP，无关的较差配置噪声不直接否决此配对。

状态：作者实现中，尚未独立动态复核。需覆盖 risk/收益端点等值、median 达门但 robust 不足、两个 robust 加第三收益跨界、upper 也不足两个、成本明确失败与 unknown wall 等边界；不得在读取正式候选结果后修改这些门槛。

### ER-13：正式成本接受采用完整外部 CLI wall

严重性：P1，主控在正式冻结前明确的成本定义。框架的 summary.tuning_wall_s 从 parse_args 后开始到搜索循环结束，包含 compiler probe、编译、测量和内部日志；它不包括 Python 启动、argparse、最终 summary 输出与退出。driver 的 task_end.driver_wall_s 是该次完整外部 CLI 进程的 monotonic wall。

正式 run table 保留内部窗口与完整 driver wall，接受规则使用完整 driver search wall 加共同 confirmation wall。多次已知 attempt 必须求和；hard-recovery 的实际 driver wall=null，不能用资源上界或离线等待代替，成本判断应为 INCONCLUSIVE。曲线横轴可保留内部窗口，但标签/报告须准确说明，不冒称完整 CLI 时间。无需为数十毫秒改动已审核框架。

状态：已向实验作者交接，等待稳定实现与动态夹具；须验证返回确认 wall 会改变成本接受、unknown/recovered actual wall 不可 KEEP，以及旧内部窗口仍保留可解释的真实 feedback 曲线。

### ER-14：含等值阈值须避免二进制舍入造成相互矛盾

严重性：P2，稳定稿的阈值边界回归。独立标准库算术实际结果：t_ref=50、Random=50、Candidate=51 时，两个 g 相减得到 −2.0000000000000018，而直接 `100*(Random−Candidate)/t_ref` 得到 −2.0；若前者用于 no_excess_loss、后者用于端点风险，同一个数学等值会得到不一致结论。`100−94.4` 为 5.599999999999994，也会被裸比较误判为未达 5.6 秒。

已要求作者统一以直接秒差计算 gain，并明确约 1e−12 的机器舍入容差处理摘要中含等值的门槛，远小于 stdout 1e−6 精度。这不是噪声容差，也不改变冻结框架 S2 的 strict > δ 定义。状态：待稳定实现及 −2pp/12pp/5.6 秒等值夹具；必须同时覆盖略微低于门槛仍失败，不能借舍入容差放宽质量风险。

## 2. 已核对的设计优点与边界

- 文献将原论文、简化启发式和本机结果分开，S1 不冒称完整 LHS，S2 不冒称论文给出的最优停止算法；全文获取失败和阅读章节有明确边界。本文尚未独立复读全部论文，因此这不是原文逐项复现认证。
- 20 配置参照采用预定每轮随机化 seed；selection 的五版本旋转能平衡 Random/S1/S2 的相对次序；两个候选分别和相同 Random 基线比较，无组合入口。
- 最終质量来自每个返回配置的三个新确认样本，而不是直接将在线 r=1 反馈当最终质量。`run_tables` 的 wall 对比已经包含搜索和共同确认。进程表分列两者，配对 savings 当前只算搜索；确认固定且完整时二者差值相同，但正文须列真实总运行数。
- 原始 journals 的 trial prefix 用来绘制在线曲线；reference 值只在事后计算 g，没有送入在线候选选择。
- 失败被保存、正式 driver 在失败处停止；硬退出的 wall 采用未知实际值和已记录下界，资源上界包含恢复等待且明确不叫实际调优时间。对这些路径的最终判断仍依赖短测试窗口。

## 3. 尚待执行的审核

1. 作者稳定稿：重新读取脚本及一致的 JSON/Markdown，关闭 ER-01 至 ER-14 的实际问题；确认参考复核、灰区和有限追加规则。
2. 主控开放短窗口后：不跑 n4096，以临时夹具核对 warmup 排除、两版本轮换、恢复尾行/资源、设置拒绝、比例单位、失败配对和 stdout/真实计数。当前没有这些审核者测试的执行结果。
3. 新预测试完成后：核对噪声与阈值推导、完整次数/时间上限、实际 compiler/affinity/目标/框架版本；才给正式设计批准或具体阻塞。
4. 正式批次结束后：独立从全部 raw stdout 和事件重算样本、中位数/MAD、返回配置、质量差、进程数、确认/编译/总成本、selection 与 holdout 结论。
5. 报告完成后：按原题 1/2/3/4 完整通读 `report.md`，检查学生信息、环境、20 配置、三基础算法、两单项来源/结果、图表标注、相对链接、截图真实性、内部术语与未完成项，记录具体修复和复查。

当前结论：设计未批准；正式测量和最终报告审核尚未执行。不授予最终 Engineering PASS。

## 4. 新单调时基预测试的独立原文检查

主控提供 9/9 已结束任务后，本审核者仅用 Python 标准库读取 `results/pretest_monotonic/*.jsonl` 与 `environment/pretest_monotonic_driver.jsonl`；没有启动 target、编译、性能测量或绘图。随后主控开始最多三个连续 O3/s128 诊断并重新上锁，本审核者停止短测试窗口、保持静态工作。

逐份重新解析 stdout 首行和唯一 checksum，核对与记录的 kernel/checksum 一致且有限、returncode=0、status=ok、spawned=true；每份一个 measurement_start 对应一个 completion，总计 9 个真实目标进程。九份 header 的目标、框架、协议哈希、compiler、flags、timeout、实际 affinity=[0] 一致；目标识别为 CLOCK_MONOTONIC。所有 kernel 小于对应 monotonic process wall，且核外耗时为 0.453599–0.541755 秒。缓存命中时的实际编译数和本次编译 wall 均为零，原准备编译来源仍保留。

再独立以 canonical JSON 重算九份 fingerprint，核对每行 run_id、当前目标/框架文件 SHA、build 与 measurement 的 build_key/binary SHA，以及当时缓存二进制实际字节 SHA；均一致。每份 r=1 的 trial score、summary best 与原 stdout float 一致。本检查不运行缓存二进制。

独立求和：目标 process wall 为 1202.446668 秒，driver monotonic wall 为 1203.049687 秒。原三份正规 O3/s128 为 42.548756、46.046341、49.066238 秒，中位数 46.046341、MAD 3.019897、relative MAD 6.558386%；预热 45.829971 单独保留。O0/s8 为 304.606781、310.770050、312.302917 秒。

各 measurement 的 UTC ended_at−started_at 比 monotonic process wall 多 2.355278–30.427750 秒。例如 03 项分别为 46.018731 和 43.011225 秒，04 项为 341.669571 和 311.241821 秒。这证明 UTC 时间戳不可直接相减用作本项目真实调优成本，也不能以 UTC 推导漂移比例；本检查不据此声称已定位宿主机原因。`pretest_resource_probe.json` 是结束后的低负载快照，不能证明此前全程隔离，且 cpufreq/温度未暴露。

单调上升和高离散度需要独立诊断；样本量三的 MAD/range 只是描述量，不是置信区间或可靠配对噪声界。epsilon 是事前近优目标、Δ_allow 是退化风险约束，不能以波动大为由放宽以使候选通过。若 η_quality 借鉴两倍相对 MAD，须说明从耗时相对比例转换到 g 的百分点所用的参照尺度和局限。正式阈值及设计批准仍等待诊断和冻结稿，不因这次原文检查通过而批准。

补充文案问题：当时 `protocol_v1.md` 第 1 节将旧预测试写成 CLOCK_MONOTONIC_RAW；原始 C 和 `timing_issue.md` 显示旧内核使用 gettimeofday，RAW 是后续时钟比较诊断。已向作者发出修正请求，待稳定稿复读。

有限追加的三个连续 O3/s128 诊断结束后，锁已解除。本审核者再次只读 `results/pretest_noise` 原 stdout/checksum/rc/affinity/fingerprint，均一致且内外 MONO guard 通过。内核分别为 41.610653、47.216225、49.724476 秒；CPU0 jiffy 忙比例 99.976–99.980%，waited children CPU 为 46.331218、51.933240、55.014867 秒，接近各次 RAW span 46.356090、51.989379、55.055316。RAW/MONO 比仍为 1.089452–1.097955，不能由此强行判定物理宿主机频率/温度或证明隔离。

六个正规 fast 样本合并的独立重算值：median 46.631283 秒，MAD 2.764074 秒，relative MAD 5.927510%，两倍 11.855020%，range 17.399957%。η_quality=12pp、δ=0.06 的拟定值可解释为事前描述性启发式，不是统计保证；epsilon=5 与 Δ_allow=2 仍分别是近优目标与严格退化风险约束。需由稳定协议的实际参照/返回确认噪声与冲突 gate 限定可作出的质量结论。三个追加诊断只作诊断，不进入正式参照或候选比较。本审核者未启动这些测量。

## 5. 借鉴边界的原文复读

本审核者随后用 web 阅读原作者的三个 arXiv 版本，未下载进仓库或安装依赖。阅读范围与结论如下，不能解释为整篇复现认证：

- [MLKAPS v1](https://arxiv.org/pdf/2501.05811v1) §4.1.1–4.1.3：原机制包括 LHS 覆盖、方差分区与模型/GA 自适应采样；本项目只取离散单维覆盖思想，S1 不能称完整 MLKAPS/LHS。后续 §5.2 页面展开返回 Internal Error，本审核者未独立核实这一节。
- [Just-in-Time autotuning v1](https://arxiv.org/pdf/2309.06414v1) §3.3、4.3、5：收益核算包含编译、试探快慢版本及未来重复调用；它支持成本核算动机，没有提出本项目 patience 规则。P1 未指定未来调用量，不能据此声称投入已摊销。
- [Autotuning Benchmarking Techniques v2](https://arxiv.org/pdf/2103.08716v2) §III-C、VI-C（表 VIII–XI）：统计停止假设与实际非正态存在差别，2695v4 实验需要将淘汰最少次数提高到 100。这支持资料文档的限制表述，不能推导本项目 r=1/2 或三个样本的可靠 CI。

目前未发现上述借鉴被冒称完整算法；最终报告仍须保留“启发式改编”和小样本局限。其他检索材料暂仅复核资料作者记录，不将其方法或完整正文视作本审核者已独立取得。

## 6. 稳定稿独立动态复核与设计批准

复核结束时间：2026-10-01 20:57 UTC（北京时间 2026-10-02 04:57）。本节取代前面历史时点的“设计未批准”结论。已完整重读 experiment/summarize 控制流与协议 JSON/Markdown，并复读 ER-08 最小修复；没有正式参照、选择、留出或冲突批次目录，没有读取正式网格或候选数据。

批准所针对的稳定文件字节：

| 文件 | SHA-256 |
| --- | --- |
| `scripts/experiment.py` | `9041accdee31d1fb7d822d1b43af4e090dc7c9308376c211533b3b552501a052` |
| `scripts/summarize.py` | `2630b8cead860d347b4cb67d5b04fade268969b5137f7c5462b8ed312340417c` |
| `tests/test_experiment.py` | `b6079145abf4a0bdce908c5550c02ef32a5a52a503dd8afe7d06e3bc8150ba32` |
| `evidence/protocol_v1.json`（审批字段更新前） | `e071a1459c11f45e59705f7a60ef2fdff7f3b7b087d102e485e5a691e068d7ae` |
| `evidence/protocol_v1.md`（审批句更新前） | `905b81446f57cf7e4fbf8708911e6bcd636823a8c5f33fdf78a4bb239b6857a3` |
| `src/autotuner.py` | `0a71c2fdb0d3d41be261c9aecc86b87487990dbc3bfd4e6b34e79b7fbd75ab49` |
| `src/matrix_multiplication.c` | `cece4fd572c1d25e9f9a7d045c21e8d77b25079a6f71513de0385d0d85d44835` |

### 6.1 ER-08 的真实发现、最小修复与复测

在先前稳定摘要 `f46f57ea316acd7871f3f12bd6871e1ac8845582bca6dc4ab4479d5b0e0f6c28` 上，本审核者构造了三项反例，确实仍被接受：status=ok 但 returncode=7；spawned=false 并同时伪减 summary.process_runs；完整 summary 前保留未对应 completion 的 measurement_start。已立即向主控/作者/代码审核者报告为正式启动阻塞，没有将旧 22 项测试通过等同于该问题修复。

作者仅修改摘要资格与 start/completion 对应检查并补回归，形成上表 2630/b607。随后本审核者在 TemporaryDirectory 中以正常合成 journal 为起点，独立复测以下五个变体：returncode=7、spawned=false+错误计数、repeat=999 的无对应 start、删除 start、重复 start。五项均抛出 ValueError；原完整日志通过。输出中的错误分别为评分包含失败/缺失样本、spawn 对应不符、非法 trial/repeat、start 缺失与重复 start；没有形成假成绩。该命令为 `python3 -B -` 标准库夹具，exit 0、约 0.2 秒，未执行 compiler 或 target。

### 6.2 本审核者实际执行的四组检查

所有命令均为 `python3 -B -` 的短夹具或只读 SHA/AST 检查。独立数据与断言由本审核者编写；少量成本/ER-08 夹具仅复用作者的正常 journal 生成助手，并另行篡改输入和断言。未执行 unittest 全套来替代独立反例，没有编译、运行 n4096、绘图、安装软件或修改原始预测试。临时数据由 TemporaryDirectory 自动清理。

| 检查组 | 实际通过 | 具体证据 |
| --- | ---: | --- |
| runner 与路径边界 | 5 | 原计划上限 61/166/100、总数327；三轮参照各20不同配置；五版本与单候选留出次序；affinity/δ/B 篡改即使重算 fingerprint 仍拒绝；历史 clone 只读允许、调度拒绝；partial 八步已跑两步只预留六步；完整 JSON 无尾换行保留原事件且不重复启动。 |
| ER-08 最小修复 | 5 | 五个非法 rc/spawn/start 变体均拒绝，原正常 journal 接受。 |
| 正式阈值与参考门 | 27 | 使用实际 JSON 的12pp、5.6秒、2pp、40秒、10%规则；−2pp/12pp/5.6秒/40秒/10%等值满足，超出或低于1e−6级仍拒绝；median 过门而 robust 不足为 INCONCLUSIVE；两个 robust 加第三仅收益跨界可 KEEP；upper 不足两对为 REJECT；风险跨界为 INCONCLUSIVE、全坏侧为 REJECT；不足两个省进程 seed、近优命中减少均拒绝；partial/unknown wall 不可 KEEP；重复 seed 拒绝；无关噪声仅报告，相关噪声使质量 INCONCLUSIVE、成本 REJECT 保留；18%/12%诊断等值与超界；极快 warmup 保留但排序仍恰三份；三个 Python 文件 AST 解析成功。 |
| 完整成本与 torn 恢复 | 3 | search 两个已知 attempt 5+7秒、confirmation3秒，外部总成本15秒而内部窗口另列；将一个 attempt 改为 hard recovery 后 actual=null、记录下界11秒/资源上界110秒且不能补成实际值；坏尾残片时 execute 拒绝且 Popen未调用，recover 保留原字节前缀及残片hex、unknown wall 与最多一个未知 spawn 资源计费。 |

四组输出分别明确 `passed=5/5/27/3`、`target_or_compiler_subprocesses=0`、`repository_writes=0`，均 exit 0，各约 0.1–0.2 秒。它们是40项独立检查断言分组，不能冒称40个 unittest 用例。另外 `/root/code_review` 已独立执行最终23/23实验 unittest（1.491秒）并审核代码；31项不变框架测试和实际小进程清理/完整 JSON 无尾换行恢复由该代码审核者负责，不计作本审核者运行结果。

### 6.3 问题关闭与批准边界

ER-01 至 ER-14 的正式设计阻塞已关闭：收益用百分点与秒差，warmup 角色排除排序；固定种子/随机参照/留出轮换；每搜索独立反馈，S1/S2 两个单项而无组合；完整 compiler/flags/affinity/参数 fingerprint；原 stdout/checksum/rc/start/repeat 及实际计数重算；共同确认与完整外部 CLI 成本；有限预注册的参考冲突复核；hard/torn 恢复保留原文且未知成本不能通过；纯读历史路径和真实调度严格分离；派生文件禁止覆盖注册 raw；样本端点敏感性与数值等值一致。参考复核不更换原 t_ref、原返回确认或原在线分数，最多两项选择事件和一项留出事件；同配置只三次、不同配置各三次，最多18额外进程，不追加选择 seed。

正式接受不使用18%噪声门放宽2pp退化约束。明确 wall/process 成本失败优先 REJECT；相关 reference/confirmation 噪声或冲突使质量结论保守为 INCONCLUSIVE；样本端点不是 CI 或总体参数界。三 seed、在线 r=1、长时间漂移以及 MONO/RAW/CPU 时间差异限制仍成立；上述检查不支持统计显著性、硬件原因或跨机器推广。

**实验设计关口结论：批准该稳定稿按事前规则进入正式比较，无未解决的设计阻塞。** 主控可仅设置 JSON 的 approved 状态、审批证据和冻结时刻，并同步 Markdown 审批句；数值、代码、种子和成本定义不能改变。正式启动仍须由本审核者复核审批后完整 JSON 字节 SHA、确认除审批字段外内容与上述 draft 完全相同，再由主控串行执行。

这不是最终 Engineering PASS。正式全部 raw 重算、selection/holdout 实际结论、完整 report.md 通读、图片/相对链接和实际 GitHub 版本审核尚未进行；任何未完成、REJECT 或 INCONCLUSIVE 都必须在报告中如实保留。当前没有新依赖、配置或外部服务写入。

## 7. 审批后最终协议字节复核

主控冻结时刻为 `2026-10-01T21:00:32.588333+00:00`。本审核者独立计算最终 JSON SHA-256 为 `7e437efd47f6f000add30ac66d7cd3e9ae7dfc100f2d0aecf92c318275bacaa7`，最终 Markdown SHA-256 为 `d679dac852d4ca9b9bd8edeb208d3960f2fcbb64dd44be3d70f4056fdad3aae2`，均与主控提供的字节哈希一致。

与审核前保存的 draft parsed JSON 逐字段比较，仅 `state` 和 `approval` 对象改变；前者为 approved，后者仅含冻结时间、本文证据路径和代码审核证据路径。其他全部字段一致。将 Markdown 四处审批说明反向替换后重新求 SHA，精确恢复审批前 `905b8144…`；没有数值规则变化。再次读取 runner/summarize/tests/framework/target 的实际文件字节，上述五份源码 SHA 均未改变。

只读调用 `plan(reference)` 产生内存计划后，`check_frozen` 在 experiment.py 第273行确实失败：`the independent approval evidence is missing`。runner 按 P1 根解析 approval.evidence，`reviews/experiment_report_review.md` 指向不存在的 P1/reviews；实际文件在 P1/evidence/reviews。已向主控立即报告，要求只修正审批证据路径为 `evidence/reviews/experiment_report_review.md`（code_evidence 同理），不变更数值/代码；当前不能启动，等待修正后的最终 JSON SHA。本审核者未写正式目录或 plan、未启动 compiler 或 target，并停止短测试；仅继续最终字节/只读 preflight 复核。

上述审批字段路径随后由主控修正。最终冻结时刻为 `2026-10-01T21:03:34.498833+00:00`，最终 JSON SHA-256 为 **`64bb8f6c66e70de2c9a53960cbd693447ecebaa43a258f21439bd2827e4b0f66`**；Markdown 仍为 `d679dac852d4ca9b9bd8edeb208d3960f2fcbb64dd44be3d70f4056fdad3aae2`。本审核者再次逐字段比较，仅 state/approval 相对 draft 改变，两份证据文件确实存在，五份源文件 SHA 不变，真实只读 `plan(reference)` + `check_frozen` 已成功（exit 0）。没有正式目录、compiler/target 启动或原始测量；之前7e437的审批路径失配不产生任何正式 runs。

**最终字节与 preflight 均批准，可由主控串行启动正式批次。** 当前审批路径问题已关闭。本审核者停止测试/编译，在测量锁期间只做静态读取，不修改冻结规则；正式 raw 重算与完整报告/GitHub 审核仍未完成。
