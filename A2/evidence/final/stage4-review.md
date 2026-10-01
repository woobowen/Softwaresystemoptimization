# 第四阶段 checkpoint：等待系统诊断授权

Engineering Status：**BLOCKED_PENDING_USER_APPROVAL**，未达到 PUBLISHED_FOR_FINAL_REVIEW。没有宣布 Engineering = PASS，也没有 stage、commit 或 push。

## 测量完整性

- Timing：结论 C。[完整调查](../timing/conclusion.md)含冻结 runner 的哈希匹配源码、实际计时顺序、127 个历史运行样本、SPEC 源码摘录、全部 raw iteration 检查、限定时间范围的系统日志、10 分钟 Python/Java 探针。旧 Base 的 470.629 s 差异不是 preserve 耗时；新探针复现 49.9879 s 差异和 19 次跳变。
- Compress：[调查](../compress-investigation/conclusion.md)确认全部是 compress throughput。旧 Base 每次 loop 的中位耗时 3131 ms，三次单项约 1508.5–1531 ms；配置相同但 JVM suite context 不同。诊断 .014 得到 799.004529 ops/m，并再次出现 wall/monotonic 差异。不能把整个 2.22 倍差距归因于已证实的单一机制。
- 原七份结果不修改、不删除，仍在原位置；尚无可采用的 replacement Base。为了避免在已知异常的环境中浪费唯一一次重跑，先请求临时时钟源诊断。
- 新旧六次参数比较的时钟风险同样不能排除。原配置统计为 mean=800.593888、min=787.962750、max=812.582467、range=24.619717 ops/m；Serial mean=803.659302，range=6.402473 ops/m；变化 +0.382892%。这些是可复核的原始数字运算，不是可信性能效果的最终判定。

## 环境、JDK 与脚本

- 原七次正式运行与成功的 JDK7 预检使用相同 LD_PRELOAD；Base 的实际 /proc 映射也含系统 FreeType。字体失败发生在报告生成，源码中的 reporter 在测量循环结束后调用；预加载库从进程启动就存在，不能声称它只在报告阶段加载或绝对不影响性能。
- JDK8 子 JVM 的大量 compiler warning 阻塞未消费的 stderr 管道；源码只读取 stdout，现场栈停在 FileOutputStream.writeBytes。旧 Python runner 已写文件，归因仍为 SPEC startup 内部。已复查 decision、README、脚本注释、runner review 和历史 final audit；修正了 runner review 的 decision 路径。没有用新 runner 压力测试倒推旧故障根因。
- Parameter .011–.013 的 runner argv 和实际 PID cmdline 都包含 UseSerialGC；repeat .007–.009 不含。default/modified flags 来自另启 JVM；README 已明确此区别。
- 正式 scripts 仍只有 run-spec.py、summarize-spec.py。runner 新增准确命名的成对时钟字段和启动失败元数据；其余日志、进程组、信号、互斥和防覆盖逻辑保留。更新后的七类测试全部通过，真实 .014 运行结束并保全报告。
- parser 逐行阅读：只取 measurement、跳过 check、startup 独立命名、SciMark Monte Carlo 参与两个大小组、组/总分几何平均、TXT/单位校对、拒绝重复 raw 哈希、拒绝无效/缺失值。未硬编码分数或 run ID。原 10 用例及新增七个 compress 原始字段回归均通过，源码无需更改。
- check-experiments 原先把正在修改的 runner 与历史冻结哈希比较，触发失败；已改为核对历史源码副本。副本 SHA256 必须匹配旧记录；第一次重建因多一个空行未匹配，未保存；修正后匹配且检查通过。没有改动历史 run metadata 来迁就检查。
- 全部 A2 Python AST、shell bash -n 检查通过；ClockProbe.java 和只读 adjtimex C 工具均真实编译/运行。

## 文档、图片和文件

- README 已连续通读并做三类修订：删去重复的时长说明与长篇旧计时解释；简化第 7 题措辞；修正计时结论、FreeType 说明和独立 flags 来源。现为 140 行、6325 字符，含 1–7 全部题目，无 TODO。时钟未解决，不能宣布文档的性能结论最终通过。
- 九张旧图逐张实际打开，内容可读，未发现凭据。01–03 是历史 Java21/JDK8 环境图，已原样移动到 compatibility/images。04–09 六张仍被 README 引用；其中测量结果图片须在数据替换后更新。
- 原生 results：base/.006（84 文件），repeat/.007–.009（各 10），parameter/.011–.013（各 10），共 144 文件、109 JPEG、95 HTML 本地资源链接。重新计算 source/copy SHA256 全一致。诊断 .014 单独保存在 evidence/compress-investigation。
- 最大文件是老师要求的 Base raw，12,660,504 bytes；没有超过 50 MiB 的文件。内部探针编译产物在临时目录清理。Python 缓存最终清理，不作为源代码。
- A1 的 274 个文件、七个原 raw、老师 PDF、777 个套件文件、6 个 JDK 关键文件哈希未改变。
- [final-value-map.md](../timing/invalidated-derived/final-value-map.md)含 40 行来源映射；[requirement-matrix.md](../requirement-matrix.md)如实标记 Q2–Q7 的数据或收尾限制，没有把有标题当作通过。
- README 的 15 个本地链接与全部 6 个图片链接存在；三张移动图片的现路径更新在 provenance，旧 checkpoint 中的历史路径由 file-moves.json 追踪，原历史输出不伪造改写。
- .gitignore 保留 A2/results，排除 materials/A2；AGENTS.md 的既有修改均为可复用的稳定规则，没有写入本次 run ID、JDK7u75、分数或 homework02。根 README 是索引，但暂不新增尚未发布的 A2 入口。
- secret 模式检查未发现命中；没有打包 JDK、SPEC 安装器或 cache。

## 八项循环状态

| 循环 | 结论 |
|---|---|
| Measurement Integrity | 未通过：现有环境有可复现时钟跳变 |
| Reproducibility | 历史 JDK/环境/命令可追溯；稳定测量环境尚待恢复 |
| Data | 旧 raw、统计、报告数字吻合；不能把算术正确当成测量可信 |
| Documentation | 已完成减法、自然表达和技术准确性检查；最终结论待重测 |
| Screenshots | 9 张实际打开；6 张正式引用；结果图待重测更新 |
| Code | runner 与 parser 的相关用例通过；历史 hash 检查已适配 |
| File Hygiene | 文件保全、位置、输入隔离和大文件检查完成 |
| Teacher Questions | 已重新阅读 PDF 1–7 题；总体状态未满足发布条件 |

## Git 与边界

仓库为 GitHub woobowen/Softwaresystemoptimization，分支 main；本地 HEAD 仍为 `5dcc4949e16127c212ad587ed096865894ebf1de`。没有新 commit，暂存为空，未 push。没有宣称 local SHA 与远端 SHA 已作发布后一致性验证，也没有进行候选版本的远端文件检查。

没有修改 A1，没有 A3+、完整 Peak、额外参数搜索、刷分或水杉动作。新增 apt/pip/npm/cargo、工具链和全局配置修改均为零。

需要用户选择的具体操作见 [recovery-options.md](../timing/recovery-options.md)。提示词第 32 节限制系统全局配置及已确认方案的变更；待用户明确授权前不切换 clocksource。Reviewer 应首先检查时钟样本、harness 裁剪公式与原 raw，而不是接受原生 compliant 或脚本成功作为测量可信度保证。
