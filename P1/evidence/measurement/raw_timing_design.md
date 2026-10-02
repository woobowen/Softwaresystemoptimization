# RAW 计时候选的有限 A/A 可行性设计

设计者：`/root/measurement`。状态：条件性方法草案；须独立方法与代码审核、精确新身份冻结后执行，尚不是正式比较准入。旧 `protocol_v2.json`、first/previous、2%停止和失败样本保持原样；不把旧 MONOTONIC 秒数转换成 RAW 成绩。

## 1. 进入本有限阶段的依据与边界

前置设计为 [QPC 只读核对 §4](formal_clock_drift_design.md)，冻结 SHA `ac920bb167e07760d841c430491df6edcdad45fe3be25af33e2acfe8f3924ea6`。其实际原始 stdout 为 `formal_clock_drift/host-qpc-two-intervals.stdout.txt`，SHA `3e13770e3e3b3cb927de2760c7f21f00c4c43dbf709be7dc0f5e3bbd306213d3`。从整数读数独立核对九个连续 response、五次握手、四个端点、固定 Frequency/PID/高分辨状态、±2tick及 Windows PID 退出，结果如下；未导入 probe 实现函数计算。

| 区间 | 宿主 ticks / Frequency | QPC 秒 | RAW/QPC 全括界 | 最大端点秒 | RAW 相对括界宽 |
| --- | ---: | ---: | --- | ---: | ---: |
| idle40 | 409477802 / 10000000 | 40.9477802 | [0.9999918632708111, 1.0000067128181307] | 0.000438595 | 0.0014839779% |
| work8e9 | 193217319 / 10000000 | 19.3217319 | [0.9999824610962287, 1.0000167904722534] | 0.000419037 | 0.0034308674% |

两项整个 RAW/QPC 区间均包含于预定 `[0.995,1.005]`，四个端点满足20ms、三个 wall 域各自宽度满足0.2%，lifecycle有效。同期 MONOTONIC/QPC 约0.977/0.978，REALTIME/QPC 约0.996/1.016；这支持评估局部 RAW 适配，不证明 QPC/RAW 绝对准确或长期稳定，也不撤销原 v2 完整预热冲突。

## 2. 全部已有矩阵区间与反例

对 append-only 主账本读取的一次 bytes 快照 `b8fda62b67ed5cb486fc4090c12e2d39a9d1a561200fbb95f239cd81c99d2b79`，独立以原整数ns重算 `q=RAW/REALTIME`。只分析已完整结束的矩阵区间；该快照当时可能含0-call QPC在途任务，以下不是项目成本完整性声明。四个 direct 多时钟矩阵只有完整 controlled-driver 与内核记录，没有独立 formal target-process journal，不能拿内核钟域代替进程钟域。

| 完整来源 | 数量 | q最小 / 最大 | 相对原同boot首项最大绝对变化 | 相对前一有效同类项最大绝对变化 | 2%冲突 |
| --- | ---: | --- | ---: | ---: | ---: |
| 完整 target process，含原冲突预热的完整 C 观测 | 39 | 0.9958610718671993 / 1.0035859255508501 | 0.548023382845% | 0.775009762813% | 0 |
| 完整 matrix driver，含4个direct诊断 | 43 | 0.9937131833968241 / 1.003591118404856 | 0.496792020488% | 0.802087113858% | 0 |

进程 first 对应原 attempt `d30f547b4da1406eac53b6b92250e447`、identity `[e68dcc091e74490694a8b3532e8c215d,0,0,248077]`，其 RAW/REALTIME 为0.9981160163930989；driver first 对应原 `a754f5ea5bc94becb31302b4966a852d`，为0.9986300042296413。没有选择新的更有利 first。原被中断的 `diagnostic-b4-05-M-B3` 不具有完整内核，仍单列失败和成本，不入完整矩阵 baseline。

