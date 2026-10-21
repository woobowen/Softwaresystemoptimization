# 本地交付审核结论

本地源码、实验、逐题报告和截图复核通过。工程状态为 CODEX_COMPLETE；ChatGPT 阶段验收 PENDING，教师提交 NOT_READY。没有把原生代理内部审查等同于外部验收，没有声明 Engineering PASS 或 Submission PASS。

## 已完成范围

两个 Checkoff、七个 Write-up（含原选做2/3/7）及完整lscpu均已完成。六个排序阶段保留，统一驱动的必要修正与算法优化分开记录。所有排序比较基于同一共同有效域；memcheck/sanitizer和极值补充已完成。详细对应在 `../requirements.md`。

- 正常性能10批共245个独立进程（不计49个预热进程），490个按输入区分的进程均值、2450次排序；原始单次时间、全进程均值及汇总均保留。
- 阈值32来自8/16/32/64有限比较。中大规模两输入等权下m/f为1.6772x/1.6765x，结果接近；random的c最快，不能把每一阶段都写成加速。
- Checkoff1是原isort DEBUG=1的227个cpu-clock:u样本，热点第20行；硬件事件不可用的实际错误/输出保留，未伪称硬件cycles/instructions/branch-misses。
- Checkoff2严格保留首次原U/N完整运行，后带-g统一批次亦完整重跑原配置与四个控制配置，模拟几何与全局/逐行分母区分清楚。
- W2/W3真实汇编确认复制/归并内联，递归未展开；noinline对照机器码相同，不编造代码膨胀或指令缓存负面效果。
- m/f的奇数、重复、极值和子数组检查通过，覆盖不变量与空间说明已核对。m/f分配次数由实际包装器测得，另外说明结构推导。

## 审查与修正

主执行者root唯一实现和调度负载；原生代理 `/root/code_review` 未参与实现，只读代码与实验证据，独立复算数据；`/root/report_review` 连续阅读全文、逐张查看12图、核对链接和结果。两者各自只写独占审查记录，均未编译或运行性能负载。

- 代码/数据审查：`../review/code-review.md`，未遗留阻塞级问题。
- 报告/截图审查：`../review/report-review.md`，未遗留必须修复问题。
- 已修正正式截图误含受控负向测试、1656合计数量表述、total/available内存措辞。重拍受影响截图并复核；代码和实验条件未变，不重跑无关正式样本。
- 主执行者再次连续阅读完整最终README，阅读全部最终排序实现，核对边界、静态函数、缓冲区生命周期、分配、简单性和实际数据。`validation.txt` 独立重算样本并检查采样索引、最终源码快照、图片/命令哈希及相对链接。
- 归档时发现旧原地构建路径已被清理，改为按原二进制SHA解析保留路径。最早inline构建经保存源码恢复，整个二进制SHA与原记录精确相同；技术审查者复核了10批匹配关系、恢复源码两处差异与94项本地索引。没有替换原始样本或重新挑选结果，详见 `../debug/fixes.md`。

## 文件整理和重新构建

所有正式源码/报告/截图在P2，内证按environment/commands/correctness/debug/performance/profiling/review/final分类。最终源码目录不保留二进制、对象、缓存或采样原件。make clean的规则事先已阅读，原始采样及匹配二进制已安全保存在根 `.cache/P2/` 后才清理。

官方附带、实际与本题无关的Python2 verifier未纳入正式P2目录；其完整原件仍在 `.cache/P2/materials/starter/recitation/verifier.py`，没有修改或安装Python2。isort构建所需的官方qsort.c保留，未用它替代本题被测算法。lscpu完整输出放在P2根以支持后续干净教师包。

从干净P2复制到 `.cache/P2/isolated-review/P2` 后重新构建，执行README两条命令、1656个qsort对照、原isort10000/10和原sum的一亿访问，全部正常结束。该检查只用于文件整理后的复现，不替换任何正式计时表；输出在 `isolated-build-run.txt`、`isolated-recitation.txt`。

`manifest.sha256` 同时作为完整文件清单与SHA-256索引（不包含它自身）。审核ZIP只含P2交付内容，不含官方PDF/ZIP重复副本、二进制、大型原始采样、其他任务、凭证或ZIP自身。压缩包校验使用同目录 `check-package.py`；最终归档SHA和压缩包检查回执保存在包旁的receipt，避免内部自引用。

## 现有限制和后续边界

- 本机WSL没有暴露所需硬件PMU事件；软件Perf定位时间热点，Cachegrind单独模拟，未互相冒充。
- a/i/p/c保留原哨兵数据域限制；共同对照在原生成器[0,2^31)域，m/f的完整uint32域检查不泛化给前四版。
- 阈值及微小性能差只适用于本机本组输入，不宣称普遍最优或显著性。
- 新增系统包/语言包/工具链/全局配置均为0，仅复用现有工具并保存任务本地材料。
- Git保持main，基础SHA `65c2128e142bf59a6e19ff635b760be3729abbac`。本次P2尚未提交，没有新commit SHA。根任务DOCX和原有用户文件保留；其他作业及AGENTS不变。未push GitHub、未向水杉提交、未创建或切换Project02。
- 下一步等待ChatGPT阶段验收。后续发布/实际GitHub最终审查/Engineering PASS/Project02教师提交严格按既定阶段进行。
