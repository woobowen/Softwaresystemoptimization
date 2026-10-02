# 正式预热完整时钟漂移后的有限只读诊断

设计者：`/root/measurement`；状态：待原独立审核者批准后执行。此记录不修改已经冻结的正式协议、first/previous 基准、2%门、种子或参数，也不重新启动正式参照。

## 1. 已发生的事实与待区分问题

正式预热 `warmup-reference` 唯一实际 attempt 为 `45586dcb04f04acc832ca39456f2451e`，目标和 CLI 均完整退出0，内核输出32.742920秒、checksum有效；但完整进程 `RAW/MONO=1.0195778546025593`，相对同 boot 的首个有效进程 `0.9981160219083189` 增加2.150234263669%，触发冻结的2%停止。完整 driver 比率1.01963584740653，相对首个0.9986300261262919增加2.103463818499%，也发生冲突。相对最后数值抽查的比率变化只有0.197238%和0.202760%；小的局部变化不能覆盖累计相对 first 的冲突。

原始进程三个区间为 MONOTONIC33.337630412、RAW33.990309693、REALTIME33.937446023秒，整数ns先相减再换秒，与保存字段一致。进程子CPU为33.977621秒，CPU/RAW约0.999627、CPU/MONO约1.019197；这些相对关系不是CPU或RAW绝对准确的证明。已启动44次n4096，正式参照有效样本为0；不得将预热或先前诊断补进新20配置表。

本轮只区分：当前多域关系的变化是否也存在于与矩阵初始化/测量解析无关的空闲区间与固定工作量区间；CPU域相对关系是否随工作量同步改变。两个探针不能定位服务或宿主机最终根因，也不能证明原被杀任务若完成的结果。原timesyncd及其他服务只读信息保持，不做任何系统调整。

## 2. 精确两项，原构建与固定顺序

复用 `scripts/clock_diagnostics.py` 已生成并审核的 `.cache/clock_goal2/probe`，不重新编译或修改源码。执行前使用已有 `check_identity` 核对 `evidence/measurement/clocks/identity.json`、probe源及binary；原probe源SHA为 `eec2fc56c80d5aa11306d6169495da614ada9c349937cf99f295f26eacc01aa9`，binary SHA为 `8c98025fbc9de32235bd25e954ea92fefba4fc396a5d649a885ff05de019d43d`。具体命令中的任务P1根从实际工作目录解析，不要求发布复现依赖缓存binary。

| 固定次序 / task | 命令（相对P1） | 目的 / 停止方式 |
| --- | --- | --- |
| 1 / `formal-drift-idle40` | `taskset -c 0 .cache/clock_goal2/probe idle 0 40` | 与原40秒idle同模式；CLOCK_BOOTTIME等待控制停止，四域只作观测。BOOTTIME与MONOTONIC有关，不自证准确。 |
| 2 / `formal-drift-work8e9` | `taskset -c 0 .cache/clock_goal2/probe work 8000000000 0` | 与原两个8e9工作探针同迭代数；固定循环次数控制停止，不由待验证时钟决定工作量。 |

两个任务仅各执行一次，role=`clock_probe`，n4096 `call_upper=0/direct_calls=0`，每项timeout300秒。按原观测预期合计约60秒，理论逐项timeout和为600秒；实际resource仍逐任务max正MONOTONIC/RAW/REALTIME计入16小时硬上限。不得把等待成本写成人工工程工作量，不得再以不同种子、窗口或顺序补到比率落回阈值。

## 3. 保存、重算与决策边界

主控持原 `.cache/performance.lock` 非阻塞独占锁，使用原 `controlled` 与全局ledger。原目录和正式raw不写；stdout/stderr与本轮说明保存在 `evidence/measurement/formal_clock_drift/`。保存四域原始start/end整数ns、调用次序、原打印秒数、工作量/idle停止方式、readonly `adjtimex modes=0`状态、受控完整driver三域和退出状态。任何倒退、非有限数、权限/身份/未知成本、超时或资源上限仍硬停止，不静默绕过。

独立重算 `q=RAW/MONO`、REALTIME/MONO；工作模式另呈现CPU/MONO、CPU/RAW与CPU占用，idle CPU不拿来替代等待时间。同模式对照旧完整probe-5-idle及probe-6/7-work，全保留，不挑更有利旧样本。新两个probe不增加算法种子，不成为n4096正式时钟baseline，也不反向校准原始秒数。

若两模式仍显示多域关系变化，可加强“变化不限于目标解析或初始化”的定位线索，不能认定特定服务因果；若两模式关系一致或落回原范围，也不能撤销已经完整发生的正式冲突或证明长期稳定。任何结果都不自动授予正式恢复或性能KEEP。测量守卫正确而环境不能在现有授权内稳定时，保留性能依赖阻塞，继续代码/历史重算/报告/真实图片/干净复现和阶段发布；未执行的20配置、算法比较及S3闭环准确标未完成。

## 4. 新增 Windows QPC 区间核对：仅有限恢复可行性诊断

本节在 QPC 结果产生前预注册，须单独经过方法与实现审核；不修改上面已执行两项的原批准范围。只读调用已经存在的 Windows PowerShell 和 `.NET Stopwatch.GetTimestamp`。Windows 的 Stopwatch 高分辨计时使用 QPC，QPC 不与 UTC 调整同步；本机须实际报告 `IsHighResolution=true`，不能落入系统时钟回退。QPC 的频率是计数单位，不据此推断本机硬件频率或独立硬件来源；宿主机和 WSL 可能共享 TSC/Hyper-V 计时基础。本设计只检验区间的相对一致性，不把任何一个时钟指定为绝对标准。[Microsoft QPC](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps)、[Stopwatch.GetTimestamp](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.stopwatch.gettimestamp?view=net-9.0)、[Stopwatch.Frequency](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.stopwatch.frequency?view=net-9.0)。

