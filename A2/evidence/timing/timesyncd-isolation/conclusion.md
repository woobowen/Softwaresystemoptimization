# timesyncd 隔离实验结论

**Engineering Status: WSL_TIMING_ISOLATION_PASS**。

这是两轮 timesyncd-off、Windows Host Stopwatch 联合计时的内部判别结果，不代表 A2 完成、SPEC 认可或正式性能资格。Submission 仍为 **NOT_READY**。

## FACT：真实测量

| Metric (s) | Gate 1 | Gate 2 | Active control |
|---|---:|---:|---:|
| Host Stopwatch | 600.436755400 | 600.422986600 | 180.604759100 |
| Linux realtime | 600.000176700 | 600.000193200 | 180.000088100 |
| Linux monotonic | 600.000176763 | 600.000193143 | 180.000088106 |
| Linux monotonic raw | 600.000265602 | 600.000273564 | 180.129239161 |
| Linux boottime | 600.000177685 | 600.000194152 | 180.000090253 |
| Java currentTimeMillis | 600.000000000 | 600.000000000 | 180.000000000 |
| Java nanoTime | 600.000288471 | 600.000329258 | 180.000206082 |
| host - monotonic | 0.436578637 | 0.422793457 | 0.604670994 |
| host - raw | 0.436489798 | 0.422713036 | 0.475519939 |
| host - boottime | 0.436577715 | 0.422792448 | 0.604668847 |
| host - nano | 0.436466929 | 0.422657342 | 0.604553018 |
| wall - monotonic | -0.000000063 | 0.000000057 | -0.000000006 |
| Java wall - nano | -0.000288471 | -0.000329258 | -0.000206082 |
| forward >0.5s（Python / Java，次数） | 0 / 0 | 0 / 0 | 0 / 0 |
| backward >0.5s（Python / Java，次数） | 0 / 0 | 0 / 0 | 0 / 0 |
| samples | 601 | 601 | 181 |
| timesyncd before / after | inactive / inactive | inactive / inactive | active / active |
| WSL / Java exit | 0 / 0 | 0 / 0 | 0 / 0 |

数据来自 [独立复算](independent-calculation.json)；秒数保留九位小数只为对照 raw，不代表 epoch 浮点数具有纳秒精度。Python endpoint/interval 与原 summary 的允许误差为 1 微秒。两轮均没有超过 ±50 ms、±0.5 s 或 ±1 s 的 Python/Java interval 差，也没有实际 wall 倒退。两轮最大 Java 请求往返分别为 0.810 ms、0.557 ms；最大 monotonic 采样间隔分别约 1.000395 s、1.000421 s。

- Gate 1：[host](gate-1/host-summary.json)、[guest](gate-1/guest-summary.json)、[samples](gate-1/samples.jsonl)、[jumps](gate-1/jumps.json)、[复算](gate-1/independent-calculation.json)。
- Gate 2：[host](gate-2/host-summary.json)、[guest](gate-2/guest-summary.json)、[samples](gate-2/samples.jsonl)、[jumps](gate-2/jumps.json)、[复算](gate-2/independent-calculation.json)。
- 两轮使用相同源码与配置，新 PowerShell/Python/Java PID、不同输出目录，见 [independence](gate-independence.json)。没有 Gate 重跑或补测。

### 环境与自测

[preflight](preflight.json)：WSL 2.7.12.0，kernel `6.18.33.2-microsoft-standard-WSL2`，boot ID `7af866bf-70f0-4652-bc4c-4d28a4eccfc6`。clocksource 为 `tsc`，timesyncd 为 `active`、`enabled`；NTP poll 32 s，offset +2.563185 s。Windows 接通电源；Stopwatch high-resolution 为 true，频率 10,000,000 Hz。

preflight 的只读 adjtimex：`state=0 status=8192 tick=10071 freq_scaled_ppm=-1682888 offset=0 tolerance=32768000 constant=1 precision=1`。停止后的查询为 `tick=10000 freq_scaled_ppm=106848`，Gate 1 后为 `tick=10000 freq_scaled_ppm=-8898`，恢复前为 `tick=10000 freq_scaled_ppm=-9551`。这些是离散时刻读数，不是连续观测，也没有用于写入或修正时钟。

15 秒 [自测](self-test/validation.json) 生成 16 个样本；当时 timesyncd active，Host Stopwatch 为 16.8464643 s，monotonic 为 15.000098971 s，出现一次约 +1.667 s 的 wall/monotonic interval 差。工具正确性检查与时钟稳定性判断分开；它不是 Gate。

同一 wrapper 包围 Linux `sleep 5` 得到 5.5291333 s；空调用 `true` 为 0.1658154 s；`exit 7` 准确返回 7。详见 [overhead 分析](wrapper-overhead-analysis.json)。`host - 5 = 0.5291333 s` 还可能包含 guest 时钟和 sleep 调度影响，不将其全部扣作固定启动开销。

