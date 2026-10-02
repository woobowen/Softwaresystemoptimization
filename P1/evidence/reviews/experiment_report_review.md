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

## 8. 正式 reference_v1 原始数据独立审核

审核时间：2026-10-01 22:56 UTC 起（北京时间 2026-10-02 06:56）。reference 已结束，selection 正在主控串行测量；测量锁仍 ON。本审核者只执行 Python 标准库只读解析、hash、CSV 比对和统计，不 import 调度入口、不启动 compiler/target、不运行 unittest 或绘图。没有读取 selection 的反馈，也不据网格修改冻结策略/阈值。唯一写入仍为本文。

### 8.1 原始记录、计划与构建身份

61 份 journal 全部以完整 JSONL 和末尾换行保存，61 个独立 run_id/fingerprint；每份严格包含 header、session_start、trial_start、cached build、measurement_start、measurement、trial、session_end、summary。逐记录核对 run_id、trial_id=0/repeat=0、配置、command、PID、spawned=true、start/completion 唯一对应；60份正式记录恰为20配置×3轮，另1份独立 warmup。用独立 Random(314159+round_index) 重建每轮20配置次序，与实际计划和driver顺序逐项一致。

每份 stdout 首行重新 float 解析，等于 kernel_s 和该 trial/best score，且正/有限；唯一 checksum 重新解析并全部等于17180040496.458935。61份均 returncode=0、status=ok、stderr空、error=null、未中断；内核均满足 MONO process wall +0.005秒 guard。header完整字典逐字段对冻结协议核对，并独立 canonical JSON 重算 fingerprint：target/frame/protocol hash、compiler完整路径/版本/SHA、公共flags、n=4096、CLOCK_MONOTONIC、实际affinity=[0]、timeout1200、compile_timeout60.0、δ.06及其余参数均一致。

四份 cache binary 的实际字节 SHA、cache identity、build_key 和原始准备记录均匹配；61份 cached build 的历史compile记录与准备阶段原记录完全一致，compile_wall均0，没有将历史compile成本重复计费。准备阶段的四组build_start/build与成功编译PID/command相对应，公共flags仅 -std=c11 -Wall -Wextra 加各自-O等级；正式reference没有编译启动。61次compiler --version探针也各有成功记录，其成本在完整CLI wall内。

只读审核脚本首版误将cache manifest的build_key当顶层字段而产生KeyError；读取实际结构后改为result.build_key并核对identity，第二次整套读取通过。这是审核者的解析假设修正，工程源码、日志和分数没有修改，也没有补测。

### 8.2 20配置统计与完整派生表

从60份正式stdout重建每配置三个值，warmup=45.921619秒保留并排除排序。独立用median、median(abs(x−median))及(max−min)/median重算；grid_summary.csv的20行顺序、valid=3/failed=0、rounds/samples、median/min/max/MAD/range逐值完全一致。另逐行核对measurements.csv的61份原stdout/stderr/rc/command/配置/时间与hash字段，全部一致；reference-only summary.json及batch_costs.csv的计数、时间与噪声标记也匹配。

以下为独立重算值，range列使用百分比显示，CSV保留比例：

| s | opt | median秒 | MAD秒 | relative range |
| --- | --- | ---: | ---: | ---: |
| 8 | O0 | 300.623230 | 5.290100 | 4.9083% |
| 8 | O1 | 77.373161 | 0.143493 | 0.8671% |
| 8 | O2 | 78.313446 | 0.174309 | 1.3959% |
| 8 | O3 | 78.263649 | 0.771935 | 2.4937% |
| 16 | O0 | 217.292618 | 0.516922 | 0.5100% |
| 16 | O1 | 44.326172 | 0.431633 | 8.2284% |
| 16 | O2 | 43.614208 | 1.487328 | 7.4005% |
| 16 | O3 | 44.371098 | 0.042152 | 2.5848% |
| 24 | O0 | 210.435379 | 0.824280 | 1.4575% |
| 24 | O1 | 46.188328 | 0.339321 | 2.5455% |
| 24 | O2 | 43.737030 | 0.055725 | 2.1718% |
| 24 | O3 | 44.067669 | 0.779091 | 4.5286% |
| 64 | O0 | 179.600632 | 1.095856 | 3.2582% |
| 64 | O1 | 41.472359 | 1.192818 | 7.7028% |
| 64 | O2 | 41.239479 | 0.024376 | 5.7859% |
| 64 | O3 | 41.112492 | 2.239270 | 13.8415% |
| 128 | O0 | 178.396179 | 5.207840 | 8.5254% |
| 128 | O1 | 41.177814 | 2.659123 | 24.3169% |
| 128 | O2 | 39.499706 | 0.885681 | 14.9380% |
| 128 | O3 | 42.501537 | 4.259323 | 32.3638% |

原参照观测最优为 O2/s128，中位数39.499706秒；三轮样本40.385387、39.499706、34.484921秒，MAD0.885681秒、range14.9380%。它是三样本中位数的观测最优，不是单次最小值或真实全局最优保证。128/O1的range24.3169%、128/O3的32.3638%超过冻结18%诊断门，只有这两个配置被标记；summary.reference_checks完全一致，参照最优本身未越门。有效慢/离散样本全部保留，没有把33.005756秒等快单次替换t_ref。

