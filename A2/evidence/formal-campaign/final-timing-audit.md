# 最终计时检查

所有时间单位为秒。Gate 与七次正式运行均通过；这不是最终工程验收。

| 运行 | Host elapsed | Guest monotonic | Host−guest | wall−monotonic | 最大单次 step | clocksource | timesyncd | boot ID | 状态 |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| Final Gate | 1800.512921700 | 1800.000213850 | 0.512707850 | -0.000000465 | 0.000992341 | tsc | inactive | `7af866bf-70f0-4652-bc4c-4d28a4eccfc6` | PASS |
| base-1 / SPECjvm2008.015 | 7964.088193700 | 7963.599677000 | 0.488516700 | -0.000000092 | 0.000294551 | tsc | inactive | `7af866bf-70f0-4652-bc4c-4d28a4eccfc6` | PASS |
| repeat-1 / SPECjvm2008.016 | 379.995140500 | 379.648732000 | 0.346408500 | -0.000000079 | 0.000001428 | tsc | inactive | `7af866bf-70f0-4652-bc4c-4d28a4eccfc6` | PASS |
| repeat-2 / SPECjvm2008.017 | 379.691281900 | 379.356557000 | 0.334724900 | -0.000000298 | 0.000001375 | tsc | inactive | `7af866bf-70f0-4652-bc4c-4d28a4eccfc6` | PASS |
| repeat-3 / SPECjvm2008.018 | 377.890115600 | 377.617053000 | 0.273062600 | 0.000000136 | 0.000001109 | tsc | inactive | `7af866bf-70f0-4652-bc4c-4d28a4eccfc6` | PASS |
| parameter-1 / SPECjvm2008.019 | 377.928816600 | 377.651880000 | 0.276936600 | 0.000000061 | 0.000001859 | tsc | inactive | `7af866bf-70f0-4652-bc4c-4d28a4eccfc6` | PASS |
| parameter-2 / SPECjvm2008.020 | 376.597620800 | 376.333215000 | 0.264405800 | 0.000000381 | 0.000001019 | tsc | inactive | `7af866bf-70f0-4652-bc4c-4d28a4eccfc6` | PASS |
| parameter-3 / SPECjvm2008.021 | 376.491692100 | 376.221014000 | 0.270678100 | -0.000000154 | 0.000001416 | tsc | inactive | `7af866bf-70f0-4652-bc4c-4d28a4eccfc6` | PASS |

Guest monotonic：Gate 使用采样首末区间，benchmark 使用 runner 包围 Java 进程的区间。Host Stopwatch 包含 WSL 启动及外围监视器准备/清理，所以 Host−guest 小幅为正。逐次 timing-review.json 中的 host_minus_guest_seconds 则对比更外层 launcher；两个边界没有混用。

wall−monotonic 与最大 step 来自原始 monitor 样本的独立计算；Gate 的最大 step 同时检查 Python 与 Java。没有超过 50 ms 的离散校正，没有睡眠、boot 或 clocksource 变化，服务在所有测量区间保持 inactive。

[Gate 独立复算](final-gate/independent-calculation.json) · [八次计时边界与配置记录](final-data-audit.json) · [完整统计](final-statistics.json) · [服务及配置恢复](restore.json)
