# systemd-timesyncd 隔离与 Windows Host Stopwatch 联合计时

本目录只记录 A2 的 timing 判别实验。起始 GitHub checkpoint 为
`1cf6011ff531a75ff09868185c4d6e92cd76df8b`，分支为 `main`。
正式报告、历史 probe、历史 raw 和 invalidated SPEC 结果保持原样。

结果为 **WSL_TIMING_ISOLATION_PASS**，事实、推断与未证明事项见 [conclusion.md](conclusion.md)。
两轮 off Gate 和 180 秒 active control 已完成；timesyncd 已恢复 active。

## 测量边界

[PowerShell wrapper](../../tools/run-host-reference-gate.ps1) 在 Windows 上启动
`System.Diagnostics.Stopwatch`，同步调用 `wsl.exe --distribution Ubuntu-24.04
--user addaswsw --exec /usr/bin/python3 ...`，等待该 probe 退出后停止计时。
Host Stopwatch 包含 WSL 调用、Python/Java 准备、采样和收尾；不包含启动
PowerShell 和编译临时防睡眠调用所需时间。原始 `ElapsedTicks`、`Frequency`
及包围该 Stopwatch 的另一对 host counter 值均保存到 `host-summary.json`。
Windows DateTime 仅作时间戳及旁证，不作为 elapsed 判据。

[Python probe](../../tools/host-reference-probe.py) 使用 `time.time()`、
`time.monotonic()`、`CLOCK_MONOTONIC_RAW`、`CLOCK_BOOTTIME`，然后通过 pipe
向独立 [Java 7 进程](../../tools/HostReferenceClock.java) 请求同一编号的
`currentTimeMillis()` 和 `nanoTime()`。Java 发出 READY 后才开始取样。
每次请求往返耗时写入 raw，以便识别采样错位。四个 Python clock 和两个 Java
clock 是相邻顺序读取，并非硬件级同时读取。

首次 monotonic 样本为起点，约每 1 秒取样，monotonic 差达到 600 秒后结束。
每个样本记录 clocksource；boot ID 和 service state 在前后检查。
每次调用启动新的 PowerShell、Python 和 Java 进程，拒绝覆盖已存在的 guest 输出目录。
Java 编译产物位于自动清理的临时目录，源码保留在 `evidence/tools/`。

## 操作与边界测试

- [preflight.json](preflight.json)：Linux/Windows 状态、配置 SHA256、NTP 状态及
  `adjtimex(modes=0)`。读取工具为 [capture-isolation-state.py](../../tools/capture-isolation-state.py)。
- [wrapper-noop.json](wrapper-noop.json)：由同一 Stopwatch 包围 Linux `true`，估计空调用开销。
- [wrapper-overhead.json](wrapper-overhead.json)：包围 Linux `sleep 5`。
  `host - 5` 包含 sleep 的时钟行为、调度和调用开销，不能全部算作纯 invocation overhead。
- [wrapper-exit-check.json](wrapper-exit-check.json)：Linux `exit 7` 被准确传回。
- [self-test/validation.json](self-test/validation.json)：timesyncd active 时的 15 秒自测；不计 Gate。
- [wrapper-initial-error.json](wrapper-initial-error.json)：UNC 未签名脚本被拒绝，未启动 probe。
  后续使用 `powershell.exe -ExecutionPolicy Bypass`，仅作用于该子进程；没有运行
  `Set-ExecutionPolicy` 或修改永久策略。首次错误记录有 UTF-8 解码替代字符。
- [stop.json](stop.json)：仅通过已有 WSL root 入口执行 `systemctl stop systemd-timesyncd.service`。
- [settling.json](settling.json)：约 60 秒 settling 中的 Linux clocks 和 Windows UTC。
- [adjtimex-after-stop.json](adjtimex-after-stop.json)：停止后的只读校时状态。

wrapper 在计时前调用 `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)`，
在 `finally` 中清除临时请求；返回值保存在 host summary。不修改永久电源方案，也不能阻止
用户手动睡眠或合盖。preflight 记录宿主接通电源。

## 复算与判断方法

[recalculate-host-reference.py](../../tools/recalculate-host-reference.py) 不导入 probe，
从 `samples.jsonl` 以 Decimal 重算六种 elapsed、逐 interval 的 wall/monotonic 差、
前跳/后跳计数，并从 host `ElapsedTicks / Frequency` 重算 Stopwatch。
原始 Python 浮点数序列化误差允许 1 微秒；Java 时间戳和 host ticks 直接做整数差。
总复算结果为 [independent-calculation.json](independent-calculation.json)。Windows host JSON 的
CRLF 统一为 LF，数值和 JSON tokens 未更改；前后哈希见 [host-output-normalization.json](host-output-normalization.json)。

内部工程判断主要比较 host 与 monotonic/nanoTime 的 600 秒累计差：小于 2 秒为接受参考，
2–3 秒需结合实际准备和调用开销，超过 5 秒需检查，超过 10 秒为严重异常。
raw、boottime 也分别对比。逐 interval 的 ±50 ms 用于标记，±0.5 秒和 ±1 秒
单独计数；不把每个 50 ms 事件都称为系统故障。这些不是 SPEC 规则。

复现单次 probe 的 PowerShell 调用参数见每轮 `wrapper-command.json`，guest/Java 命令及
源码 SHA256 见 `command.json`。复算命令（不执行新 probe）：

```bash
python3 A2/evidence/tools/recalculate-host-reference.py \
  A2/evidence/timing/timesyncd-isolation/gate-1 \
  A2/evidence/timing/timesyncd-isolation/gate-2
```

API 依据：[Microsoft Stopwatch](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.stopwatch?view=netframework-4.8.1)、
[SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)。

## 目录入口

`self-test/`、`gate-1/`、`gate-2/` 和 `active-control/` 各有独立的 `host-summary.json`、
`guest-summary.json`、`samples.jsonl`、`jumps.json`、`java-stderr.log`、`command.json`、
service 前后记录和 `independent-calculation.json`。Gate/control 另保存完整 PowerShell argv。
`gate-independence.json` 核对进程独立性，`preserved-files.json` 保留历史源码与正式报告哈希。
`start-control.json` 是恢复 active 的实际命令记录，`restore.json` 是 control 后与 preflight 的状态对照。