### 8.3 独立成本与版本快照

计数为61个真实target进程、61次compiler版本探针、0次reference编译、0失败/恢复/未知成本。driver有61组完整start/process/end，attempt_id0..60，rc0且interrupted=false；monotonic starts和各完整driver wall证明这些任务串行，不用UTC跨度代替成本。以下均含reference warmup，时间单位秒：

| 项目 | 独立重算 |
| --- | ---: |
| 内核时间和 | 5533.803465000 |
| target process wall和 | 5563.930275265 |
| 框架内部窗口和 | 5565.119835502 |
| 完整CLI driver wall和 | 5569.810459629 |
| 版本探针process wall和（已在CLI内） | 0.118502434 |
| 共同四次编译process wall和（单列准备） | 0.537283707 |
| 共同build完整driver wall（单列准备） | 0.610331204 |

target process wall−kernel为0.458709–0.636853秒；UTC跨度−MONO process wall为约−0.000008至25.387543秒，后者只作时钟诊断，不加入调优成本或推断物理硬件原因。没有未知wall或免费恢复数据。上述值不等于整个项目最终成本，selection/holdout/冲突及其他准备项尚未结算。

审核快照：

- protocol JSON：64bb8f6c66e70de2c9a53960cbd693447ecebaa43a258f21439bd2827e4b0f66。
- reference plan：9f5f093803045373aecc48a22b355ce99ef8fc19eb8c07d79fb95ef409dde1ad。
- reference driver.jsonl：05a23220bc4ed3b59686f14f9dea5ed7d969fb104f26f53a78c7aafbd62037a7。
- 61份journal集合：ffeeeb906b5eec5910af67569e1ca5ad7787932b737c32fa3e9c7413aadec6a2；定义为计划顺序的(file_name,SHA256)列表经sort_keys、紧凑分隔canonical JSON再SHA256。
- grid_summary.csv：8f3bfbb506370076afe3a15f08cd1bcff8f5e23e34f05a5ec6e9e5702f6761ec。
- measurements.csv：b0c8f4e1f90cba3ac6b244b6f372b6c1c0a914291dc526707c0536e853ee2715。
- reference-only summary.json：b7c427137899298ad78201bdfc4a3addd6df84b77b8440eac3152646278dc48d。
- batch_costs.csv：6082bcf50daac80ccf0f2d9a97cc97f8d45d1e8d7f2cba3994cfadfd08c8007e。

这些派生摘要以后加入selection/holdout可更新，以上为仅reference快照，原始reference文件不得更改。冻结目标cece、框架0a71、runner9041、summarizer2630仍一致。

**reference审核结论：完整61份原始数据与20配置表通过，未发现影响结果的实现或派生数据错误。** 128/O1与128/O3的预设噪声标记应如实保留，后续只有相关返回配置才应用对应gate，不能因新网格数据重调参数、删除样本或更换参照。selection/holdout/冲突、最终曲线和报告/GitHub的独立审核仍待各批结束，不授予最终Engineering PASS。

## 9. 报告已完成段落的连续通读

审核时刻：2026-10-01 23:16:45 UTC。selection仍在主控串行测量、锁ON。完整通读当时的report.md，重点范围为1–3和4(1)，并核对4(2)已写的方法说明；其明确的在线结果待填区域按项目进度保留，不作为当前缺陷。report SHA-256为`9c7dede676c07994ffb915d7a3cd7d44fb269d8bd199c0a47bac6be328660305`，framework.svg为`dbc13ad44a457092bff9547d12c0751fbc9cc917fc40d76b989a84731c3a93bb`。本节不是完整最终报告或实际GitHub验收。

### 9.1 已核对内容

