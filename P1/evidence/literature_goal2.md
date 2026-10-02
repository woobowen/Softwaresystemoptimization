# Goal 2：重复测量、预算与时钟资料核对

核对日期：2026-10-02（Asia/Shanghai）。这里记录实际读到的原文与方法边界，不包含本机性能结论。Goal 1 的 [literature.md](literature.md) 保留原样；本次不新增模型、进化搜索或组合策略。

## 1. 实际借鉴与限制

| 原始材料 | 实际版本和阅读位置 | 原方法、假设 | 本项目使用 |
| --- | --- | --- | --- |
| Jacob Odgård Tørring、Jan Christian Meyer、Anne C. Elster，**Autotuning Benchmarking Techniques: A Roofline Model Case Study** | 2021，arXiv v2（2021-03-18），已重新取得 [正文](https://arxiv.org/pdf/2103.08716v2)，§III-C、§V、§VI-C，PDF pp.4–8 | 重复内核与进程调用；在线均值/方差构造正态近似 CI，按精度或低于当前最佳性能的 CI 上界停止。正文承认分布经常非正态；默认最低两次在部分平台不足，需要100次避免过早淘汰。 | 只借鉴有限重复分配的动机。S3 是先探索六配置、对首测两候选各复核一次的项目启发式；不实现原 CI 淘汰，不称两样本提供99%保证。原 BLAS/OpenMP 与本题六层循环不等同。 |
| Floris-Jan Willemsen、Richard Schoonhoven、Jiří Filipovič、Jacob O. Tørring、Rob van Nieuwpoort、Ben van Werkhoven，**A methodology for comparing optimization algorithms for auto-tuning** | 2024，FGCS159，489–504，[DOI](https://doi.org/10.1016/j.future.2024.05.021)，已重新取得 [大学仓储出版正文](https://pure.uva.nl/ws/files/182730825/A_methodology_for_comparing_optimization_algorithms_for_auto-tuning.pdf)，§3.2–3.4，PDF pp.7–11 | 分开测量噪声和算法随机性；计数预算不能替代wall时间；重复可能非iid。完整空间可支持事后随机参照，但论文的计算随机基线和大量重复不等于真实在线测量。 | 共用R=8，六新种子真实独立搜索；内核、目标进程、编译、driver和共同评价分账；统一配置身份的事后参照加成组确认。不用原计算基线代替真实Random，不对六种子套正态CI，也不强制S3修正后的在线估计曲线单调下降。 |
| Elian Morel、Camille Coti，**Just-in-Time autotuning** | 2023，arXiv v1（2023-09-12），已重新取得 [正文](https://arxiv.org/pdf/2309.06414v1)，§3.3、§4.3，PDF pp.4–5 | 编译及试探慢变体有开销，需要后续多次调用摊销。 | 继续使用真实调优成本；本题没有未来调用次数，不宣称已实现应用总收益或盈亏平衡。该文没有提出S3六加二规则。 |

以上三个借鉴点分别是有限重复、公平预算/随机性比较、成本核算。S3 不因文献支持重复测量就被预设为有收益；减少两个不同配置的探索是必须实测的代价。正式接收规则和本机结果见新协议及优化证据。

## 2. 有限的2025—2026补查

检索实际包含 `2025 2026 autotuning measurement noise repeated sampling candidate re-evaluation paper arxiv`、2025预算论文题名和2026 CARBS题名，没有按年份凑数量。

| 原始材料 | 本次实际获取 | 对本轮的限制 |
| --- | --- | --- |
| Jaroslav Oľha、Jana Hozzová、Matej Antol、Jiří Filipovič，**Estimating resource budgets to ensure autotuning efficiency**（2025，Parallel Computing123，103126） | [出版索引正文](https://www.sciencedirect.com/science/article/pii/S016781912500002X) 的摘要、完整可见引言及各节开头；未取得§3完整公式与完整PDF。 | 再次确认优化预算需要未来执行工作量等条件；不实施未取得的公式。不能据本题有限早停/复核推定最优投入。 |
| Sichen Wang、Zhipeng Lu，**Depth over Fidelity in Fixed-Budget Noisy Evolution Strategies**（2026） | [arXiv v1元数据](https://arxiv.org/abs/2606.06555)及[正文](https://arxiv.org/pdf/2606.06555v1)，提交2026-06-04；实际读§3.1–3.5、§4开头，PDF pp.2–4。版本按arXiv记录引用，不单凭PDF页眉扩大出版确认。 | 固定调用预算把重复、探针全部计入；增加重复会减少探索/更新次数。其连续CMA-ES、iid条件和残差池不适用于本题时段漂移；不加入RB-PEM、bootstrap或probe-and-switch，只用作复核代价的限制说明。 |
| Wei Li、Bin Gao、Weng-Fai Wong，**CARBS: Compiler Autotuning via Randomized Biased Search**（2026，HPDC26，361–373） | [作者出版页](https://doi.org/10.1145/3806645.3807592)的题名、作者、2026-07-13日期和公开摘要元数据，[作者仓库](https://github.com/lv2020/CARBS)存在；本次未重新获取完整方法PDF。 | 与四个整体O级别的20配置结构不同。未新增概率flag搜索，不把它称为S3来源，也不继承其加速比。 |

## 3. 官方计时资料与只读边界

[Linux clock_gettime 手册](https://man7.org/linux/man-pages/man3/clock_gettime.3.html)实际读取了各时钟语义：MONOTONIC避免离散墙钟跳变但仍受渐进调频影响；RAW不受NTP渐进调整；CPU时钟累计进程使用的CPU时间。BOOTTIME包含挂起时间，但与MONOTONIC相关，使用它控制idle探针不提供绝对准确度证明。所有ns差先按整数相减，再换秒；不能拿不同域的kernel和process直接作大小保护。

[Canonical WSL时间同步文档](https://ubuntu.com/wsl/docs/stable/explanation/time-sync/)（页面更新2026-04-16）提到Hyper-V隐式同步与用户空间NTP可能冲突，以及24.04/后续版本的差异。这是本机只读服务检查的线索，不能由文档认定本机约1.09比率的根因。主控实查记录在 `environment/goal2.json`；本次没有执行文档里的停用服务、NTP配置或内核参数命令。

浏览成功获取上述三个指定正文和2026补查正文，未安装依赖、未将论文PDF加入仓库、未修改全局设置。阅读范围按本表保留；没有声称全部原论文都逐页读完。
