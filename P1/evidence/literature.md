# P1 Goal 1 文献筛选与单项机制建议

检索日期：2026-10-02（Asia/Shanghai）。公开材料截止日为 2026-10-02。本文保留实现前的文献筛选与机制建议，不包含本机性能结论。文献筛选和候选机制确定阶段没有读取测量结果，也没有编译或运行性能程序；代码与协议冻结后，只读参照结果和已保存的汇编作报告解读，机制未改，阶段记录见 [agents.md](agents.md)。

## 1. 已确认的任务条件

已完整阅读根目录 `AGENTS.md`、`P1_Goal1_Codex_Prompt.md`、老师的一页 P1 PDF 和原始 C。正式空间为 `s ∈ {8,16,24,64,128}`、`O ∈ {O0,O1,O2,O3}`，共 20 个配置；`n=4096`、double 和六层计算循环保持一致。24 的尾块合法，初始化不在内核计时内。原程序没有结果校验，因此搜索策略不能替代正确性验证。

根目录原件和 `P1/src/matrix_multiplication.original.c` 的 SHA-256 均为 `188d011109c4470e1f41829216e8677a5c2d8f2b7c8a44215652320dbdf6de15`。文献筛选阶段建议的共同对照为无放回 Random Search，候选预算约 6–10、每配置重复约 1–2；这些数值在该阶段尚须由预测试和设计审核冻结。下文保留当时的建议，实际执行规则见 [protocol_v1.json](protocol_v1.json)。不得据正式全网格结果修改候选顺序或推定 O3 最优。

## 2. 紧凑筛选表

“读到正文”指下面明确列出的章节；不表示逐页阅读整篇。arXiv DOI 标识所选预印本，不能据此推定会议或期刊归属。