- 再次完整读取老师一页PDF：报告按1（三接口）、2（附件目标）、3（五s与四O）、4（Grid与另两算法）原题次序组织；学生10245102410/吴博闻正确。已包含框架图与实现优劣、关键搜索循环代码及明确软件硬件信息。
- 逐段与ConfigSpace、TargetProgram、SearchStrategy、Evaluator和search()实际源码对应：配置枚举、四构建缓存、测量与构建隔离、统一feedback/预算、失败score=None、恢复已完成trial占预算均准确。代码片段与search()循环一致，没有把全部网格中位数回填在线轨迹。Greedy相邻候选列表、稳定邻域访问、严格改进、全局已观测best返回也与源码一致。
- 读取运行目标和原始附件、验证生成器及现存记录：计时前初始化、原六层循环与末块边界、计时后checksum、同边界CLOCK_MONOTONIC说明正确。独立重新解析240个small、5个sanitizer、2个full检查的stdout CHECK行/rc/stderr/source SHA；全部failures=0。small最大绝对误差5.174333e−14、full2.937539e−12，与report逐值一致；full确实各检查24点，报告没有冒称4096逐元素比较。容差式与独立long double点积代码一致。
- 原始C实际字节与根目录输入完全相同：1357字节、47个CRLF、原始SHA为188d011109c4470e1f41829216e8677a5c2d8f2b7c8a44215652320dbdf6de15。仅读文本比较时归一换行并逐行rstrip，运行目标与原附件的循环文本相同，kernel SHA为4005ab7de11a2336c300420cdf354b3ec2f05aa995be988b5008abdf21e382ab；没有混用文本归一后的hash冒充原始字节SHA。
- 报告20个网格中位数全部与第8节已独立审核CSV精确对应，O2/s128样本/MAD及两项range噪声说明正确。明确观测参照不是真值、保留快慢有效数据；缓存原因只作结构解释，没有由时间反推精确cache命中或物理硬件原因。
- 读取已有四份assembly，无重新编译：每个计时区间均包含mulsd/addsd且没有mulpd/addpd。O2/O3两计时调用之间的原始行文本SHA同为`1de9fbae5f59d7faae97467f0367110271122a31d21be341eadfad8802668aef`。O0内核可见多次栈索引访问，O1有指针加8；源码报告以“相符”解释耗时下降，没有假称测量了cache miss。向量化优化备注与实际指令的表述还需下述PR-01修订。
- Ubuntu24.04.2、WSL2内核6.18.33.2、CPU显示Intel Core Ultra9 185H、GCC13.3、Python3.12.3都对应initial_environment记录；MemTotal16173232KiB转换为15.423996GiB，约15.42GiB正确。未用厂商规格替代WSL2证据。
- 所有本地Markdown链接对应现存文件；framework.svg是有效SVG XML、1000×640，三输入、真实类名、Evaluator/search、Journal及反馈箭头结构与实现一致，没有外部图片依赖或伪终端结果。仅核本地结构与链接，GitHub实际渲染留待发布后的最终审核。
- 通读文风：已完成段落先说明行为再给必要结果，主体是学生回答与技术解释，没有Codex/ChatGPT/AI/审核流水账或状态标签；表格数值不重复逐项念述，正确性与噪声限制保留有必要的明确边界。没有仅凭关键词筛查判定“自然”。

上述只读标准库断言与原记录重解析命令exit0，未启动compiler或target，未运行unittest、绘图或改变测量文件。当前没有P1级内容/数据阻塞，以下两项P2表述问题由主控接受，仍待其修订与再次核对。

### PR-01：区分GCC向量化备注与实际checksum归约指令

严重性P2。位置：report.md第76行“向量化的 checksum 循环位于计时之后”。optimization_diagnostics.txt确实将源码57行checksum内层标为“loop vectorized using 16 byte vectors”，但现有O2/O3实际计时后归约使用连续addsd，未见addpd/mulpd。把该备注直接写成实际packed算术容易混淆IR阶段优化报告和最后指令。

改法：保留“计时内核标量乘加/O2O3区间相同/内层控制流阻碍向量化”，将这一短句改为“优化信息中唯一标为向量化的是计时后的checksum循环”。这样准确说明GCC备注位置，又不把它当计时SIMD加速证据。主控已接受；状态：待主控在测量监控窗口结束后修改文稿，本审核者不改report。

### PR-02：框架图TargetProgram方法名与源码一致

严重性P2。位置：images/framework.svg第10行TargetProgram框的“build / run / parse; compiler identity”。TargetProgram实际方法为build、measure、parse（measure在autotuner.py第235行），run是CLI动作而不是该类方法。图中的类名和方法名应直接对应读者查看的源码。

改法：将标签run改为measure，必要时简化后面的描述以保持框内文字长度，不变更框架数据流。主控已接受；状态：待主控修改SVG标签。本项仅文档准确性，与冻结源码/协议/性能数据无关。

**本次部分报告审核结论：已完成1–3/4(1)的内容和数值与证据相符，两项P2修订待复查；4(2)结果尚未结束，最终全文/图表/selection/holdout审核未完成。** 不授予最终Engineering PASS；测量锁继续遵守。

## 10. 正式 selection_v1 原始数据、比较与后续诊断关口

记录时刻：2026-10-02 02:53:33 UTC。31个选择任务已结束，主控随后串行启动已批准的9个 conflict_selection_v1 诊断任务；测量锁持续ON。本审核者只执行 Python 标准库的JSONL/CSV/计划、hash和数值重算，不调用工程中的搜索或比较实现，不启动compiler/target，不运行unittest或绘图。原始结果、派生表、冻结代码/协议均未修改，唯一写入为本文。

### 10.1 原始记录与真实运行数

独立逐份读取reference的61份和selection的31份journal，合计92个不同run_id、215个真实target测量。selection恰含108次online、45次返回确认、1次warmup，共154；五种算法online分别为Grid24、Random24、Greedy19、S1分层24、S2 patience17。15个搜索轮都只有各自新feedback，三个确认样本是搜索结束后的独立进程，warmup保留但不进入质量排序。相同参数的header可以具有相同fingerprint，独立run_id和measurement_start证明它们没有共享测量。

所有原始stdout恰有首行正有限float和唯一有限checksum，重新解析后与kernel_s、trial中位数/score及best完全对应；checksum均为17180040496.458935。每次均spawned=true、returncode=0、status=ok、stderr空、error=null，满足kernel≤MONO process wall+0.005秒。按trial_id/repeat核对唯一start与completion、配置/command/PID/start/end与重复索引；完整trial和summary计数一致，没有失败、未终结记录、重跑恢复或未知wall。

