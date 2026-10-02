# Goal 2 编排与时钟实现独立审核

审核者：`/root/review`；owner：主控 `/root`。本记录追踪代码/设计边界。**有限 30 次矩阵诊断代码关已通过；正式参照和主实验尚未放行。** 核心的 72 个独立测试通过记录另见 `goal2_code_gate.md/json`。

## 初稿问题

| ID | 位置（初稿） | 严重性、证据与影响 | 要求与状态 |
| --- | --- | --- | --- |
| R1 | `scripts/experiment_v2.py:185`，`panel:305` | 高：task 校验只核对 header 和部分 measurement，panel 直接读取 summary.best。未从原始输出、真实步骤和阶段重算 trial/summary，改 summary 可改变锁定返回 | 需严格重算并用伪造 metadata/summary/raw/start 的 fixtures 拒绝；待修复复核 |
| R2 | `freeze_check:227`，`plan:246` | 高：manifest.jobs 尚未与冻结协议生成结果比较；修改合法配置内的 seed/预算/顺序仍可能形成非预注册批次 | 需核对完整计划、原根和依赖集合，不仅 protocol SHA；待修复复核 |
| R3 | `execute:363` | 中：当前 >1s 区间只与 protocol 常数比一次，和 design 的同 boot、本 Goal 矩阵 driver>=10s、与前一个和首个比较不一致 | 按已审规则执行并验证边界；待修复复核 |
| R4 | `controlled:142` | 高：finally 中 elapsed 验证失败会在保存 end 边界前抛出，留下 start 而缺少实际 end/未知成本现场 | 先保存所有原值和明确未知/异常状态，再阻止后续运行；待修复复核 |
| R5 | `stop:91` | 高风险故障路径：升级只 kill 直接 driver；若 driver 没清理自己创建的独立 session C，可能遗留被测进程 | 根据 journal 中本任务创建的 PID/command 确认存活与归属，清理或阻止继续；不得按进程名杀用户任务；待修复复核 |
| R6 | `validate_task:190`，`main:388` | 中：historical 校验取 protocol.measurement_root，而 main 无条件设为当前 P1；干净 clone 中原始绝对 metadata 会错配 | 历史校验从原 manifest 取得冻结根，执行/恢复仍必须在原根；待修复复核 |
| R7 | `plan` / 正式资源计划 | 中：输出 jobs 个数尚不等于调用上界，panel 动态去重有实际展开成本 | 事前提供各角色及全 Goal 调用上界、实际调用口径、明确时间域的最坏剩余成本及 cap；待资源计划 |
| K1 | `scripts/clock_diagnostics.py:85` | 中：数组 initializer 含多个诊断函数调用，C 不保证它们按文本顺序求值；输出却声明固定钟域顺序 | 独立赋值语句保证 RAW/REALTIME/CPU 顺序，kernel 文本保持不变；待修复复核 |
| K2 | `clock_diagnostics.py:109` / `:126` | 中：重执行会改写 identity/diff 并 append 到既有结果，可能把两个执行拼成一份 | 拒绝已完成覆盖或明确新批次，不改写旧记录；待修复复核 |
| K3 | `clock_diagnostics.py:116` | 中：诊断 identity 尚无实际 compiler/binary SHA，运行前不核对缓存来源 | 保存成功构建身份，运行前核对源/二进制；待修复复核 |
| K4 | `clock_diagnostics.py:64` | 中：[adjtimex 手册](https://man7.org/linux/man-pages/man2/adjtimex.2.html)明确 offset 在 STA_NANO 时为 ns，否则 us；固定 `offset_us` 可能错标单位 | 保存 offset_raw 和按 status flag 得出的 offset_unit；freq 保留 scaled-ppm 原值；待修复复核 |

以上为静态代码证据，未把可能故障宣称已经发生。修复后需读真实版本和测试，不能仅凭作者摘要关闭。

## 诊断进入条件

`measurement/design.md` 的有限设计已通过独立审查，初始上界 30 次 n4096；新正式接受表未冻结。clock 探针只读查询、固定工作量和必要 idle 间隔可执行，但矩阵诊断需要上述 runner/clock 关键问题关闭以及实际独占/计费检查。新正式参照及主比较还需诊断原始结果和协议两关通过。

全部审核证据为内部检查，不是最终 Engineering PASS。

## 修复后的实际复核

审核读取修复后的完整关键路径，并独占 `P1/.cache/performance.lock` 以 `LOCK_EX|LOCK_NB` 实际执行：

```text
cd P1
python3 -m unittest discover -s tests -p test_goal2_driver.py -v
Ran 19 tests in 1.021s
OK
```

退出码 0，无跳过，n4096 调用为 0。测试外层 MONOTONIC 为 1.105982891 s、RAW 为 1.112742327 s、REALTIME 为 1.105982761 s；这些短工程测试的时钟比率不属于矩阵 >=10s 时钟健康判定。锁已释放。原始输出、全部起止值、运行前后源码身份见 `goal2_runner_regression.json`；此前 16 个测试的记录 `goal2_runner_tests.json` 保留，未被覆盖。

被审身份，测试前后相同：

| 文件 | SHA-256 |
| --- | --- |
| `scripts/experiment_v2.py` | `22a839a0df7fe409227a8c2a8671d839b5703408aac845bcabb169c817547273` |
| `scripts/clock_diagnostics.py` | `12e22003e861028292445951c8bb4bffc80c3d61a9479611eddc73db230999ff` |
| `tests/test_goal2_driver.py` | `776f932a224b26f8d79cda93f68e28ac1b80cd6cfc3dd3466396ac396c115d3d` |
| `src/autotuner.py` | `32f4dd734a15b7d295ee011b566bf113b722e8128fd147525e8c77856dfdf964` |

| 问题 | 修复与复核证据 | 当前状态 |
| --- | --- | --- |
| R1 | `validate_trace` 重算提议次序、真实初测与复核反馈、成功复核资格、trial/best/counters；原输出、重复/PID、三域整数 ns、kernel 秒与 MONOTONIC 同域保护严格校验。测试拒绝 summary 回填、fresh/eligible 改写、原始计分/单位/钟域伪造 | 关闭代码缺口；正式原始数据仍待执行审核 |
| R2 | frozen manifest 与协议重生成 jobs 全量比较，执行/分析身份分离；测试拒绝即使重算 fingerprint 的元数据改写 | 关闭 |
| R3 | `matrix_clock_baselines` 仅取同 boot、实际矩阵调用、MONOTONIC>=10s 的历史 task_end；运行中对本 Goal 首个及前一个比率任一相对变化>2%暂停。fixture 确认短探针与其他 boot 不成为基准 | 关闭代码缺口；实际 q 稳定性待诊断 |
| R4 | 倒退先保存 `clock_error`、原始 end 和 unknown 状态；未结任务阻止继续，恢复保存未知真实成本和保守计费上界 | 关闭；如实际出现未知成本仍必须停止及记录影响 |
| R5 | SIGTERM/超时/自然非零退出均处理本任务独立进程组；从 journal 核对精确 PID/command/group 后清理未完成 C。实际 fixture 令 driver `os._exit(7)` 留独立 sleep，审核执行确认其已不存在或处于非活动 zombie，调用仍计费 | 关闭；不涉及按进程名清理用户任务 |
| R6 | historical 原根取 manifest；panel 新增只读历史模式，缺失 panel 不创建。原根 fixture 通过；干净 clone 的完整结果重算仍是交付关必要实际验证 | 关闭实现缺口，交付复现待执行 |
| R7 | 初始 28 A/A/锚点任务和 2 独立多钟域矩阵清单精确固定，调用与 max 三域控制成本由全 Goal ledger 计费。全部正式批次调用和最坏剩余时间预测须在诊断后按实际成本再冻结 | 仅有限诊断满足；正式资源关待完成 |
| K1 | 多时钟读取改为逐语句赋值，实际测试核对调用顺序和 `kernel()` 文本相同 | 关闭；大矩阵多域观测待执行 |
| K2 | 已存在诊断 identity/直接输出拒绝覆盖，实际输出保护 fixture 通过 | 关闭 |
| K3 | 保存实际编译器、正式源、诊断源与构建成功的两 binary SHA；launch 前复核源/二进制，编译通过的 provenance 后续查 raw | 关闭静态身份缺口；真实构建结果待执行 |
| K4 | 查询 `adjtimex` 的 modes=0；保存 `offset_raw`、按 STA_NANO 得到的 `offset_unit`、`frequency_scaled_ppm`，不将 RAW 当准确真值 | 关闭单位与只读约束缺口 |

有限诊断放行条件：主控将 `protocol_diagnostic.json` 从 draft 按已审设计冻结，并记录被审 runner 身份；总初始 n4096 上界为 30。主控仅有此有限诊断与必要小规模数值检查的进入依据，不能将本文件解释成正式性能比较、S3 KEEP 或最终 Engineering PASS。正式关还依赖真实诊断可比性、分析器复核、精确剩余资源计划和协议审核。