原预热的完整进程 RAW/REALTIME 为1.0015576796781989，对上述 first/previous 分别为+0.344815956119%/−0.107214044002%；driver 为1.0017312987253102，对 first/previous 为+0.310554908478%/−0.106594264101%。这里只呈现另一个钟域关系，原预热 `clock_conflict=true` 仍保留，也不将它加入有效 baseline 或成绩。

反例必须同时保留：原 probe-6/7 固定 work 的 RAW/REALTIME 为0.9819975772732095 / 1.010758641520136，变化约2.93%；最新单独 work 为0.985164904813601；QPC 两项中的 C 原 work 区间 RAW/REALTIME 约0.983934。因此 REALTIME 不是普适稳定标准，矩阵过去未越2%也不是未来保证。新辅助守卫仍保留 REALTIME，若再次越门就停止，不能为了推进删除它或增大门槛。

## 3. 最小适配和两个完整区间守卫

本候选唯一改变测量机制：C 的两个 `clock_gettime` literal 从 MONOTONIC 换为 MONOTONIC_RAW。n=4096、double、默认 rand 初始化、六层循环、s24尾块、checksum、四级公共编译参数全部不变。对老师原程序、旧计时目标和新计时目标抽取的计算内核须逐字一致；新源/框架/driver/分析/编译器/四级二进制哈希独立冻结，不更新旧 plan/hash 或复用旧搜索样本。

核心最小接口为：明确识别唯一一致的 MONOTONIC 或 RAW 计时域；混合/不支持的域不能进入本实验；内核输出与同次目标进程 `clock_deltas_s[kernel_clock]` 比较。不能因为 RAW 内核不同于 `process_wall_clock=MONOTONIC` 而跳过上界保护。`process_wall_s`、`driver_wall_s`、已有 `tuning_elapsed_s` 保持原 MONOTONIC 含义，RAW 成本另由整数ns重算，不给旧字段换语义。

候选新守卫只在另冻结的 RAW 矩阵阶段生效，完整 target-process 和完整 driver 分开重算 `q=RAW/REALTIME`，与同 boot、同来源的 first 和 previous 各比较 `abs(q/q_baseline-1)>0.02`。沿用第2节的原物理 first 身份，不通过清空历史或从首个新候选样本重新取 first 来避门。原 RAW/MONOTONIC 比率继续完整保存为诊断；旧 v2 的 RAW/MONOTONIC 停止条件和失败状态不改，新守卫语义在新协议中明确记录。

只有完整、已知成本/调用数、退出0、无 reason/clock-conflict 的既有矩阵 attempt 可更新相应历史；失败预热和中断不更新。每个目标进程都检查，不能用多调用 driver 均值隐藏单个进程变化。任何倒退、未知成本、缺原整数边界/coverage/身份、1200秒目标超时、520调用或16小时资源上限仍硬停止并保全已发生成本。完整字段/结构/identity/first/previous及资源三域须能从指定账本快照逐一重算；summary存在不等于时钟健康。

版本迁移只用于 clock baseline，不能用于成绩：已冻结旧 framework/target/compiler/flags、数值 adapter 绑定及原 journal fingerprint 以精确版本身份核对。旧 source SHA不能被新 SHA覆盖，也不能泛接受任意旧源码。原始ns足以计算新辅助比率，不足以把旧 MONOTONIC 内核输出重标 RAW；旧表仍用匹配 commit 的旧脚本重生成。

本有限 A/A 的主观测是新的 C 内核 RAW 秒；进程 RAW 秒和 driver RAW 秒分别从其原ns计算，完整实际调优成本优先用 RAW driver 秒。MONOTONIC、REALTIME、CPU及编译费用全部并列保留，项目硬资源继续按每 controlled 任务三 wall 域正差最大值计账。新正式比较若获准，协议和分析须显式选取 RAW 成本字段；不把旧 `search_driver_wall_s` 乘比例改成 RAW，也不把 CPU 代替等待时间。时间曲线的旧字段可保留并明确标 MONOTONIC；若另展示 RAW 时间曲线，须使用实际 RAW 边界/事件，不能事后校正旧坐标。

## 4. 精确8个新独立A/A，不增加预热或探索