各header完整metadata和独立canonical JSON fingerprint与冻结source/frame/protocol/compiler版本、realpath/SHA、flags、affinity=[0]、B8/r1/seed/δ.06/min5/patience3/timeout等逐项一致。确认任务的action=run、r3和最终选择配置另行核对，未误用搜索预算。31组driver start/process/end严格按实际计划串行，algorithm轮换后立刻执行自身确认；31次compiler版本探针成功、0次新增编译。cached build的四个binary实际SHA、identity、build_key和原准备记录保持一致。原reference journal集合SHA仍为ffeeeb…，grid_summary.csv仍为8f3bfb…，没有覆盖原参照。

### 10.2 候选次序、停止与当时反馈

用独立Random(seed)重建三次Random无放回列表；S2前三个序列分别等于对应Random的5、7、5步前缀。S1独立重建四O层内的s打乱和每轮O打乱：20配置不放回，任意前缀各O计数差≤1，B8每O各2次；候选生成不读取Grid或其他轮反馈。Grid三轮均为稳定前8项。Greedy以seed均匀选择单起点，重建相邻下标四邻域、配置枚举稳定次序、整邻域观测后严格改善及本轮缓存，得到7、7、5次测量和local_optimum停止，与每条trial一致；起点16/O2、128/O3、64/O3如报告所写，不据这些较有利起点推断一般优势。

S2的stale/best逐步重放一致：104729第5步42.730598秒比原best43.460831改善约1.6802%，仍更新best但未越6%，stale=3后停止；130363第4步改善约6.3483%重置计数，第5步约2.6348%只更新best，第7步stale=3后停止。该seed的Random第8项128/O2在S2中没有被评估，不能免费补入S2结果；155921第5步停止。所有试探计入真实预算，无未测候选参与best。

逐行核对当前215行measurements.csv、108行online_curves.csv和15行search_summary.csv，配置、stdout、hash、分数、计数及完整成本均一致。曲线每个prefix best只取当时本搜索已经完成的原始score；横轴为框架内部窗口，不回填全网格中位数或后续确认值。以下表由原始测量和driver重建，时间单位秒，g列为相对原t_ref=39.499706秒的百分值：

| 算法 | seed | 返回s/opt | online数 | online best秒 | 确认median秒 | g（%） | 完整search+confirm wall秒 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| Grid | 104729 | 16/O1 | 8 | 45.099396 | 44.194180 | 11.884833 | 1053.200412 |
| Grid | 130363 | 16/O3 | 8 | 44.952080 | 44.844345 | 13.530832 | 1040.768085 |
| Grid | 155921 | 16/O3 | 8 | 42.053825 | 42.672432 | 8.032278 | 1006.073105 |
| Random | 104729 | 16/O1 | 8 | 43.431442 | 48.896767 | 23.790205 | 1082.793920 |
| Random | 130363 | 128/O2 | 8 | 34.116451 | 33.191216 | -15.970980 | 697.458856 |
| Random | 155921 | 128/O3 | 8 | 32.570972 | 32.911858 | -16.678220 | 1057.642905 |
| Greedy | 104729 | 16/O3 | 7 | 44.572552 | 43.453590 | 10.009907 | 526.521878 |
| Greedy | 130363 | 128/O1 | 7 | 37.570213 | 39.124683 | -0.949432 | 529.634615 |
| Greedy | 155921 | 128/O3 | 5 | 32.670555 | 33.041843 | -16.349142 | 289.012571 |
| S1 分层 | 104729 | 128/O2 | 8 | 39.282055 | 39.030720 | -1.187315 | 924.156011 |
| S1 分层 | 130363 | 128/O2 | 8 | 35.368584 | 36.206318 | -8.337753 | 875.295188 |
| S1 分层 | 155921 | 128/O2 | 8 | 32.955601 | 32.248898 | -18.356613 | 890.827406 |
| S2 patience | 104729 | 16/O3 | 5 | 42.730598 | 46.152561 | 16.842796 | 559.359397 |
| S2 patience | 130363 | 64/O3 | 7 | 38.860531 | 39.563389 | 0.161224 | 664.630474 |
| S2 patience | 155921 | 128/O3 | 5 | 32.697639 | 33.396526 | -15.451204 | 770.713016 |

近优计数Grid0/3、Random2/3、Greedy2/3、S1 3/3、S2 2/3，与派生表一致。负g对应比原参照阶段更快的后续有效样本，不表示生成了配置空间之外的性能。

### 10.3 成本与配对接受规则的独立重算

selection含warmup的kernel和11935.717976秒、target process wall和12011.861294秒、内部窗口和12013.745039秒、完整CLI driver wall和12016.120603秒；31次版本探针wall和0.061806秒已包含在CLI成本内，不重复加。reference与selection共215个target进程、完整CLI合计17585.931062秒。共同准备的四次compile成本仍单列，各搜索没有新增compile。没有用内部窗口、UTC跨度或资源上界替代真实完整成本。

