# 固定八次 RAW A/A：独立代码关

审核者 `/root/review`，不是执行器、计时适配或分析器作者。此关只批准下列八次诊断在最终冻结条件满足后执行；不批准完整参照、搜索、原 MONOTONIC 批次恢复或最终 Engineering PASS。实际结果另写 `goal2_raw_aa_result_review.*`，本文件与同名 JSON 到此冻结。

## 实际回归与读取

独立授权窗口 2026-10-02 20:44:26–20:44:28 UTC，持真实 `P1/.cache/performance.lock` 非阻塞排他锁，实际运行 driver 36 项与 followup 13 项，共 **49/49 通过**，报告 1.899 秒；三文件语法检查返回 0。两个实际 attempt 是 `ffeb4c141fcf4b96aa72bb94163de8bb`、`b39c42086528447f9427d27a4a15e18d`，资源计费分别 2.086520273、0.265043751 秒，均 0 个 n4096。原始命令、stdout/stderr、三域 ns、前后哈希保存在同名 JSON 和 `commands/goal2-raw-aa-driver-independent-*`。测试前后源码、8ced 时钟历史、51dc 数值绑定未变，锁已释放。

连续读取最终 driver、相关测试与 RAW 分析路径，严格 known 修补只把新矩阵基准的调用覆盖要求固定为 `is True`；不能把缺失、1、字符串 true 或未知值当作已知。旧兼容只允许精确验证过的旧 ledger 前缀，新矩阵仍需要真实 journal、schema 2、完整逐过程/driver 守卫和同一历史身份。新 analyzer 327c、测试 c654 由不同上下文 `/root/implementation` 实际独立运行 **79/79 与两项语法检查**，RA1 已关闭；本审核者连续读其完整原始记录与最终结论，没有把另一角色的测试称为自己执行。

主控 `commands/goal2_raw_integration.json` 与实际 stderr 记录完整 **221 项、18 项语法检查返回 0**，包括真实安全截图/Windows 生命周期检查，0 个 n4096。这是主控的实际集成回归。当前记录的 O2/O3 二进制汇编区间各 113 条指令，标量 mulsd/addsd 各一、无 packed mulpd/addpd，源、binary SHA 对应新 RAW 构建；本次只读取该汇编证据，没有再次编译或运行大目标。数学内核 SHA 仍为 4005ab，目标适配只改两处 timer 字面量。

## 前置数值与八项范围

两个已经完成的 RAW 数值进程对应原冻结提交 `75a0154b563b4123813e39a967967b0abbfb7f5c`、原协议 03218 与当时 driver a6daf，不将后来的 483a 版本填回旧原始数据。两个真实 attempt 为 `4c1527651be84705b786f6ca4c27f475`、`82f0b8afb8c047889ba7148ead33ed1a`；各一个进程、24 个预定元素抽查均 failures=0，原 ns/完整守卫和成本已独立复算。不是大矩阵全元素验证，也不作为正式成绩。

| 前置配置 | driver RAW 秒 | 最大三域资源秒 | 此阶段再次调用 |
| --- | ---: | ---: | ---: |
| s24/O0 | 227.313596304 | 227.340566506 | 0 |
| s128/O3 | 45.925977175 | 46.605943140 | 0 |

数值绑定为 51dc；对应完整结果审核 `goal2_raw_timing_result_review.*` 保留原字节。本阶段只调度同一个 O2 二进制、原 n4096 初始化的八个独立进程：

| 顺序 | 配置 | 标签/配对 |
| --- | --- | --- |
| 1、2 | s128/O2 | A1、B1 |
| 3、4 | s8/O2 | B1、A1 |
| 5、6 | s8/O2 | A2、B2 |
| 7、8 | s128/O2 | B2、A2 |

每项一次，额外预热 0、数值再测 0、自动重试 0。待审协议 26605 的工作项、标签、D/P、四组粗排序门逐项等于原 03218；继承的 warmup 字段不会增加任务。内核和主成本为 RAW，既有 process_wall_s/driver_wall_s 仍表示 MONOTONIC。完整目标与 driver 的 RAW/REALTIME 各沿同 boot/来源的原 first 和 previous 作 2% 检查；失败旧预热不变成有效基准。5% 目标、2pp 风险、10% 最低实用收益不变，不同身份精细风险仍不受支持。QPC 是有限相对观测，旧短工作反例与同配置 24.35% 波动均保留。

## 准入条件与边界

本关批准 **仅此八次 A/A** 的代码路径。执行前主控须更新批准状态、冻结时间、审核路径/实际 SHA 和资源引用，科学规则及输入身份保持待审 26605；生成新的准确八项 plan，旧 03218/dff23 plan 与原始数值日志不变。新的 closed 资源快照和协议 SHA 必须匹配，正常 local source/protocol commit 后，由独立角色作最后轻量身份检查再启动。

已经发生 46 次调用；`46+8+70+283+76+32+1=516`，基础确认分支 483，520 上限余 4 次共同保留额度。16 小时按逐任务 MONOTONIC、RAW、REALTIME 正差最大值累计，不能承诺全部最坏 timeout 均可完成。任一完整时钟保护、未知调用/成本、倒退、timeout 或资源上限失败就停止并保留日志；不重置 first、放宽阈值、换样本或重复到通过。

实际八项须另审原整数 ns、逐过程与完整 driver 的守卫、八个独立标签/成本和四组粗排序。两对 A/A 不是 CI、总体稳定性或 5%/2pp 分辨能力。即使粗排序门通过，完整正式批次仍需新协议和独立准入，S3 未经主实验与新 seed 确认不能 KEEP。旧 MONOTONIC 停止结论、未执行阶段和最终验收状态不变。

## 固定输入

| 文件 | SHA-256 |
| --- | --- |
| `evidence/protocol_raw_aa.json` | `26605c4f81c67724c6a16da309f75c10d816663f4e97cc0d20c7fd4363eb5f7e` |
| `evidence/reviews/goal2_raw_aa_method_review.md` | `294d8b98872c74ea42ae7457f999f2e7526621c7f80d7bd0f6be96e741d95fd2` |
| `evidence/reviews/goal2_raw_analysis_review.md` | `ac14eb157c578c29552818754ee509c3eb46b56199f7641fda8dfc7caa768531` |
| `evidence/measurement/raw_timing/clock_history.json` | `8ced08e3ac7fb86cc7d6f7a67c040981bbee90a3224005720d2b6fa7ad3faba3` |
| `evidence/measurement/raw_timing/numeric_clock_baselines.json` | `51dc3dc9d20c1b34b68c6806ca913acdcf855bf52a709f4f38d8f19f551483ca` |

最终化时间：2026-10-02T21:01:11.088160+00:00。精确源码/测试、历史输入、实际成本快照、完整执行条件与原始回归均在同名 JSON；后续执行结果不追加到本门。
