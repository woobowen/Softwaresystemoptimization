# GitHub timing investigation checkpoint（历史记录）

以下保存早期诊断检查点的状态，不代表最终实验状态。最新候选见 [final-review.md](final-review.md)和 [运行索引](../run-index.md)。

A2 Engineering：**BLOCKED_ENVIRONMENT_TIMING**。本提交供 ChatGPT 直接读取 GitHub 实际文件进行诊断，不表示 A2 完成或 Engineering = PASS。Submission：**NOT_READY**；未操作水杉。

本次开始时，本地 `main` 与 fetch 后的 `origin/main` 均为 `5dcc4949e16127c212ad587ed096865894ebf1de`。目标仓库为 [woobowen/Softwaresystemoptimization](https://github.com/woobowen/Softwaresystemoptimization)，分支 `main`。提交后的 SHA、远端 SHA 和 GitHub 内容读取核对结果以发布回执为准。

## 计时失败证据

旧 Base `.006` 的开始/结束日期差为 8404 s，runner 单调时钟区间为 7933.371 s，相差 **470.629 s**。历史 `wall_seconds` 实际是 monotonic elapsed，不能作为 wall-clock elapsed 使用。计时边界、127 个运行中观测点和 SPEC timer 逻辑见 [调查结论](../timing/conclusion.md)、[timeline](../timing/base-timeline.csv)、[SPEC 源码摘录及哈希](../timing/harness-excerpts.txt)和 [raw duration audit](../timing/raw-duration-audit.json)。

下表来自既有 raw samples 和 summary，本次没有重新运行探针。tsc 探针未生成 `gate_pass` 字段，但其多秒跳变和近 50 s 累计差不满足后来明确的计时门槛；两次 Hyper-V 探针的 `gate_pass` 均为 false。

| Clocksource / 探针 | 样本 | Python wall (s) | Python monotonic (s) | 累计差 (s) | Java wall (s) | Java nanoTime (s) | Java 差 (s) | Python / Java jumps（前 / 后） |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| tsc / probe-10min | 601 | 650.366261 | 600.378370 | 49.987891 | 650.366 | 600.378267 | 49.987733 | 18 / 1；18 / 1 |
| Hyper-V / gate-1 | 601 | 639.180424 | 600.521209 | 38.659215 | 639.181 | 600.521213 | 38.659787 | 16 / 0；16 / 0 |
| Hyper-V / gate-2 | 601 | 646.435680 | 600.148702 | 46.286978 | 646.436 | 600.148705 | 46.287295 | 18 / 0；18 / 0 |

Jumps 按相邻 wall 与 monotonic（Java 为 nanoTime）增量差超过 ±50 ms 计数，不等于实际 wall 时间倒退次数。Python 最大单步差依次为 +3.747466、+3.329240、+2.694235 s；tsc 最小单步差为 −1.086558 s。

- tsc：[summary](../timing/probe-10min/summary.json)、[raw samples](../timing/probe-10min/samples.jsonl)、[jumps](../timing/probe-10min/jumps.json)。
- Hyper-V 1：[summary](../timing/gate-1/summary.json)、[raw samples](../timing/gate-1/samples.jsonl)、[jumps](../timing/gate-1/jumps.json)。
- Hyper-V 2：[summary](../timing/gate-2/summary.json)、[raw samples](../timing/gate-2/samples.jsonl)、[jumps](../timing/gate-2/jumps.json)。
- [current / available（切换前）](../timing/clocksource-before.txt)、[首次切换](../timing/clocksource-after-switch.txt)、[第二次确认](../timing/clocksource-reasserted.txt)、[恢复 tsc](../timing/clocksource-restored.txt)。本次发布开始时只读回查也为 `tsc`，未再次切换。
- [恢复结论](../timing/recovery-conclusion.md)、[历史恢复方案](../timing/recovery-options.md)。没有修改持久化 clocksource、`.wslconfig` 或 Windows 时间服务。

## 结果与文档状态

旧 Base `.006`、原配置 `.007–.009`、Serial GC `.011–.013` 和 timing diagnostic `.014` 全部为 **TIMING-INVALIDATED investigation evidence**。这些结果来自真实运行，但由于随后发现系统计时异常，不再用于正式性能结论。原生分数、validity、raw、HTML、TXT、run ID 和内部资源保持原样；[迁移 manifest](../timing/invalidated-results/manifest.md)及 [逐文件 SHA256](../timing/invalidated-results/file-manifest.json)保留原路径与现路径。

其余兼容性/短测 `.001–.005`、`.010` 仍留在原有 evidence 位置，也不作为正式性能结果。`.004` 字体故障留下的空 JPEG 是失败现场，不能替换成成功图像。

当前没有 replacement Base、final 3+3 或 final performance report；`A2/results/` 不存在。[README](../../README.md)保留系统信息和第 1–7 题：第 2 题缺可信 Base，第 3/4/5/7 题缺正式比较数据，第 6 题仅记录已有经历。[要求表](../requirement-matrix.md)标明这些缺项。

正式图片仅为 `04-environment.png` 和 `07-official-result.png`。Java 21/JDK 8 旧图保留在 `evidence/compatibility/images/`；旧环境、Base、repeat、参数成绩图保留在 `evidence/timing/invalidated-images/`，均不作为本机正式性能图。

## 可审查源码与边界

正式脚本为 [run-spec.py](../../scripts/run-spec.py)和 [summarize-spec.py](../../scripts/summarize-spec.py)，本次不重构。内部工具见 [tools 说明](../tools/README.md)。原 tsc Python/Java 源码保留在 `timing/probe-10min/`；两次 Hyper-V probe 源码在 `tools/`，无需恢复已删除的临时 `.class` 文件即可检查采样逻辑。

runner 将 stdout/stderr 直接写入两个文件，保存 exact argv、环境白名单、PID、exit code、wall/monotonic 和起止 clocksource。它记录观测值，不负责证明时钟可信。parser 的 native validity 检查也不能替代计时完整性检查；历史 raw 仅用于 regression fixture。

探针并非同时原子读取两种时钟：Java 连续读取 nanoTime/currentTimeMillis，Python 在收到每行输出后采样。Hyper-V 版 probe/monitor 的 clocksource 判定写死为 `hyperv_clocksource_tsc_page`；进程退出 0 仅说明采样完成，必须另看 summary 的 `gate_pass`。本次保留源码供检查，不把它直接当作其他环境的通用门控工具。

## 下一步尚未决定

先独立检查 timing probe 实现、raw samples、SPEC timer evidence、runner、invalidated raw 与 README，再选择 clean WSL restart、普通 Linux VM、原生 Linux、检查/改变 WSL version/kernel 或其他最小风险路线。这里不预选、不执行任何路线。

本阶段只整理、做离线文件与脚本检查、commit/push GitHub 和读取远端验证。不运行 Base、3+3、JVM 参数实验或新 timing probe，不切 clocksource，不修改 Windows/WSL 全局设置，不运行 Peak 或 A3+，不准备或提交水杉包。

## 本地发布检查

[检查记录](checkpoint-local-validation.json)包含 14 个原生目录、434 个文件与安装目录原件的 SHA256 对照，8 个迁移目录的 154 个文件全部匹配既有 manifest；336 个 native HTML 本地资源链接无缺失。三组 timing raw 只做离线复算，没有重新采样。runner 的 6 个假进程场景、parser 的 15 个历史 fixture 用例和源码语法/编译检查通过。

完整 `git diff --cached --check` 对原生 TXT/SUB/summary、历史日志、CSV 及旧报告中的原有空白返回 2。这些文件逐一核对与整理前字节相同，按证据保全要求保留；本次编辑的 README、文档和源码单独检查通过。没有为了消除格式警告修改原始输出，也没有调整 Git whitespace 配置。