15轮比较成本逐轮为自身search完整driver wall加自身三个确认的完整driver wall，不能免费省去共同确认。三seed完整wall中位数：Grid1040.768085、Random1057.642905、Greedy526.521878、S1 890.827406、S2 664.630474秒。S1每轮与Random均8次搜索，wall满足≤1.10×Random；S2真实少跑3、1、3次搜索，合计7次，三seed中位数节约393.012431秒，进程与40秒成本门均满足。

配对gain以原始确认值直接计算：gain秒=t_random−t_candidate，gain_pp=100×gain秒/t_ref。端点为[minRandom−maxCandidate, maxRandom−minCandidate]，不解释为CI、真实参数界或统计显著性：

| 候选 | seed | median gain秒 | median gain_pp | 样本端点gain秒 | 样本端点gain_pp |
| --- | ---: | ---: | ---: | --- | --- |
| S1 分层 | 104729 | 9.866047 | 24.977520 | [8.646503, 11.560444] | [21.890044, 29.267165] |
| S1 分层 | 130363 | -3.015102 | -7.633226 | [-4.208470, -2.064873] | [-10.654434, -5.227565] |
| S1 分层 | 155921 | 0.662960 | 1.678392 | [0.410816, 1.182334] | [1.040048, 2.993273] |
| S2 patience | 104729 | 2.744206 | 6.947409 | [1.651348, 6.074474] | [4.180659, 15.378530] |
| S2 patience | 130363 | -6.372173 | -16.132204 | [-7.311440, -5.351803] | [-18.510112, -13.548969] |
| S2 patience | 155921 | -0.484668 | -1.227017 | [-1.021938, 0.400440] | [-2.587204, 1.013780] |

S1仅104729这1对的lower同时满足≥12pp、≥5.6秒；possible upper也只有1对，未满足至少2对实质改善。130363风险全落在−2pp坏侧，quality和risk事前门均失败。该seed的Random与S1实际上都返回128/O2，−3.015102秒差发生于相同目标配置的不同时段，不能归因于策略改变了固定配置性能。

S2近优次数未减少且成本门通过，但130363的风险upper=−13.548969pp，明确越过−2pp；155921端点跨−2pp。独立重算两项decision_before_reference_checks均为REJECT。相关原128/O3 range32.3638%越18%，配对Random155921返回该配置；原128/O1 range24.3169%只对相关Greedy结果标记。返回确认自身的range都没有超过18%。再按原同配置reference/confirmation差核得五条超过12%的冲突，正好是Random130363/O2、S1 155921/O2、S2 155921/O3、Random155921/O3、Greedy155921/O3。

根据冻结的诊断优先级，相关reference噪声/冲突使上述质量REJECT保守降为INCONCLUSIVE；没有成本REJECT被覆盖，两项都不是KEEP、retained=false。summary.json的条件、clear failures、端点、robust/possible数、near hits、成本及reference标记逐字段一致。后续诊断不能更换原t_ref、原在线feedback或原确认样本，也不能据此把失败门放宽为KEEP。

### 10.4 预注册诊断请求和下一步边界

从上述五条冲突独立按ConfigSpace canonical顺序去重，恰得两事件：第一为returned=reference=128/O2，影响Random130363与S1 155921，只需三份新样本；第二为returned128/O3与reference128/O2，影响S2/Random/Greedy155921，两配置各三份，采用AB、BA、AB次序。请求受最多2个selection事件限制，无warmup、无新增selection seed，合计9个target任务；与conflict_request_selection.json和conflict_selection_v1/plan.json的每个id/round/member/配置/repeat/seed完全一致。manifest冻结源码、protocol与request路径/hash也一致，215+9=224未超360总进程上限，9未超18诊断reserve。

实际只读审核首版误把manifest.conflict_request.sha256当成顶层conflict_request_sha256，产生KeyError；按真实嵌套结构修正审核读取后整套数值、请求、计划与hash断言exit0。没有修改工程代码、计划或raw，没有补测。本审核者批准时该诊断尚未启动；主控随后实际启动9任务，记录本节时仍在串行运行，诊断结果尚未审核，不冒称已结束。

**selection数据与诊断plan关口批准：没有影响结果的实现/派生数据阻塞，允许主控执行上述唯一预注册9进程诊断。** S1/S2当前均INCONCLUSIVE而非KEEP，后续holdout只能按冻结规则保留Random基础版本；实际holdout计划/原始数据和诊断完成结果仍待独立复算。此批准不增加搜索、修改阈值、采用增强或授予最终Engineering PASS。

### 10.5 报告修订闭环与审核快照

本审核者连续通读新增4(2)及internal optimization.md，与上表和原始停止轨迹对应。正式表9行基本算法的配置/median/g/运行数/wall、Greedy三个起点与有限推广、S1第二seed同配置时段差、S2错过第8项及负结果均如实说明；尚待完成的诊断/holdout句子保留其未结束状态，没有将待执行结果当成最终结论。

