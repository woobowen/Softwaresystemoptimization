> 此候选方案已在第五阶段获得授权并执行，未恢复稳定计时；已恢复原 clocksource。见 [实测结论](recovery-conclusion.md)。以下是当时提出的方案，不再表示等待授权。当前 [GitHub 检查点](../final/github-checkpoint.md)仅供诊断；clean WSL restart、VM、原生 Linux、WSL version/kernel 或其他路线均尚未决定，也未执行。

# 当前测量环境的恢复选项

2026-10-01，只读检查发现以下问题：

- 原 Base 的 wall 日期差 8404 s，单调时钟 7933.371 s；复制结果不在这两个区间内。
- Java 7 与 Python 的 wall clock 同步发生约 3 s 的离散前跳；时间同步服务报告的一个偏移 3.254952 s 与探针的跳变量一致。这支持校时进入测量区间，尚不确定底层时钟异常的根因。
- Windows 独立 30 s 探针：wall 30.158 s，Stopwatch 30.1598493 s；Linux 外层同一次调用的 monotonic 27.846234 s、raw 30.770393 s、wall 30.584306 s。外层包含 PowerShell 启停，不能把两层绝对时长直接相减。
- 当前 clocksource 为 `tsc`，可用源中有 `hyperv_clocksource_tsc_page`、`hyperv_clocksource_msr`、`acpi_pm`。只读 adjtimex 查询的 tick=10833，freq=2167896（scaled ppm）；没有修改这些值，也不能单凭它们认定根因。
- SPEC 用 wall-clock loop 时间扣减越过计划终点的末次操作；七份原结果的 compress 均出现所有 22 个线程扣减量大于一个操作。固定的 raw 240000 ms 不能证明实际时钟正常。

拟请求的最小系统变更：结束当前诊断后，仅把
`/sys/devices/system/clocksource/clocksource0/current_clocksource`
从 `tsc` 临时改为已提供的 `hyperv_clocksource_tsc_page`。
这是全局运行时设置，影响同一 WSL 内其他进程，需用户批准；不写启动配置、不修改 Windows、不停用时间同步。
写入前后记录该文件、adjtimex、timesync 状态；随后运行同样的 10 分钟探针。
若仍不稳定或写入失败，停止该路线并恢复 `tsc`，不继续猜测其他全局设置。
这是一项可检验的候选修复，不是已经证实有效的修复。

只有探针通过才运行一次 replacement Base；新测量期间保留轻量时钟监视。
旧六次单项也有计时风险，建议经明确同意后在稳定环境重新做 3+3，旧结果全部保留为历史证据。
所有新数据都来自未修改的 SPEC/JDK，不对旧分数进行人工校正。

依据：[Linux Hyper-V clocks](https://docs.kernel.org/virt/hyperv/clocks.html)、
[Microsoft Hyper-V timers](https://learn.microsoft.com/en-us/virtualization/hyper-v-on-windows/tlfs/timers)。
Linux 文档说明共享页时钟应用 hypervisor 提供的 scale/offset；这支持试验该可用源，不足以保证本机修复成功。

任务提示词第 32 节将“需要改变系统/Windows 全局配置”和“需要改变已确认的大方案”列为需停下报告的边界。
在获得批准以前，继续只读检查、证据整理、脚本测试和文档准备；不进行此系统变更，也不发布未消除高风险的结果。
