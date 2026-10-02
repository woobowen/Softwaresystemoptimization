# Goal 2 实验与报告独立审核

审核者：`/root/implementation`，独立于方法/分析作者。状态：**CLOCK_BLOCKED_ADAPTATION_FEASIBILITY_REVIEW_PENDING_EVIDENCE**。正式参照曾在冻结提交 `6463e2a3ab507debf02204d555c1f2083257235e` 启动串行测量，第一预热后因完整时钟门停止；本记录只审核实际证据和文稿，不提前认定新的性能结果。主控唯一拥有报告/README，本角色没有修改它们。

## 连续阅读与原题核对

从头至尾阅读完整 `report.md`、`README.md`、冻结 `protocol_v2.md/json`，重新提取并阅读老师原 PDF 全文。题目要求三个接口及框架图和优劣说明，附件 Matrix Multiplication，严格五个 s、四个 O，完整 Grid 和另外两种自行实现算法，Markdown 图片、源码重点和 OS/CPU/编译器；报告保留用户要求的内存。老师截止为 2026-10-28 24:00，`project01` 为后续教师提交分支，本阶段 GitHub 仍是 main，不创建或提交教师分支。

当前 report SHA `1e0ddf846a060ca6c17e58e14e6627d9d5c8508a794fd09796aea4f1ea01e4bc`，README SHA `41322069f4d5fe074486510715d414e11f7597aaa983387d6628cc0f8308001b`，新协议 JSON SHA `8ff12729a65650da1e45ff0b29be79b863d733765ae4da16a45451a904aaa78b`。报告还是有明确来源标识的 Goal 1 结果；没有把其表格当作已完成的新正式参照。全文按老师 1、2、3、4 顺序展开，身份、环境、三个接口、参数与算法说明均存在，最终内容/数字/图片审查待新数据。

本阶段只执行轻量文件读取和 PDF 文本提取，没有编译、测试、绘图、GUI 或 n4096；全局性能窗口保持由主控占用。

## 给报告 owner 的具体建议

| ID | 位置 | 具体修改与理由 | 当前状态 |
| --- | --- | --- | --- |
| ER1 | `report.md:27–36` / `autotuner.py:561–569` | 现循环片段只对应三基础算法。注明基础路径即可，或展示 S3 把 strategy 交给 Evaluator、内部观察 fresh_score 的实际分支；不要重复 observe 聚合分数。恢复细节移证据，正文保留所有试探占预算/失败不参与最优的必要解释。 | 待 owner 文稿修订 |
| ER2 | `report.md:64–80` | 当前旧参照/预热为 s128/O3；新冻结协议是 s128/O2、三轮完整遍历和九锚点。等真实参照结束再替换 20 个中位数/波动和来源链接，O0/块大小/s24尾块/标量汇编的解释只保留与新构建及数据对应者。 | 待实际新完整参照 |
| ER3 | `report.md:87–109,119–127` | 三旧 seed、算法专属三个确认、旧 g 和 8+3 成本不能描述六块共同面板。新主表用身份相同的 g_ref 和同块新 panel 分列，保留近优/明显较差/不确定；搜索含内部复核，共享外部成本只在项目账记一次。种子逐轮明细可链接，正文保留分布与严重失败/起点例，起点面板另列。 | 待实际主比较及确认 |
| ER4 | `report.md:45,76,111–131,148` | 同一 MONOTONIC 没有消除时段变化；用一次简明段落解释独立 A/A 的大波动与细排序限制。旧 S1/S2/留出长过程移证据，保留简短历史负结果。内部批次名改来源链接，重复截图“没有重跑/没有混入”用一处必要图注。 | 待 owner 精简及新结果 |
| ER5 | `README.md:3` / `safe_screenshots.py:89–95` | native Xauthority 由标准库写入，不需要 xauth；实际依赖包含 ss/iproute2。xterm 有忽略缓存回退，干净 clone 不应默认有该目录；说明具体局部工具检查/复用，并在最终干净环境实际执行 README。 | 文档修改与干净复现待完成 |

README 已将旧重生改为匹配 3ac/2fc/c247 固定 checkout，历史 CR1 的文档修订可以静态确认；最终仍须实际执行新 README 整套流程，不把链接存在当作复现完成。

## 后续独立验收边界