PR-01已改为“优化信息中唯一标为向量化的是计时后的checksum循环”，区分GCC备注和最终packed指令；PR-02图中方法改为build/measure/parse，与TargetProgram源码一致，两项关闭。新增P2 PR-03指出“后续确认低超过12%”不能覆盖全部O2/128确认：S1 104729/130363仅低1.1873%/8.3378%；主控已加“其中部分”，本审核者实际重新读取并断言该限定词存在，PR-03关闭。三项都是文字/标签修正，不改变冻结代码、规则或原始数值。

当前报告字节SHA：0398af23ee8acc8218a129bc0bcce7734b8aa9816d5cafc458c49a229d61a69b；SVG字节SHA：f6ef83292bb2623a0e4ecd2604b4b4577ef1040d5320b0946736d15089fa3bdc。报告后续还将补诊断/holdout，以上不是最终GitHub版本。

selection审核快照（后续加入诊断/holdout允许更新派生summary，原始文件不得改）：

- selection plan：0e6629e2f62abab18cf56bf3803497517883aa430e1219a3fddd4b9384431700。
- selection driver.jsonl：775ddb2b11564057583e7ba55b96b6cd459da1292e75ed9d71b25b49ae15477a。
- 31份selection journal集合：d41a55591e54dfae84d4f3ce4e5662281670bb9ec17bfaa734ca60e914d10a7f；集合hash定义同第8节。
- summary.json：1fa894182340ebeb3399666847465f6de3b786010ad325e3252193ab683ad361。
- measurements.csv：391b61624cc010b439bb9f76507991653fbec9044cd27cd49c605275f0e241fe。
- online_curves.csv：f8686d18812b6837c883203d757fdb31b8e24541e4ce7e2edec7cfce083e72c1。
- search_summary.csv：5eb883e2ceea3e38ea1602761d90674a349d2cb9617addb1dfffcfc2179ff2d1。
- batch_costs.csv：759c501b62997b190bfe28be81871b651d7ab0c4e91901ef5f382e40c765a282。
- conflict_request_selection.json：ac527ec2cc0d11e4fe0b9818fb81398500b5c2679aac3eb182327f7be278bdf7。
- conflict_selection_v1 plan：7a8c6f4aeeac2b3e2f9350da4f71f27efc4d3e2c9f5c8d261b4465b849a166fb。

本节所有独立raw/派生/接受规则读取命令均已实际exit0，compiler/target启动数0，新增依赖/配置0；未用unittest通过替代原始数据重算。完整最终report通读、诊断/holdout/曲线图和实际GitHub文件审核仍未完成。

## 11. selection冲突诊断完成与Random-only留出关口

记录时刻：2026-10-02 02:59:07 UTC。主控9任务实际exit0后，本审核者再次独立标准库读取reference61、selection31、conflict_selection9份journal及三份driver，合计101个独立run_id、224个真实target进程；完整raw/helper统计核对命令实际exit0。没有compiler/target启动、unittest、绘图或源代码/原始结果写入，锁ON约束继续遵守。

### 11.1 九份原始诊断和派生表

9份记录与第10节批准的两事件/配置/AB、BA、AB次序逐项一致，无warmup、额外seed或重试。重新检查全部header/fingerprint、冻结目标/框架/协议、affinity、compiler identity、实际cache binary SHA与历史build identity；每个trial唯一start/completion、配置/command/PID、repeat0、rc0/spawned=true/status=ok/stderr空、stdout首行finite positive和checksum=17180040496.458935，clock guard全部满足。9次版本探针成功、0次编译；CLI stdout的完整summary与journal末record相同且output路径正确，stderr文件全空。27条driver记录按计划串行、attempt_id0..8、完整wall已知，无中断或恢复。

从原始stdout独立分组计算中位数和相对原同配置reference差，与reference_conflicts.csv三行及summary.diagnostics完全一致：

| event | member | s/opt | 三个原样本秒 | median秒 | 相对原reference绝对差 | environment_drift | return_instability |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| 1 | both | 128/O2 | 37.563213 / 36.683041 / 39.436100 | 37.563213 | 4.902550% | false | true |
| 2 | returned | 128/O3 | 40.151283 / 40.911190 / 40.802387 | 40.802387 | 3.997855% | false | true |
| 2 | reference | 128/O2 | 40.804188 / 41.600006 / 41.061607 | 41.061607 | 3.954209% | false | false |

environment_drift只对reference/both成员应用原参照相对差>12%的事前规则；两项相关reference差约4.9026%和3.9542%，未触发门。它不表示不存在时漂，也不能确认宿主机频率或温度。return_instability以诊断median与同配置原selection返回确认比较；e1的128/O2及e2的128/O3均有差>12%，故前两项true，纯reference成员不把该条件当返回标记。没有将任何样本删除、把37.563213或41.061607秒替代t_ref，或据此重排在线历史/原确认。

所有原reference/selection journal集合hash、grid_summary、online_curves、search_summary字节hash均与第10节快照一致。summary原reference_median仍39.499706秒，两项selection决定、质量端点、成本门、原始失败门逐字段未变；均INCONCLUSIVE、retained=false，候选holdout状态NOT_REQUIRED。

### 11.2 完整成本与下一计划