| 原始材料与作者 | 年份、版本、原文定位 | 实际阅读与原假设 | 对 P1 的选择 |
| --- | --- | --- | --- |
| **Autotuning Benchmarking Techniques: A Roofline Model Case Study**；Jacob Odgård Tørring、Jan Christian Meyer、Anne C. Elster | 2021；arXiv v2，2021-03-18；[PDF](https://arxiv.org/pdf/2103.08716v2)，[元数据](https://arxiv.org/abs/2103.08716)，[DOI](https://doi.org/10.48550/arXiv.2103.08716) | §III-C 的重复、在线方差及 CI 停止；§V 的实验设置；§VI-C 的精度/时间结果及表 VIII–XI。原任务是 BLAS DGEMM/TRIAD 的峰值性能测量，具有内外重复循环。正态假设与实际非正态分布有差异；一个系统需把最小次数提高到 100 才避免过早淘汰。 | 保留“对明显落后配置减少重复”的后备方向；拒绝把一两次观测称为可靠 99% CI。其性能指标最大化，P1 内核耗时最小化，比较方向必须转换。 |
| **Just-in-Time autotuning**；Elian Morel、Camille Coti | 2023；arXiv v1，2023-09-12；[PDF](https://arxiv.org/pdf/2309.06414v1)，[元数据](https://arxiv.org/abs/2309.06414)，[DOI](https://doi.org/10.48550/arXiv.2309.06414) | §3.2 的在线调优与参数状态；§3.3 的编译开销/收益关系；§4.1–4.3 的选择一致性、单次及累计开销；§5 的适用限制。使用 ClangJIT，多次调用相似输入以摊销编译和试探慢变体成本。 | 借鉴成本核算与有限投入的动机；不引入 JIT，也不改 P1 内核或假造未来调用次数。该文没有提出本项目的 patience 规则。 |
| **A methodology for comparing optimization algorithms for auto-tuning**；Floris-Jan Willemsen、Richard Schoonhoven、Jiří Filipovič、Jacob O. Tørring、Rob van Nieuwpoort、Ben van Werkhoven | 2024；FGCS 159，489–504，出版版；[大学仓储 PDF](https://pure.uva.nl/ws/files/182730825/A_methodology_for_comparing_optimization_algorithms_for_auto-tuning.pdf)，[DOI](https://doi.org/10.1016/j.future.2024.05.021) | §2.2 的常见比较缺陷；§3.3 的预算与两类随机性；§3.4 的随机对照和耗时评价；§4.6 与 §6 的讨论/限制。其演示主要是 GPU，并依赖可完整探索的搜索空间。 | 用于公平对照设计；保留实际运行数、wall time、种子分布及规则说明。论文中的仿真/计算随机对照不能替代本项目真实在线搜索。 |
| **MLKAPS: Machine Learning and Adaptive Sampling for HPC Kernel Auto-tuning**；Mathys Jam、Eric Petit、Pablo de Oliveira Castro、David Defour、Greg Henry、William Jalby | 2025；实际阅读 arXiv v1，2025-01-10；[PDF](https://arxiv.org/pdf/2501.05811v1)，[元数据](https://arxiv.org/abs/2501.05811)，[DOI](https://doi.org/10.48550/arXiv.2501.05811)。后有 [TACO 出版记录](https://doi.org/10.1145/3774418)，本建议不混用两版章节编号。 | §4.1.1 的 space-filling/LHS；§4.1.2–4.1.3 的 HVS/GA-adaptive；§4.2 的代理模型；§5.1–5.3 的采样效果与退化；§5.4 的适用规模。针对大输入空间、多设计参数，常需数千样本。§5.2 表明全局预测精度或覆盖好不保证调优配置好。 | 只借鉴有限预算覆盖，形成离散单维分层；拒绝代理模型、决策树、GA、跨输入迁移和数千历史样本。不会声称分层是 MLKAPS 的完整算法或该论文证明它一定胜过随机。 |
| **Estimating resource budgets to ensure autotuning efficiency**；Jaroslav Oľha、Jana Hozzová、Matej Antol、Jiří Filipovič | 2025；Parallel Computing 123，103126；[出版页](https://www.sciencedirect.com/science/article/pii/S016781912500002X)，[作者单位记录](https://www.ics.muni.cz/en/research/publications/2478850)，[DOI](https://doi.org/10.1016/j.parco.2025.103126) | 已核实元数据并读到出版页索引中的摘要、引言、章节开头；§3 的完整公式和算法、§4 的完整结果尚未取得。引言要求结合后续执行工作量判断调优投入，并指出单纯无改进次数不足以保证总体最优。 | 作为停止机制的限制提醒；完整方法未核实，**不作为某个具体预算估计算法已复现的依据**。P1 没有给定未来调用工作量，不虚构盈亏平衡结论。 |
| **CARBS: Compiler Autotuning via Randomized Biased Search**；Wei Li、Bin Gao、Weng-Fai Wong | 2026；HPDC '26，361–373，出版日 2026-07-13；[原出版页/DOI](https://doi.org/10.1145/3806645.3807592)，[作者代码](https://github.com/lv2020/CARBS) | 通过原出版页索引读取 §3.1–3.4 的概率、差异 flag 和历史更新，§3.6–3.8 的算法/复杂度，§4.1–4.5 的预算、种子与消融，§6。直接全文/PDF 访问失败，未取得完整 PDF。其原空间包含数百可独立开关的 flag；§4.2 报告预算增大后的收益饱和。 | 拒绝照搬概率向量、top-k 和动量组合；O0–O3 是四个整体级别，不能当作数百独立 flag。收益递减只提供有限停止动机，不能证明 P1 的早停有效。 |

OpenTuner 仅作为老师指定的历史框架入口：[作者 GitHub](https://github.com/jansel/opentuner)。本任务不把其早期工作改称 2021–2026 论文，也不引入多算法 ensemble 作为单项策略。

## 3. 三个轻量借鉴点

1. **覆盖候选值，而不训练模型。** 从 MLKAPS §4.1.1 抽取参数空间覆盖思想；P1 改编为优化级别分层的无放回顺序。原论文的 LHS 对连续区间和多维覆盖有自己的定义，本机制不冒称完整 LHS。
2. **把调优投入单独量化。** JIT 论文 §3.3/§4.3 与 CARBS §4.2 支持考察投入及递减收益；P1 可检验有限 patience 停止。patience 的具体规则属于本项目启发式，其质量损失风险必须用独立确认衡量。
3. **昂贵重复应有有限分配规则。** 2021 年论文 §III-C 给出统计停止的原机制。P1 若预算允许，可用首测与预测试噪声界判断是否执行第二次，属于阈值简化，不能称统计上安全的 CI 淘汰。

上述均为机制建议。本机是否改善只能由后续在线实验得出，文献中的速度比和配置不能移作本机结果。

## 4. 建议的两个单项及一个后备

### S1：优化级别分层无放回（推荐探索候选）

假设：有限预算的普通随机可能遗漏某一优化级别；平衡访问四个级别能降低这种遗漏带来的种子差异，改善找到的配置质量。

唯一改动是候选访问顺序：将 20 配置按 O 分为四层；每层独立用 seed 打乱五个 s；每轮用 seed 打乱四个 O，各取该层下一个尚未访问的配置。预算内各 O 访问数最多相差 1，前四步覆盖四级，20 步完整无重复。不得按预测试速度排序层或 s，也不为 O3 提高权重。

单纯组合计数可说明覆盖假设：均匀无放回随机抽取 B 个配置，至少遗漏一个 O 的概率为 `Σ[k=1..4] (−1)^(k+1) C(4,k) C(20−5k,B) / C(20,B)`（不合法的组合数按零计）。Python `math.comb` 计算 B=6/8/10 分别为 48.40%/20.22%/6.50%；这是空间结构的理论概率，**不是性能实测**。S1 在 B≥4 时消除此类遗漏，但两种规则对任一个固定配置的入选概率仍均为 B/20，因而不能提高唯一最优点的理论命中率；它改变配置间联合覆盖，质量是否受益仍取决于未知性能分布。

共同对照为普通无放回 Random Search。两者用相同 B、r、目标、构建缓存、测量统计和最终确认流程；各轮 seed 预定，算法运行顺序交错。S1 不免费读取网格表、不增加候选试跑，实际进程运行上限仍是 `B*r`。新增 Python 候选编排时间计入总 wall time。

主要检验同预算确认质量与跨 seed 分布；同时核对总 wall time。风险是强制覆盖某些较慢层而减少其他层探索，可能质量或耗时均无收益；不能用覆盖数本身宣称性能提升。B=20 时两者覆盖相同，有限预算结果不能泛化为全空间优势。

### S2：固定随机顺序上的有限 patience 停止（推荐成本候选，待协议冻结）

假设：在相同随机无放回候选顺序上，允许在连续若干次没有实质改善后停止，可以节省评估成本，同时最终返回配置的确认质量维持在事前容差内。

只改停止条件；候选生成保持基线 Random Search，r、评分和平局规则不变。建议预测试后冻结最少评估数 `k_min=5`、`patience=3`、相对改善界 `δ` 与硬预算 B。每次有效测量按原规则更新真实 best；若相对前一步 best 的改善超过 δ，停滞计数清零，否则加一。达到 k_min 且计数达到 patience 后停止。δ 只可由预测试噪声和可解释的最小收益确定，不能看正式候选结果后放宽。

同一个 seed 的 S2 候选列表必须是基线列表的前缀。未测候选不能参与 best 比较；日志须保存实际步数、best、计数和停止原因。预算小于 k_min 时运行至预算；失败/超时仍按统一预算和失败规则计费，不能被早停计数隐藏。

新增性能运行上限为 0；若 B=8 且 r=1，最早第 5 步停止，相比基线最多省 3 次搜索运行。共同确认开销照常计入。早停可能错过后续关键配置，且噪声会误触发或延迟停止；仅凭无改进轨迹不能证明剩余空间无优配置。接受条件应以确认质量不退化与真实进程数/总时间实质减少为主，质量明显退化则 REJECT。2025 预算论文尤其限制了把该规则叫作“最优预算估计”的说法。

### 后备：首测落后者跳过第二次重复

只有在共同基线 **r=2** 且成本允许时才替换 S2，不与其并用。保持基线随机候选顺序与 B；第一配置测两次建立 incumbent，以后每配置先测一次，若首测明显慢于 incumbent 并超过冻结 margin，则不做第二次，否则做第二次。margin 依据预测试噪声，最终评分统计和返回配置确认规则固定。

基线搜索上限为 `2B` 次，此后备搜索约 `B+1` 至 `2B` 次；所有重复、失败、确认都计实际运行与 wall time。它不会在 r=1 基线上产生“省掉不存在的重复”的收益。一次首测可能被干扰，两个样本也不足以可信估计尾部概率，因此只能作为待证启发式；不得为被跳过者伪造第二次样本。若没有足够噪声估计或预算，保留 S2，不做此后备。

## 5. 比较和接受设计交接

- 正式测量前由主控/实验/审核共同冻结同一已审核基线哈希、B、r、探索与确认 seed、预热、超时、失败计费、统计量、δ/epsilon、最小收益和允许退化范围。两个候选只各改一个主要因素，不执行 S1+S2。
- 两候选各至少三个预定探索 seed。相同 seed 便于配对，但不能要求 S1 和基线访问同一配置集合；S2 必须保持随机基线顺序的前缀。确认种子至少三个，未用于选择或调参。
- 质量用共同确认得到的 `t_found` 与独立全网格参照 `t_ref` 比较，报告 `g=(t_found/t_ref−1)×100%`、近优命中及原始分布。参照是观测最优，有冲突时复核，不将名称当真值。
- 同时列候选提议数、不同配置数、实际进程运行数、失败/超时数、编译时间、kernel time 和调优总 wall time。搜索得到较好的配置不代表固定二进制的内核因搜索规则而加速。
- S1 优先同预算质量改进；S2 优先质量在预定容差内的成本下降。阈值在正式比较前写入协议；没有量化收益则 REJECT，无法区分则 INCONCLUSIVE，并且只在预定上限内追加。不得使用加权总分掩盖取舍。
- 若采用 r=1，每个候选 B 次搜索运行及共同最终确认；两个候选、三探索 seed 的候选组成本不超过 `6B` 次（基线组另计）。r=2 时上述上限翻倍。每个 KEEP 的独立确认都需另给候选和匹配基线真实运行，不复用选择数据。最终资源预算以冻结协议为准。

## 6. 获取失败与阅读边界

检索确实包含明确的 2025 和 2026 查询，例如 `2025 autotuning program configuration measurement noise adaptive sampling early stopping primary paper`、`2026 kernel autotuning search budget sampling benchmark repeat measurement paper`、`2026 autotuning benchmarking confidence intervals performance noise stopping site:arxiv.org`。也对论文题名、作者和方法章节进行了定向检索；没有按每年强行凑材料。

成功取得三个指定 arXiv PDF，以及 2024 年大学仓储 PDF 的正文。2026 CARBS 的方法/实验/限制相关出版正文通过原出版页搜索索引取得，章节范围见表；这不等价于完整 PDF 阅读。2025 资源预算论文只能取得有限原文片段，其完整方法仍未核实。EVADyR（J. Comput. Sci. 84，102468，[DOI](https://doi.org/10.1016/j.jocs.2024.102468)）检索到出版摘要，但未取得方法原文，未据此实现算法。

失败记录：

| 日期 | 路径/动作 | 真实结果与处理 |
| --- | --- | --- |
| 2026-10-02 | Web 打开资源预算论文 ScienceDirect 原页 | `403 Forbidden`；转查作者单位元数据与 SSRN。 |
| 2026-10-02 | Web 打开 CARBS DOI、ACM `/doi/full/` 与 `/doi/pdf/` | `403` 或工具 Internal Error；改读原出版页索引，不伪称已下载 PDF。 |
| 2026-10-02 | Web 打开 SSRN 4661862、5000678 及 5000678 的 Delivery PDF | 工具 Internal Error，未取得完整方法；不采用未核实公式。 |
| 2026-10-02 | Python 标准库 urllib 获取 SSRN Delivery PDF、CARBS PDF | 两项均 `SSL: UNEXPECTED_EOF_WHILE_READING`；非 PDF 未落盘，未安装依赖。 |
| 2026-10-02 | 后续 Web 原文补充批次及一次重试 | 两次 `connection failed: error sending request`；保留已有可核实原文，未填造缺失内容。 |

不保存下载原文到 Git；本工作包未安装系统包、语言包或工具链，未改变环境配置。所有候选的本机实现、性能试验与 KEEP/REJECT 判定由后续工作包完成，不能从本文推定它们已验证。
