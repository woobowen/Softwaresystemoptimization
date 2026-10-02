# P1 Goal 1 滚动计划

首个时钟记录：2026-10-02 02:11:09 Asia/Shanghai（首条目录扫描略早）。一次性任务；本文件是用户明确要求的内部滚动记录。

## 已确认事实与边界

- 工作目录 `/home/addaswsw/lab/Software_system_optimization`，授权 GitHub origin、main 与实际仓库匹配；起始 local/remote SHA 均为 `9b0ca66cdd218de034ba2c29979bcbfa9307e1fb`。
- 根目录用户提示词、原 C 和 PDF 保留。原题全部读取；仅 P1、必要根 AGENTS/.gitignore/最小索引属于本次改动范围。
- 原题顺序：1 三接口、框架图和优缺点；2 附件矩阵；3 s={8,16,24,64,128}×O={O0,O1,O2,O3}；4 完整 Grid 与自行实现另两搜索的比较；正式报告 `report.md`。
- 老师截止 2026-10-28 24:00；未来水杉需自建 `project01`。本阶段不操作水杉、不组合策略、不改矩阵内核/规模、不使用 GPU/BLAS/多线程、不宣称最终 Engineering PASS。
- 本次授权内部审核后直接 GitHub commit/push main；不推广为未来任务自动发布授权。

## 当前可靠版本与冻结条件

测量 checkpoint `dea74febda56aa4a2ef8eaa877068d5523bf1842`；目标 SHA `cece4fd572c1d25e9f9a7d045c21e8d77b25079a6f71513de0385d0d85d44835`，框架 SHA `0a71c2fdb0d3d41be261c9aecc86b87487990dbc3bfd4e6b34e79b7fbd75ab49`，协议 JSON SHA `64bb8f6c66e70de2c9a53960cbd693447ecebaa43a258f21439bd2827e4b0f66`。全部核心源码、测试、协议 bytes 与该 checkpoint 相同，完整列表见 baseline_snapshot.json。

n=4096、double、原六循环/默认矩阵初始化，统一 CLOCK_MONOTONIC 且原计时边界不变；公共选项 -std=c11 -Wall -Wextra，仅 O0..O3；CPU0，运行 timeout1200秒。正式共同四级构建 compile0.537284秒、完整 driver0.610331秒，全部正式运行 cache hit；前期 API 整数 timeout 与 CLI 浮点 timeout 键表示不同，两组四构建真实记录保留，不称整个任务只编译四次。

阶段保留 grid/random/greedy 三基础算法。stratified 与 patience 只作为两个独立实验变体保留，选择结论均 INCONCLUSIVE、无 KEEP、不作为推荐策略；未运行第三候选或 S1+S2。

## 责任与验收

主控是目标/验证/报告/集成与唯一正式测量 owner；framework 是框架实现 owner，后续独立审核其他作者的实验/报告；literature 是资料、实验编排/汇总及协议 owner；code_review 独立实查框架/目标/测试与隔离复现。每个产物只有一个修改 owner。可核实角色、调用与跨阶段职责见 agents.md；具体问题和关闭证据见两份 reviews。

## 已完成

- 首命令 ls -la、目录/Git/环境检查、逐份原题与附件阅读、原始 C 字节留存及输入哈希记录；主控+三个原生子代理实际协作。
- 三接口、统一评估器、构建复用、真实进程失败/超时处理、有限预算、持久化与安全恢复；31项框架和23项实验测试分别独立通过。干净clone的完整54项实际通过（7.615秒，无skip），不用历史53项冒充当前总数。
- 同源小尺寸128/129×5s×4O×6输入共240用例、5 ASan/UBSan、正式大矩阵两组各24点通过；独立上下文另240小例+5 sanitizer。原/适配O3计算及四级代表汇编核查完成。
- 当前目标九次预测试和有界三次噪声诊断；正式方案在成绩产生前冻结并经过两类独立关口。
- 2021—2026原始论文检索、六项筛选、三个重点原文方法/限制阅读，明确全文获取限制；两个单因素机制/接受门事前固定。
- 全部四批正式实验已结束，无后台正式任务；数据审核逐条重算258条有效测量、132条在线曲线、18轮搜索汇总及所有成本，未发现不一致。

| 批次 | 实际目标进程数 | 完整 driver MONOTONIC 秒 | 内容 |
| --- | ---: | ---: | --- |
| reference_v1 | 61 | 5569.810460 | warm1+20配置各3有效样本 |
| selection_v1 | 154 | 12016.120603 | warm1+108搜索+45返回确认，五独立规则×三seed |
| conflict_selection_v1 | 9 | 364.221829 | 最多两配置的预注册诊断，无预热 |
| holdout_v1 | 34 | 2659.654211 | warm1+Random三新seed各8搜索+3确认 |
| 总计 | 258 | 20609.807102 | 失败/计时排除0，共同准备编译和前期/复现另列 |