Gate 1 guest 准备/收尾共约 0.337472 s，host-minus-monotonic 扣除这两项后约 0.099106 s；Gate 2 对应约 0.305841 s 和 0.116953 s。因而两轮完整 host 差值约 0.42–0.44 s 与短调用开销相容，远小于历史 38–50 s 差异。

### Optional active control

两轮 off Gate 完成后执行一次 `systemctl start systemd-timesyncd.service`，确认 active，再运行 180 秒 control。其全部 elapsed 和差值列于上表，最大请求往返 0.545 ms；Python/Java 在 ±50 ms、±0.5 s、±1 s 阈值上的前跳/后跳均为 0。见 [host](active-control/host-summary.json)、[guest](active-control/guest-summary.json)、[samples](active-control/samples.jsonl)、[jumps](active-control/jumps.json)、[复算](active-control/independent-calculation.json)。

**重新启用服务后，在这 180 秒采样区间内没有复现旧的周期性多秒 step。** RAW 比 monotonic 多约 0.129151 s，host-minus-monotonic 约 0.604671 s，未出现数十秒差距。control 后 timesync-status 为 poll 128 s、offset +4.800 ms、packet count 3；服务自动选择的服务器从 preflight 的 `185.125.190.56` 变为 `185.125.190.58`，配置文件未改变。重启服务改变了运行状态，这不是严格保留全部 NTP 状态的对照。服务启动到首个样本之前不属于 interval 检测区间，不能把“采样内未发现 step”扩大为整个恢复过程无校时。

## INFERENCE：证据支持的解释

1. 停止 timesyncd 后，两轮各 600 秒均未出现旧的多秒 wall jump；host 与 guest monotonic、raw、boottime、nanoTime 的差异均处于本次实际调用和准备开销的量级。
2. 本次隔离状态下没有观测到 guest 持续丢失数十秒真实 host elapsed。H2 预测的“即使停止服务，host 约 640 秒而 guest 约 600 秒”没有发生；因此不支持据此直接判为 VM 层持续 elapsed 丢失。
3. 相比 H2，数据更支持 H1 所预测的停止校时后改善，也支持校时服务或其运行状态参与原异常。但恢复 active 后没有复现故障，不能仅凭这组 off/on 数据断言唯一根因就是 timesyncd 本身，或认定启用服务必然触发异常。
4. 按本阶段预先约定的内部阈值，两轮 off Gate 均通过，因此使用 `WSL_TIMING_ISOLATION_PASS`。该名称只描述本次隔离试验。

## NOT PROVEN：仍未证明

- 尚未定位唯一底层原因，也未证明任何具体 WSL、kernel、Hyper-V 或 systemd bug 编号。
- 未证明必须永久关闭 timesyncd；active control 没有复现原故障。
- 轻量 1 Hz 探针不能代替更长时间、正式 benchmark 负载下的稳定性检查；当前没有可信 Base 或 final 3+3。
- 未排除其他时段、重启后、宿主睡眠/负载变化等条件下出现异常。单次 180 秒 active control 也不构成长期稳定性保证。

## 恢复、边界与下一步

[restore.json](restore.json) 确认 service 恢复到实验前 `active`，enable state 仍为 `enabled`；preflight、全部样本及结束读数均为 `tsc`，boot ID 未改变。`.wslconfig`、Linux NTP/systemd 配置 SHA256、电源方案、Windows Time Service 状态（前后均 Stopped/Manual）、kernel release/cmdline 均匹配。

唯一服务操作是 Linux timesyncd 的一次 stop 和一次 start。未执行 disable/mask、adjtimex 写入、clocksource 写入、Windows/Hyper-V 时间配置、电源永久配置、kernel 修改或 `wsl --shutdown`。没有安装系统包、语言包或工具链；临时编译产物自动清理。PowerShell 仅使用进程级 ExecutionPolicy Bypass 和临时防自动睡眠请求。

没有运行 SPEC Base、compress 正式测试、3+3、JVM 参数 benchmark、Serial GC、Peak；没有配置 VM、准备 Teacher Submission Package 或操作水杉。正式 `A2/README.md`、A1、历史 probe 和历史 raw 不变；旧 invalidated 结果不恢复正式资格。

建议下一阶段继续评估 WSL，在受控 timing 环境下先做更长稳定性 Gate，再决定正式性能实验；现在不直接迁移 VMware，也不启动正式 benchmark。本阶段在证据发布与远端核对后停止，等待对真实 GitHub 文件的复核。

## Reviewer Notes

- [probe](../../tools/host-reference-probe.py)、[Java](../../tools/HostReferenceClock.java)、[PowerShell wrapper](../../tools/run-host-reference-gate.ps1)。
- 两轮 `host-summary.json`、`guest-summary.json`、`samples.jsonl`、`jumps.json`、`command.json` 与 [独立复算源码](../../tools/recalculate-host-reference.py)。
- [preflight](preflight.json)、[stop](stop.json)、[settling](settling.json)、[wrapper 自测](self-test/validation.json)、[overhead](wrapper-overhead-analysis.json)。
- [active control](active-control/guest-summary.json)、[start-control](start-control.json)、[restore](restore.json)、[全部独立复算](independent-calculation.json)。