F 为 s128/O2，M 为 s8/O2；两者同源同O2二进制，仅运行参数s不同。每个 A/B 标签都是全新目标进程，不按身份去重、不共享在线样本、不混入正式20配置表。

| 固定位置 | task | 档/标签/配对 | config |
| --- | --- | --- | --- |
| 1 | raw-aa-01-F-A1 | F / A / 1 | s128/O2 |
| 2 | raw-aa-02-F-B1 | F / B / 1 | s128/O2 |
| 3 | raw-aa-03-M-B1 | M / B / 1 | s8/O2 |
| 4 | raw-aa-04-M-A1 | M / A / 1 | s8/O2 |
| 5 | raw-aa-05-M-A2 | M / A / 2 | s8/O2 |
| 6 | raw-aa-06-M-B2 | M / B / 2 | s8/O2 |
| 7 | raw-aa-07-F-B2 | F / B / 2 | s128/O2 |
| 8 | raw-aa-08-F-A2 | F / A / 2 | s128/O2 |

两个连续块先F后M/先M后F，每档分别AB和BA，A/B各两个实际独立样本。不得遇到较慢样本就换顺序、替换标签或追加直到稳定。每项 role=`aa_raw_timer`、repeat=1、call_upper=1，统一性能锁与全局ledger；未满足前置审核不启动。构建检查、失败和中断成本照计。

输出每档两个标签的中位数及范围、每对 signed秒差与 `100*(B/A-1)`、`D=100*abs(median(B)/median(A)-1)` 和 `P=max_pairs 100*abs(B/A-1)`，全保留。另比较四组匹配 `(A1,B1,A2,B2)` 的 M/F−1：若全部同向且最小正差大于 `max(P_F,P_M)`，仅支持这两档的粗排序；否则排序暂无法分开。这个有限描述规则不是显著性或非劣证明。

数值、同域保护、全部8有效/成本已知、两个完整来源2%守卫都通过，且上述粗排序可支持时，才交回独立方法审核讨论新正式协议。无需A/A小于5%才给出粗排序，但不能由此承诺5%近优可分辨；`different_identity_risk_supported=false`、5%目标、2pp风险、10%收益门、原六主seed与三个未用确认seed均不放宽。这个阶段不能 KEEP 搜索增强；S3仍未开始，默认可靠 Random 保持。任何准入条件失败就停止本有限阶段、保存缺口，不自动增加下一批诊断。

## 5. 正确性与精确资源

计时适配先复核同源小矩阵全元素、全部s含尾块、独立参考、sanitizer及四级构建；只用小n作正确性。必要新 n4096 数值抽查最多两项，分别 s24/O0 与 s128/O3、默认seed1/mode0、同计算内核24个独立 long-double 点，沿用已审核方法但绑定新计时源；不称全量大矩阵验证，不成为成绩。

不额外预热或运行矩阵来检查CLI；8个A/A和2个必要新数值抽查共最多10次n4096。已有实际44次（包含原失败warmup），QPC/短probe均0次矩阵。若后续所有必要工作在新冻结协议下执行，调用上界为：

```text
候选获选：44 + 8 AA + 2数值 + 70完整参照/锚点/预热
        + 283六块四算法/共同面板/预热 + 76候选留出/面板/预热
        + 32起点面板 + 1干净复现 = 516，距520上限余4。
保留基础：将候选留出76换为新Random确认43，总483。
```

70项是全新的新时域参照，旧 v2 冲突warmup只在已有44中计一次，不抵消新预热。实际 Greedy提前停止、面板去重可降低次数，不能成为免费额外复测额度。正常候选路线仅余4次共同安全预留；若影响结果的bug要求重跑全部8次A/A，不能擅自突破520或把失败成本清零。资源上限另按真实三域受控成本执行，不保证516调用能在16小时内完成；八A/A和两抽查目标超时之和12000秒，必要编译/小测试也计费，最终正式计划须基于实际新诊断成本更新且复核剩余硬上限。
