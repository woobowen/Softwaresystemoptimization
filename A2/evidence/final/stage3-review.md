# 第三阶段本地最终检查

记录时间：2026-10-01T04:05:09.765693+08:00。本记录属于本地执行与复查，不替代独立阶段验收，也不赋予 Engineering = PASS。阶段范围只有 A2，未暂存、提交、推送、创建分支或提交水杉 / SPEC。

## 七个检查循环

1. **实验**：重新核对完整 Base、三次原配置、三次修改配置的 run.json、assessment.json 与原生目录。Base 38 项计分 workload、checksum/correctness 通过；六次单项均正确。JDK / runner / 环境固定，compress 22 个基准线程与 120/240 秒相同，独立 PID 和时间次序成立。正式结果为 .006、.007–009、.011–013，诊断 .010 不参与统计。见 [experiment-comparison.json](../timing/invalidated-derived/experiment-comparison.json)。
2. **数据**：重新解析 raw，与 TXT / HTML / summary、README 和截图统计核对。Base 482.49，原配置均值 800.59，修改后 803.66，变化 +0.38%。七份原生目录 144 个文件逐文件与来源哈希相同，109 张 JPEG 解码、95 处 HTML 资源链接检查通过。见 [data-check.json](../timing/invalidated-derived/data-check.json)。
3. **runner / scripts**：完整阅读两份正式脚本及所有新增内部 Python、shell、Java 源文件，核对实际压力、退出码、信号、错误输入和真实实验测试。修正截图工具的失败退出处理并实际测试。当前 10 个 Python 文件 AST 与 5 个 shell 文件 bash -n 成功；FontProbe 已用 JDK 7 编译运行。详见 [script-review.md](../timing/invalidated-derived/script-review.md)。
4. **截图**：九张 PNG 均通过 view_image 实际打开。04/05/06/07/08/09 在报告中，内容与冻结环境、Base、官方记录和六次数据一致。01/02/03 为保留的历史记录。没有编辑图像像素，没有用文本绘制终端。来源、哈希和逐图检查说明见 [screenshot-provenance.json](../environment/screenshot-provenance.json)。
5. **README**：按下面四轮完成全文连读，删去重复和含糊表达，保留所有必要数字、原生元数据限制和计时限制。没有 TODO、诊断分数冒充正式结果或内部工作流程词。自然程度仍应由独立阅读者评价。
6. **文件卫生**：使用 rg --files --hidden --no-ignore 检查整个 A2；无 class / pyc / ELF / object / installer / cache / 空目录。保留唯一压缩的 JDK 8 原始诊断日志和失败报告，未按普通临时文件删除。144 个正式结果不被 ignore；老师 PDF 原件存在且位于已忽略输入目录。常见 secret / token / SSH 私钥格式扫描没有命中。274 个 A1 文件、AGENTS.md、.gitignore 与老师 PDF 共 277 个保护文件哈希不变；777 个 SPEC 文件与六个 JDK 关键文件不变。见 [hygiene-check.json](../timing/invalidated-derived/hygiene-check.json)。
7. **老师原题**：再次用 pdftotext 读取原 PDF，并实际打开其两页渲染图，逐题对照第 1–7 题。用途和 Base/Peak、完整 Base、三项分析、官方比较、三次重复、真实体会、一个参数的两组三次均可从 README + images + results 找到。对应关系见 [requirement-matrix.md](../requirement-matrix.md)。

## 四轮 README 连读

| 轮次 | 检查重点 | 实际处理 |
|---|---|---|
| 1 | 老师原题与内容覆盖 | 核对七题；补充 Peak 可按测试项调优，三个 workload 分开解释，区分 crypto 组分数与 crypto.aes 子项分数 |
| 2 | raw、报告、截图与正文数字 | 重新计算全部正式数值并核对链接；检查代码最初把 FAQ 的 #Q4.8 当成章节边界，改为只按行首 ## n. 分节后通过；报告本身没有缺第 2 题 |
| 3 | 连续阅读、冗余与指代 | 删除第 1 题与第 3 题重复的跨 workload 比值提醒；第 7 题将“这组三次”改为“两组三次结果”，明确 3.08% 属于原配置、0.80% 属于修改配置 |
| 4 | 修改后从头至尾复读 | 检查七题顺序、首句与回答、表文关系、限制说明与自然衔接；保留必要的兼容问题与计时现象，不再扩展背景或重复操作证明 |

## 重要问题、修复与保留限制

- **JDK 8 startup 阻塞**：旧 Python runner 本来已使用文件输出。实际是 SPEC startup 只读取子 JVM stdout，未读 stderr；旧 javac 的版本警告写满内部管道。runner 增强直接输出与信号处理并通过压力测试；正式套件改用获授权的官方 JDK 7，全套预检后才运行 Base，没有改动 SPEC 源码。
- **JDK 7 报告字体失败**：第一次全套短测 38 项计算正确但图片失败，Java exit 0 未反映报告错误。动态加载器显示 JDK 自带 FreeType 缺少系统 fontconfig 需要的 FT_Done_MM_Var。进程级预加载已安装系统 FreeType 后，FontProbe、原始 raw 的独立 reporter 诊断及第二次全套预检成功。原失败目录完整保留。
- **参数原生元数据 n/a**：smoke 后的附加检查曾错误要求原生 JVM 字段包含参数。源码确认该采集需要 -pja；改为检查实际 argv / PrintFlagsFinal / 运行中 /proc，保持原配置与修改配置的 SPEC 参数相同。没有改写 raw 的 n/a 或 Base 标题。六次单项仅因非完整发表序列而 noncompliant，不代表计算失败。
- **截图工具错误处理**：原工具没有验证截图命令的返回值；增加失败阻止写图并通过 exit 7 用例验证。正式图 09 命令 exit 0。
- **WSL2 计时差异**：Base 日期时间相差 8404 秒，单调计时 7933.371 秒；单独 30 秒等待也观察到约 32.214 秒日期时间变化。没有确定宿主侧根因，没有改 Windows/WSL 配置或校正分数。源码中的计划测量时长不能证明两类时钟速率一致，详见 [timekeeping-analysis.md](../environment/timekeeping-analysis.md)。
- **历史 01 转录为空**：旧 terminal.txt 不能证明命令输出，已在安装记录与截图来源中纠正；01 图片保留为历史材料，正式报告使用新图 04。初始环境事实另有 initial-environment.txt。
- **结论边界**：native compliant 只描述套件自产生的状态，不代表官方发表审核。参数均值变化 0.38% 小于两组各自波动，不声称提升或测量了 GC 次数 / 暂停时间。

## 环境变更与 Git

本阶段只新增官方 OpenJDK 7u75 RI 用户级工具链及仓库外下载缓存。新增 apt / pip / npm / cargo 包、字体、数据库均为零；没有改全局 alternatives、shell、Windows 或 WSL 配置。Java 21、JDK 8、SPEC 和缓存按指示保留。详见 [installation-log.md](../environment/installation-log.md)。

实际检查了 git status --short、git diff --stat、git diff -- . ':!A2/results/**' 以及暂存区。分支仍 main，HEAD 仍 5dcc4949e16127c212ad587ed096865894ebf1de；AGENTS.md 与 .gitignore 的 Git 差异来自本阶段开始前，A2 仍未跟踪。暂存区为空，没有 GitHub / 水杉 / SPEC 提交；远程 SHA 不属于本阶段操作范围。

独立复查重点：七份 raw 与完整原生目录、六次真实命令 / flags / 进程记录、README、六张报告图、runner 的压力与信号测试，以及 WSL2 计时和原生参数字段的限制。