九次诊断kernel总和359.013015秒、target process wall363.320939090秒、框架内部窗口363.506392784秒、完整外部CLI wall364.221829021秒；9次版本探针0.018835431秒已含CLI成本，无免费诊断。当前三个正式批次共224target、invalid=0、完整driver wall17950.152891439秒；batch_costs.csv及summary.costs各列全部与独立driver/measurement计数和求和匹配。准备、正确性、预测试仍各单列，以上不是整个项目总投入。

独立按冻结warmup、B8/r1、返回r3和三固定留出seed196613/229939/262147重建holdout计划，再与实际plan逐字典字段比较：schema/stage、原measurement_root、协议路径/hash、框架/target/driver hash和七项jobs完全一致。恰为warmup1、Random搜索3及各自依赖确认3；仅Random，没有候选/组合或新增seed。预定34个target进程，224+34=258小于360上限；当前wall未达57600秒，runner既有全局wall限制仍需执行时保持。审核时holdout目录仅plan.json，没有journal、driver或已启动测量。

**诊断原始数据与Random-only留出plan关口批准。** 可由主控串行执行这一个冻结计划；此关口不采用S1/S2、追加选择或修改阈值。诊断不能提升原INCONCLUSIVE为KEEP。实际留出原始结果/可能的一次预注册留出冲突事件、完整报告和GitHub最终审核仍待执行后核对，不授予Engineering PASS。

审核快照：

- conflict_selection plan：7a8c6f4aeeac2b3e2f9350da4f71f27efc4d3e2c9f5c8d261b4465b849a166fb。
- conflict_selection driver.jsonl：005c3ff9a42f6249108a2a448b7c4f46947620afdaca6ac60460cd9f19f952fd。
- 9份诊断journal集合：3bddb779929a3e3d19a0685b764c5d06fec3cf32b280250aff24223255510332；集合hash定义同第8节。
- summary.json：6a4139d6c87bd006345cb95eb75d01c454674b8684c8b7d548267fafe5e0f935。
- reference_conflicts.csv：5f85ac0afc38fbbd0a336e51fa4804abb2fba1ea2c1aa2f83f12e27f1cb57d90。
- measurements.csv：a98b86334ddde64517c26c021893563a066b3d969e1bf7a7546f8031d4369163。
- batch_costs.csv：962e0b47d2ce40ae36fd4861e423a70db9bb73bf7b073b812dbaecae40b3a755。
- holdout计划：03362796d14612cac9a2d622ea68146d712e37cc255fde9e7dbecef998c54cd5。

本审核者停止计算、测试和编译，等待主控留出结束后的新工作包。唯一改动仍为本文，无新依赖或配置。

## 12. 完整holdout与全部正式原始数据最终关口

记录时刻：2026-10-02 03:52:00 UTC。主控holdout七个CLI任务实际exit0后重生strict summary；本审核者才将完成记录纳入本节。接任务时先ls -la扫描并完整重读最新AGENTS.md；目录/一页老师题目/任务范围不变。仍只执行标准库JSONL/CSV/hash/统计、没有编译、测试、绘图或n4096；冻结代码/协议与全部raw均仅读，唯一写入本文。

### 12.1 留出预算、次序与原始输出

七份journal/21条driver记录全部结束，无partial、torn tail、失败、timeout、恢复或未知wall。独立逐字段核对plan、三seed196613/229939/262147、B8/r1/返回r3、实际affinity=[0]、source/frame/runner/protocol SHA、完整compiler identity/公共flags和四cache binary字节SHA；每份header canonical fingerprint正确。只含Random、warmup1、online24和返回确认9，合计34个target进程；7次版本探针、0新增compile。

独立按Random(seed)无放回shuffle20配置重建前8项，与每个trial完全一致：

- 196613：16/O3 → 128/O3 → 64/O0 → 8/O2 → 8/O0 → 8/O1 → 16/O1 → 8/O3。
- 229939：16/O1 → 24/O2 → 64/O0 → 24/O3 → 128/O1 → 64/O2 → 16/O2 → 64/O3。
- 262147：16/O3 → 16/O1 → 8/O2 → 128/O3 → 24/O0 → 8/O3 → 8/O0 → 24/O2。

所有初选与试探占预算，每轮恰8个不同配置；prefix best逐次由当时本轮score更新，严格更好才移动，没有读取参考表或确认值回填。三个seed都没有测到原观测最优128/O2，不隐藏这一限制。返回配置从相应搜索最后best确定，确认依赖正确，三个新样本未复用原测量。

34个measurement_start与completion按trial_id/repeat唯一匹配；每个实际spawned=true/rc0/status=ok/stderr空/error=null、命令/配置/PID/start/end一致。stdout两行重新解析为正有限时间与唯一checksum17180040496.458935，和kernel_s、score/median一致，均满足process wall+0.005秒clock guard。CLI stdout末summary与对应journal一致且output路径正确，stderr文件空；driver记录证明七个CLI严格串行。

| seed | 返回s/opt | online best秒 | 三个新确认样本秒 | 确认median秒 | g | 搜索+确认进程 | 完整search+confirm wall秒 |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 196613 | 16/O3 | 45.317799 | 43.493999 / 44.634007 / 44.424389 | 44.424389 | 12.467645% | 8+3 | 998.793670 |
| 229939 | 64/O3 | 41.704674 | 42.496933 / 41.582001 / 43.278969 | 42.496933 | 7.587973% | 8+3 | 618.051391 |
| 262147 | 16/O3 | 42.843807 | 44.296986 / 44.321510 / 43.848125 | 44.296986 | 12.145103% | 8+3 | 993.877322 |