t_ref=39.499706秒（O2/s128），原参照20表每配置3有效，全部快慢样本保留。O1/s128、O3/s128相对范围24.32%/32.36%；不追加直到满意，不替换原 t_ref。选择阶段两个单项的初始数值判定均 REJECT，相关噪声/冲突规则使最终 INCONCLUSIVE。预注册9次诊断仍不支持保留；诊断不能把INC升级KEEP。

留出seed196613/229939/262147分别返回16/O3、64/O3、16/O3，确认中位数44.424389/42.496933/44.296986秒；近优0/3，不能称Random稳定达到5%近优。没有KEEP候选，所以候选留出为NOT_REQUIRED；基础Random三新seed实际执行。留出确认相对同配置原参照均未越12%门，conflict_request_holdout.json为空，无额外诊断。正式258进程/20609.807秒在360进程/57600秒的预注册上限以内。

- report.md已有全部真实结果，框架SVG、两个可重生成数据图及两张真实xterm截图；图片已实际查看，最后一张干净构建/运行截图已补并实际查看。正式结论未写入内部审核术语。
- 根AGENTS已合并长期规则，报告文件名以老师要求为准；根README仅增加P1入口。

## 最后复现与当前状态

本地数据/文稿checkpoint `9ba1427137fadbb17b8f99cf7a8c10ed7ec061d9`，实际 `git clone --no-hardlinks` 到独立临时目录，初始git status空且无P1/.cache。code_review在主控授予的独占窗口实跑54/54测试（7.615秒，无skip）、四级冷编译和唯一一次CPU0/O3/s128 n4096。编译实际四个binary SHA与正式四构建相同；新运行kernel30.583361秒、process MONOTONIC31.160817秒、完整CLI31.229703秒、rc0、checksum17180040496.458935、clock guard通过，run cache hit/新增编译0。该单次仅用于复现，绝不替换原参照或混入258正式样本。

9个保存CSV/JSON的文件集合及bytes完全相同；两PNG重生成逐bytes相同，实际查看可读；final_snapshot341份数据SHA匹配，P1/results全358文件前后SHA不变。必要原始command/stdout/stderr/build/run/inspection/comparison在 reproduction/，缓存/二进制/临时checkout不入Git。源码、协议、测试和正式数据仍冻结；复现后仅新增报告图片/说明及恢复措辞准确性修正、证据和审核。

实验/报告审核已连续通读§13实际文稿、现有五图和全部表/链接；最后新增真实运行图及“只继续尚未开始repeat、失败不重跑”的一句均由原审核者复核关闭。最终代码/隔离复现与实验/报告两独立关口已实际落盘批准，分别见 reviews/code_review.md:271与reviews/experiment_report_review.md §14；不以测试自动替代审核，也不授予最终Engineering PASS。

下一步：两独立关口落盘并关闭问题 → 检查完整最终文稿/文件/links/secret/范围 → 安全正常commit/push GitHub main → 实际ls-remote核对local/remote SHA及远端文件树。当前已fetch确认远端仍起始9b0ca66；尚未push，不称远端完成。用户本次已授权发布，剩余步骤不反复请求确认。

## 已解决问题与限制

旧 gettimeofday 预试四个样本 kernel 时间超过进程 MONOTONIC wall；第五项是我方SIGTERM安全停止，原始数据保留在 pretest、不能进正式成绩。改为同一计时区间 CLOCK_MONOTONIC 后一致性检查与数值回归通过；未定位系统级根因，统一时钟不等于绝对校准或没有噪声，UTC/RAW只作诊断不代替成本。

缩小验证器首次因插入参考函数重复return marker而生成失败，修正生成顺序后回归通过，错误日志保留。完成日志设置校验、spawn后日志异常清理、torn成本、完整外部driver计费、有效退出码和唯一启动/完成记录等审核问题均已修复并交原审核者关闭；参照/选择/诊断/留出零正式失败。

真实截图采用独立 Xvfb TCP+xterm+ffmpeg；唯一局部下载的xterm不作全局安装。原生线程总上限4导致复用资料角色承担实验设计；不虚报第四子代理。WSL2 PMU实际不可用，不编造perf、频率、温度或物理核心信息。当前无阻塞正确性/正式实验的未解决问题；测量波动、三个seed和抽查证明范围作为结果限制保留。