待主控结束参照/主比较后，本角色要读完整 plan/journal/stdout/driver/指定账本快照，独立重算参照、在线轨迹、共同确认、S3 配对与必要新种子，以及真实计费。不同配置风险支持 flag 为 false，fine 5%/2pp 结论不能靠扩大 rho 或换 seed 放行；同身份质量映射为零，实际搜索效率另判。最终报告连续重读、所有图逐张实际打开、干净复现和发布内容另审。当前没有最终图片视觉通过、性能 KEEP 或最终 Engineering PASS 声明。


## 完整参照启动失败与计时适配的静态边界

正式参照的第一预热进程结束后，完整目标进程及 driver 的 RAW/MONOTONIC 比例相对同 boot 首个区间超过冻结的 2% 门，批次实际停止；尚无新参照样本。这里只读 `warmup-reference.jsonl` 和对应 primary end，独立从三域原始 ns 做算术：kernel MONOTONIC 32.742920 秒，进程 MONOTONIC 33.337630412、RAW 33.990309693、REALTIME 33.937446023 秒；q=1.0195778546。进程与 driver 相对首个的变化分别为 2.15023426%、2.10346382%，保存 guard 完整且 conflict=true。程序退出 0 与输出可解析不使该样本成为有效正式成绩；实启一次和 MONOTONIC driver 33.558745205/max域34.217699605秒保留成本。

主控正在执行有限的 idle/fixed-work 四域探针。方法作者须判断证据是否足够；本角色只评估最小代码边界，没有选择新计时器、写代码、运行测试/编译/目标或放宽门槛。

| 边界 | 若另审证据支持换计时器，最小必要修改/复核 |
| --- | --- |
| C 的 start/end | 最多改两处为同一已明确选择的域；原 n/double/初始化/六层循环/尾块/计时外 checksum 不变。不能只改一端。 |
| TargetProgram 的身份与上界保护 | `autotuner.py:163` 只识别 MONOTONIC；RAW 会成为 unknown。`measure:271–274` 仅域等于 process_wall_clock 时比较，故单换 C 会跳过上界保护。识别一致的 kernel 域，明确检查 `kernel_s <= clock_deltas_s[kernel_clock] + 0.005`，缺/混合域不成为有效正式测量。 |
| 进程/driver/资源成本 | `process_wall_s` 和既有 `driver_wall_s` 当前明确是 MONOTONIC。可保持该真实含义并使用已有 RAW delta 作 kernel 同域保护；若新协议选 RAW 主成本，应另明确实际 RAW 边界/字段或派生列，不能重命名旧数值。16小时和520调用总账仍累计原任务，max域资源账不重置。 |
| 完整 clock health | 现 driver 与分析分别重算 RAW/MONO first/previous。只改 kernel timer 不会修复已触发的比例冲突；改变 health 比较来源/政策是新的方法决定，须实际诊断、两类审核、新冻结协议，不是删 guard 或换首个基准的代码修复。2% 不自动放宽。 |
| 数值/汇编 | `validate_target.kernel:15–17` 的结束 marker 写死 MONOTONIC，要最小支持明确的新边界。同源 kernel hash、小矩阵全元素/尾块和 sanitizer、必要大 n 抽查及代表汇编需重新检查；不能沿用旧目标源码身份。 |
| 严格分析/历史 | `common_metadata`、`validate_task`、`valid_measurement`、`formal_clock_health` 与成本复算的硬域假设同步；在线进度时轴/编译/调优成本分别标域。新 target/framework/build SHA、新协议/批次；旧失败、旧 raw/header/判定和旧派生保持原样，由固定提交重算。老过程域与新源身份不能靠放宽 SHA 检查兼容。 |

同一区间四域关系可以支持一个受限候选计时选择，却不把 RAW 变成绝对真值；CPU 时间不能替代真实等待，两个探针也不证明数小时稳定或 5% 分辨能力。若审核无法建立可比性，性能分支保持阻塞：老师所需完整 Grid 可继续展示真实 Goal 1 表及其出处，但新 20 配置参照没有完成，新六种子三算法与 S3 必须注明未执行，不能借旧数值授予新 KEEP/REJECT 或 Goal 2 COMPLETE。该情况仍可完成真实报告/图像/复现/阶段发布审核，不因计时阻塞跳过无依赖交付。

本段记录的第一次纯审核序列化命令有一个多余右括号，解释器在执行写入前报 SyntaxError；删除该括号后保存成功。没有修改源码、原始数据或协议，也没有因此启动新测量。
