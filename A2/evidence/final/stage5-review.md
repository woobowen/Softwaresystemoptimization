# 第五阶段收尾：时钟恢复试验失败

**Engineering Status: BLOCKED_ENVIRONMENT_TIMING**。已按提示词允许的失败路径保存证据、恢复 `tsc` 并完成可完成的本地整理。A2 的正式重测与 GitHub 发布没有完成；未授予 Engineering = PASS。

## 1. Clocksource

原值 `tsc`，available 为 `tsc hyperv_clocksource_tsc_page hyperv_clocksource_msr acpi_pm`。先保存 [原状态](../timing/clocksource-before.txt)，通过已验证可用的 WSL root 入口执行已授权的 sysfs runtime 写入，回读为 Hyper-V；第一轮失败后重新写同一值。两次分别等待约 90 秒，没有改 NTP、Windows 时间服务、电源、`.wslconfig` 或 boot 参数。`sudo -n true` 无缓存凭据，未请求或保存密码。

实际切换命令：

```text
wsl.exe --distribution Ubuntu-24.04 --user root --exec sh -c 'echo hyperv_clocksource_tsc_page > /sys/devices/system/clocksource/clocksource0/current_clocksource'
```

恢复命令同样通过 WSL root 入口写 `tsc`，退出 0，最终回读为 `tsc`；[恢复证据](../timing/clocksource-restored.txt)。

## 2. Timing Gate 1 与恢复复测

| 项目 | 第一次 | 第二次 |
|---|---:|---:|
| Python wall (s) | 639.180424 | 646.435680 |
| Python monotonic (s) | 600.521209 | 600.148702 |
| Python 累计差值 (s) | 38.659215 | 46.286978 |
| Java wall (s) | 639.181000 | 646.436000 |
| Java nanoTime (s) | 600.521213 | 600.148705 |
| Java 累计差值 (s) | 38.659787 | 46.287295 |
| Python/Java 前跳次数（>50 ms） | 16 / 16 | 18 / 18 |
| Python/Java 后跳次数（<-50 ms） | 0 / 0 | 0 / 0 |
| 每组样本数 | 601 | 601 |
| clocksource | 全程 Hyper-V | 全程 Hyper-V |
| Timing Gate | FAIL | FAIL |

第二次是第一轮失败后的独立恢复复测，不是两轮连续通过。两次采样进程退出 0；不能把这个退出码解释为计时通过。没有 clocksource 回切或 boot ID 改变。限定窗口的宿主事件查询没有匹配事件；第一轮内核出现 `Adjusting hyperv_clocksource_tsc_page more than 11%`。探针源与整数复算、全部只读诊断、首次 PowerShell 编码错误及一次修复均保留在 [timing 结论](../timing/recovery-conclusion.md)。底层根因仍未确认。

## 3. 正式实验与成绩

| 项目 | 实际执行 / 结果 |
|---|---|
| 新 compress timing diagnostic | NOT_RUN，门控未通过；无 wall/monotonic/score |
| Replacement Base | NOT_RUN；无 native ID、PID、起止时间、38 项分数、checksum、correctness 或合规性新判定 |
| 第 3 题 compress / derby / crypto.aes | 无新 Base 分数，仅保留 workload 特点 |
| 第 4 题 | 官方 853.15 及配置重新获取成功；无本机新分数，未计算差距 |
| 第 5 题 FINAL-REPEAT-1/2/3 | NOT_RUN；无均值、min/max、range、relative range |
| 第 7 题 FINAL-SERIAL-1/2/3 | NOT_RUN；仍固定 -XX:+UseSerialGC，无变化百分比或优化结论 |
| Base vs single compress | 无新数据，见 [final-comparison.md](../compress-investigation/final-comparison.md) |
| 最终正式环境冻结 | NOT_RUN；没有建立 final-formal-environment.json 冒充稳定环境 |
| GitHub 候选发布 | NOT_RUN；没有 stage、commit、push |

计划使用的 JDK 仍为 OpenJDK 7u75 RI，FreeType 仍为 `/usr/lib/x86_64-linux-gnu/libfreetype.so.6`。Base 命令仍为 `java -jar SPECjvm2008.jar --base`，没有 JVM 调优或 properties 修改；这里记的是既定方案，不是第五阶段执行过的 Base 命令。

## 4. 旧数据与当前文档

