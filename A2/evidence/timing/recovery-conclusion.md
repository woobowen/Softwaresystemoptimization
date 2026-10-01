# Hyper-V clocksource 恢复试验结论

> 本文保留上次恢复试验的操作和结论；其中“没有 commit/push”指该次试验结束时。当前只发布 [GitHub 诊断检查点](../final/github-checkpoint.md)，下一步环境路线尚未选择，不执行新的恢复试验。

**BLOCKED_ENVIRONMENT_TIMING**。两次各约 600 秒的探针均在 `hyperv_clocksource_tsc_page` 下出现数十秒累计 wall/monotonic 差异。临时切换不足以恢复可信测量条件，按第五阶段提示词第 59 节停止此路线。没有运行新的 SPEC diagnostic、replacement Base 或 3+3，也没有 stage、commit、push 或水杉操作。

## 实测结果

| 探针 | 样本 | Python wall (s) | Python monotonic (s) | Python 差值 (s) | Java 差值 (s) | 前跳 / 后跳 | 门控 |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 601 | 639.180424 | 600.521209 | 38.659215 | 38.659787 | 16 / 0 | FAIL |
| 2 | 601 | 646.435680 | 600.148702 | 46.286978 | 46.287295 | 18 / 0 | FAIL |

两组均由 Python 与 OpenJDK 7u75 RI 同时采样，Java 使用上一阶段完全相同的源文件和 1 秒采样周期。两组 Java nanoTime 时长分别为 600.521213328、600.148705103 秒。两个 probe 进程退出码为 0，只表示采样完成；`gate_pass` 均为 false。

所有 1,202 个样本的 clocksource 都为 `hyperv_clocksource_tsc_page`，两次 boot ID 相同。第一组最大单步 Python 差为 3.329240 秒，第二组为 2.694235 秒；没有实际 wall 时间倒退。前/后跳计数以 interval difference 超过 ±50 ms 为界，Python 与 Java 数量一致。门控阈值是内部工程标准，不是 SPEC 规则；这里的失败由多秒跳变和数十秒累计差异直接支持。

原始 interval 与累计值见 [gate-1/samples.jsonl](gate-1/samples.jsonl)、[gate-2/samples.jsonl](gate-2/samples.jsonl)，汇总见 [第一组](gate-1/summary.json)、[第二组](gate-2/summary.json)，独立整数纳秒重算见各目录 `independent-calculation.json`，明显跳变见各目录 `jumps.json`。

## 实际操作与诊断

原值为 `tsc`，available 包含 `tsc hyperv_clocksource_tsc_page hyperv_clocksource_msr acpi_pm`。`sudo -n true` 没有可用的缓存凭据；已有 WSL root 入口可用，故仅执行已授权的 sysfs runtime 写入：

```text
wsl.exe --distribution Ubuntu-24.04 --user root --exec sh -c 'echo hyperv_clocksource_tsc_page > /sys/devices/system/clocksource/clocksource0/current_clocksource'
```

首次切换时间 2026-10-01T10:59:05.050467+08:00，之后等待 90 秒。第一轮失败后只读检查 guest kernel、timesync 状态、boot ID、宿主事件及探针代码；重新写入同一个 clocksource 并再次等待 90 秒后进行第二次独立探针。这是失败恢复复测，不是两轮连续通过。

第一轮 kernel 记录 `Adjusting hyperv_clocksource_tsc_page more than 11% (1472393379 vs 1862270976)`。两段指定时间窗口的 Windows System 日志查询均返回 NoMatchingEvents（按记录中的 provider/ID 筛选），guest kernel 没有匹配 suspend/resume 记录，boottime 与 monotonic 区间差接近零。未发现支持一次外部 suspend 解释这些重复跳变的证据；这些查询不证明所有宿主事件均可见。底层根因未确认，不能把 NTP 或 Hyper-V 某个机制直接定为唯一原因。

首次 PowerShell 查询的 Python 包装器因输出编码解码失败；改为读取 bytes 并按编码解码后，同一受限只读查询成功。见 [query repair](diagnostic-query-repair.json)。这不是探针失败，也没有更改系统设置。

## 恢复与数据保全

在 2026-10-01T11:27:11.412033+08:00 执行相同 WSL 入口的 `echo tsc > .../current_clocksource`，退出 0，回读为 `tsc`。见 [clocksource-restored.txt](clocksource-restored.txt)。没有修改 Windows 时间服务、电源、Hyper-V TimeSync、`.wslconfig`、boot 参数或永久默认 clocksource。

旧 .006、.007–.009、.011–.014 的原生内容全部保留在 [invalidated-results](invalidated-results/manifest.md)，共 154 文件、114 JPEG、98 个 HTML 本地资源链接；逐文件 SHA256 与源安装目录一致。原生 validity、分数、raw 和编号均未修改。旧五张图片及报告草稿、派生统计分别归档；正式 README 不再包含旧性能值。

下一步环境方案尚未决定，可能包括 clean WSL restart、普通 Linux VM、原生 Linux 或其他最小风险方案。需要先检查真实仓库和探针实现，再选择路线；本次发布不执行任何候选方案。