原t_ref=39.499706秒不变，冻结近优门g≤5%下Random留出命中0/3。不能由selection的2/3近优推广为稳定命中，或将未保留候选当作在留出获得免费成绩。各返回确认range约2.5662%、3.9932%、1.0687%；均保留全部有效样本。

### 12.2 空冲突请求与实际成本

独立读取各返回配置的原reference中位数：16/O3为44.371098秒，64/O3为41.112492秒。与三次确认median的绝对相对差依次为0.120103%、3.367446%、0.167028%，均未超过冻结12%冲突门。重建conflict_request_holdout.json为schema1、source_stage=holdout、相同protocol SHA、events=[]，与文件完全相等；没有conflict_holdout_v1目录或诊断任务。

**留出不需再启动任何冲突目标进程。** 最多1事件是资源上限，不是必须填满；不得因近优0/3追加seed、重跑直到结果更好或更换参照。两候选selection仍INCONCLUSIVE、retained=false，候选holdout为NOT_REQUIRED，没有KEEP或组合接口进入留出。

holdout含warmup的kernel总和2642.373157秒、target process wall2658.706616616秒、内部窗口2659.137691733秒、完整外部CLI wall2659.654210891秒；7次版本探针0.014937509秒已含CLI成本。三个搜索+确认完整wall中位数993.877322秒；warmup单列，不计任何单次算法质量/比较成本。

全部正式四批次共108个不同run_id、258个真实target进程、0invalid，完整CLI driver wall20609.807102330秒，小于冻结360进程/57600秒上限。四阶段分别61、154、9、34进程；没有重复将cached build历史compile计入，四次共同准备仍另列，也没有省略诊断或返回确认。准备、预测试与正确性证据仍单列，正式CLI合计不冒称项目全部耗时。

### 12.3 全部派生表、不可变性与结论

此次独立重读全部reference、selection、selection诊断及holdout的原始记录，重新核对258行measurements.csv、132行online_curves.csv和18行search_summary.csv；所有配置、原stdout、有效性/rc、hash、当时分数、确认median/min/max/range、near标记、进程数和internal/full wall列完全一致。batch_costs.csv与summary.costs四阶段的实际完整wall、记录下界和资源上界均相等、unknown=false，不用内部窗口替代外部成本。

summary的原t_ref、selection两项条件/端点/robust/possible/收益/成本/REJECT→INCONCLUSIVE规则逐字段保持第10节结果，九次diagnostics保持第11节结果；原reference/selection/conflict_selection journal集合SHA和20配置CSV字节不变。summary中的四plan hash对应实际manifest，冻结target cece/framework0a71/runner9041/summarizer2630/protocol64bb均不变。

**全部正式实验原始数据与派生汇总关口通过，无未解决的数据/成本/空冲突请求错误。** 结果是S1/S2未保留、基础Random留出0/3近优；本审核者认可如实报告这些负/不确定结论，不认可增强性能提升、统计显著性或跨机器推广。这个数据关口不等于最终Engineering PASS：最终report完整连续通读、图/截图/链接、实际GitHub版本仍待主控冻结后独立核查。

最终测量快照：

- holdout plan：03362796d14612cac9a2d622ea68146d712e37cc255fde9e7dbecef998c54cd5。
- holdout driver.jsonl：3f82c70f8a6ade6b756a8c701d4088c2ce8b3d830d7bc7773488b41ccf4e7573。
- 七份holdout journal集合：8a268adc179e1f3525afaa35a8f0e8d30e7fbddb25703d5e4e7f38c3357d35cb；定义同第8节。
- summary.json：4fd2f0e7aa326880618f5d88e52afbd4f641c36265b6e4ec1c7baa4b0fae90de。
- grid_summary.csv：8f3bfbb506370076afe3a15f08cd1bcff8f5e23e34f05a5ec6e9e5702f6761ec。
- measurements.csv：f0659aa3f7ec75f1e4d14768c42d415b58e21958d4e3667f25ea3c0ab31f74c3。
- online_curves.csv：c54edb9e3243168c7783201912615cd07cab1cf050f461304865c488c130de26。
- search_summary.csv：9bbc2490e77476f40278f16eead5b053a0cc67b828b86e14346d1de548e31fbc。
- batch_costs.csv：b7d0a6a590b52cf6d7f91dddc32e1e8b4bdf12a9ed8689d468802651db700302。
- reference_conflicts.csv：5f85ac0afc38fbbd0a336e51fa4804abb2fba1ea2c1aa2f83f12e27f1cb57d90。
- conflict_request_holdout.json：02867ec65625cba6089a9bb02b6b02bd94fb0b2de88e750401ee3094999c5b5e。

所有独立复算命令实际exit0，compiler/target启动数0，没有新依赖或配置。本审核者等待最终图/截图/report稳定稿，继续只读与本文记录。