旧 Base .006、repeat .007–.009、Serial .011–.013 和 diagnostic .014 均在 [invalidated-results](../timing/invalidated-results/manifest.md)，8 目录、154 文件，raw/HTML/编号/validity 未改变。SHA256 与源安装目录逐文件一致，114 JPEG 和 98 HTML 本地链接正常。旧五张图片在 [invalidated-images](../timing/invalidated-images/manifest.json)，旧报告和统计另行归档。旧 3+3 不参与当前 README 的统计或结论。

[A2/README.md](../../README.md) 保留身份、系统信息和 1–7 原题顺序，无 TODO、旧性能值或内部工作流词。第 2/3/4/5/7 题仍有实质性实验缺项，报告如实说明，不能作为完成稿提交。

当前图片仅为：

- [04-environment.png](../formal-campaign/preparation/04-environment.png)：实际 Zutty/Xvfb 截图，JDK/变量/恢复后的 tsc；已打开。
- [07-official-result.png](../../images/07-official-result.png)：官方 Summary，在线内容哈希未变；已打开。

没有生成不存在的新 Base 或 3+3 截图。当前不存在 `A2/results/`，没有放入任何不可信“正式结果”；所有旧原生目录均已完整归档。

正式脚本只有 [run-spec.py](../../scripts/run-spec.py)、[summarize-spec.py](../../scripts/summarize-spec.py)。内部工具迁移见 [stage5-tool-moves.json](stage5-tool-moves.json)，代码检查见 [script-review.md](script-review.md)。

当前 [数值映射](final-value-map.md)、[逐题要求表](../requirement-matrix.md)、[运行索引](../run-index.md) 均明确区分已有配置资料和缺失的可信性能数据。Q1 与 Q6 的过程说明可完成；整体作业不能通过。

## 5. 本地循环结果

| 循环 | 结论 |
|---|---|
| Measurement | FAIL：两次约 600 秒探针均有数十秒级差异 |
| Data | 当前配置/官方数值可追溯；旧 raw 副本完整；新正式数据核对 NOT_RUN |
| Code | runner 实际用例和 parser 历史 fixture 用例通过；Java/C 实际编译运行；Python/shell 语法通过 |
| README | 逐题检查、删旧数据、准确性和连续阅读完成；实测缺项保留，不宣称成品 |
| Screenshots | 当前两张已打开，来源真实；新成绩图 NOT_RUN |
| File hygiene | 本地清理检查通过；Markdown 本地链接无断链、无编译缓存、无高置信凭据模式命中 |
| Teacher questions | NOT_READY：缺可信 Base 与 3+3，不能满足 Q1–Q6 全部 PASS |

[本地检查记录](stage5-cleanup-check.json)只验证整理与保全，不代表测量可信。A1 的 272 个跟踪文件、老师 A2 PDF、777 个 SPEC 原始文件和 6 个 JDK 关键文件哈希未变。本阶段未修改 AGENTS.md 或 .gitignore 的既有改动，未写入 A2 clocksource 永久规则。

唯一超过 10 MiB 的 A2 文件为已归档的旧 Base raw，12,660,504 bytes；它是必须保留的原始测量数据。没有安装包、JDK archive、teacher PDF 或编译产物进入 A2 正式目录。

## 6. Git、安装与剩余工作

仓库 `woobowen/Softwaresystemoptimization`，branch `main`。本地 SHA 与只读 ls-remote 查询到的远端 SHA 均为 `5dcc4949e16127c212ad587ed096865894ebf1de`，相等；这是原历史提交，**不表示 A2 已发布**。新 commit 数为 0，暂存为空。见 [git-stage5.json](git-stage5.json)。没有对新的 GitHub A2 文件树作发布后验收，因为根本没有发布。

没有访问、克隆、切换或提交水杉 homework02。没有 A3+、Peak、额外参数搜索或为追分重跑。系统包、语言级包、工具链新增均为 0；临时 runtime clocksource 已恢复，永久系统配置修改为 0，无新增依赖需要清理。

剩余工作需要计时稳定的 Linux 原生或 VM 环境：先通过 timing gate，再完成 SPEC diagnostic、唯一 Base、3+3、数据驱动报告与截图及最终 GitHub 发布。本阶段不再运行第三次探针，不扩展到 Windows TimeSync 或内核配置修改。

审核重点是两组逐秒时钟样本、实际恢复记录、归档原始字节及 README 的缺项表述；不能把原生 compliant、parser 测试或本地整理通过代替新性能测量。当前没有可交付给远端最终工程验收的新候选版本。