### 4.1 固定执行范围与真实成本

使用一个本任务创建的常驻 PowerShell 子进程，启动后做固定五次握手，全部保存。启动和握手计入项目成本，但不包含在待比较区间中，也不按握手速度挑选端点。之后固定测量四个端点：idle 起点/终点，work 起点/终点；同一宿主进程、同一串行请求线程，每个响应包含唯一递增 seq、正整数 tick、正整数 Frequency、`IsHighResolution=true` 与实际宿主 PID，逐响应与启动身份一致。每个请求的 Linux 读取顺序固定为 MONOTONIC、RAW、REALTIME、PROCESS_CPU，保留整数 ns 和请求/响应原文。

| 顺序 | 工作负载 | 结束条件 | 数量 |
| --- | --- | --- | --- |
| 1 | 原 probe `idle 0 40`，CPU0 | 原 CLOCK_BOOTTIME 等待；40 是请求值，不用它证明时钟准确 | 一次 |
| 2 | 原 probe `work 8000000000 0`，CPU0 | 固定 8e9 次工作循环，不由待验证时钟决定工作量 | 一次 |

两项均复用原已验证的 probe 源/二进制/GCC 身份，不编译、不执行 n4096。每个工作进程最多300秒；单个桥响应完整行最多10秒（必须包括 partial-line 情形），宿主启动/退出分别最多10秒。受控总超时上界750秒，预计约60秒的 workload 加有限互操作开销；主控按实际三域正差最大值计入剩余16小时硬上限，`n4096_calls=0`。任何无响应、身份不一致、倒退、非整数/非有限值、异常退出、未知成本或资源上限都停止，不追加新的握手/窗口或重跑直到满足阈值。

### 4.2 区间括界与量化误差

每个请求在写入前读 Linux 四域 `before`，读取完整宿主响应后立即读 `after`，因此宿主 tick 的读取事件被 Linux 读数括住；不假定事件在往返时延的中点，不扣除半 RTT。对某个 wall 域 D，两个端点为 A/B，先以整数相减，再换为秒：

```text
D_low  = (B.before_D - A.after_D) / 1e9
D_high = (B.after_D  - A.before_D) / 1e9
delta_ticks = B.tick - A.tick
H_low  = (delta_ticks - 2) / Frequency
H_high = (delta_ticks + 2) / Frequency
D_over_H_bounds = [D_low / H_high, D_high / H_low]
```

要求 `delta_ticks>2`、`0<D_low<=D_high`，所有宿主和 Linux 端点有序。额外 ±2 tick 是本项目保守量化敏感性处理；不声称同线程存在官方跨线程排序歧义，也不把该带宽叫置信区间。REALTIME 可能调整，相关区间括界依赖该请求期间没有未观察到的跳变；它只作并列诊断，不用它独自保证 QPC/RAW 正确。

固定四个测量端点均须满足 `max(after-before for MONOTONIC/RAW/REALTIME)<=0.020秒`；两项各自三个 wall 域的 `(D_high-D_low)/((H_low+H_high)/2)<=0.002`。五次暖握手保存全部延迟，但不替换四个端点；任一端点过宽，则该项不能用于相对关系准入，保留实际数据并终止后续 workload。输出完整边界、量化带宽、比例区间和逐条件 bool，不能只在文字中写阈值。

Linux 桥 parent 的 PROCESS_CPU 只反映桥自身开销。原 C stdout 内四域覆盖其工作区间，C 的 CPU/RAW 另列；其边界不同于 QPC 请求端点，不能把两个 CPU 域或不同区间合成同一占用率。完整受控 driver 时间仍独立计费。

### 4.3 在看到 QPC 数据前固定可支持的下一步

若两项都完整、括界合格、身份/生命周期/成本可核对，且两项 `RAW/QPC` 的整个比例区间均包含于 `[0.995,1.005]`，只能提出一次另行审核、另冻结身份的有限 RAW A/A 可行性试验。0.5% 是该只读桥接相对关系筛查门，不更改原协议2%时钟停止、5%近优目标、2pp风险或10%收益门。若仅区间与该范围相交或只有一项满足，证据不足；若完全落在范围外，记录方向与差距。该两项绝不能证明数小时稳定、总体假阳性率或5%/2pp性能分辨力，也不自动放行新正式比较或授予 KEEP。

分析须并列保留原 probe-5/6/7 与最新两项 Linux 探针、全部矩阵完整多域区间。原两个固定 work 的 RAW/REALTIME 比率变化约2.93%是反对将 REALTIME 自动当作稳定标准的证据，不挑选只有矩阵的片段。原 MONOTONIC 协议的完整预热冲突、first 基准、原始秒数及未执行状态均保留，不校准旧成绩，也不追认原中断任务的未知完整结果。

记录桥的 Linux PID/实际宿主 PID/创建来源，并在正常退出、SIGTERM、超时和异常的退出处理中只清理自己创建的桥与 workload，验证实际宿主 PID 已退出；不能按进程名终止用户会话。读 pipe 的期限必须涵盖未换行响应，退出清理不能被 blocking read 绕过。若宿主资源清理无法可靠确认，标明缺口并停止本诊断，不借系统设置或管理员权限绕过。
