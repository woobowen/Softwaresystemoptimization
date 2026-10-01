# P1 Goal 1 独立代码与正确性审核

审核角色：独立源码审核；不修改实现代码，不调度正式性能测量。

## 已读材料与边界

- 根 `AGENTS.md`、`P1_Goal1_Codex_Prompt.md` 全文。
- 老师 `P1 Matrix Multiplication Autotuner.pdf`（通过 `pdftotext -layout` 读取）。
- 根原始 `matrix_multiplication.c` 全文；原始副本的 SHA-256 与输入一致：`188d011109c4470e1f41829216e8677a5c2d8f2b7c8a44215652320dbdf6de15`。
- 未安装依赖、未改其他作业、未提交 Git。

## 原始程序预审

| 位置 | 严重性/状态 | 证据与判断 | 建议 |
| --- | --- | --- | --- |
| `matrix_multiplication.c:37–43` | 正确性要点已静态核对 | 内核为 `ih/jh/kh → il/kl/jl`；每个尾块同时检查局部长度与矩阵上界。4096 除 24 余 16，并非非法配置。每个 C 元素按递增 k 累加。 | 适配版保留循环次序、边界和计算式，同源验证覆盖 128 和 129。 |
| `matrix_multiplication.c:26–35,45–46` | 测量语义已静态核对 | 初始化在起始计时之前；输出是 `gettimeofday` 计时的内核区间。`tdiff` 返回 float，存在精度限制。 | 不将其当作进程或调优总成本；如改计时必须先说明并统一目标。本阶段优先保留老师计时。 |
| `matrix_multiplication.c:19–20` | 中：CLI 错误处理缺口 | `atoi` 接受带数字前缀的非法输入，`assert(argc==2)` 的行为依赖构建是否定义 NDEBUG。 | 最小 argc/strtol 完整解析并保持合法 s 运行一致。 |
| `matrix_multiplication.c:43–47` | 高：结果可观察性/正确性尚待执行核查 | C 未被读取；打印时间不能证明数值正确。全局 C 具有外部链接，不能由源码单独断言编译器已消除计算。 | 实查 original/adapted 高优化汇编；适配版计时后遍历 C 求校验和并输出，使结果可观察。 |

## 建议的必要验证

- 正式程序固定 `n=4096`、double、原随机初始化与原内核；四优化级别公共编译选项一致，只有 O 变化。
- 验证尺寸用受控宏 128、129；自动比较完整循环与老师原件，避免另写正确内核证明错误程序。
- 五种 s、四种 O、至少两个随机种子、正负输入及单位矩阵输入；全部元素与独立朴素三循环/高精度累计参考比较，记录最大绝对误差、最大相对误差及容差依据。
- 小规模 ASan/UBSan；非法 CLI；n4096 边角、分块边缘及预定随机点独立重算。抽样不可声称全量证明。
- 框架需实查配置、预算 0/1/20、失败、超时、解析非有限/非正值、随机复现、平局、无改进邻居、邻域中途耗尽、缓存键和恢复计数。

## 执行状态

已完整阅读适配版 `P1/src/matrix_multiplication.c`（60 行）并执行 `diff -u` 对照原件。第 43–49 行保留原件第 37–43 行循环（仅换行格式不同）；第 32–41 行默认初始化与计时起点未改变；第 54–58 行在结束计时后读取全 C 校验和。第 19–30 行的 argc/strtol 检查补上原输入缺口；超长整数导致 LONG_MAX/MIN 也被范围检查拒绝。没有发现需要阻断构建的静态问题。

stdout 现为时间与 `checksum=...` 两行，统一评估器必须按这个实际协议解析，拒绝非有限校验和及非有限/非正时间。全矩阵校验和使结果可观察，但不能代替独立逐元素数值验证。

在该预审时点，尚未收到主控的测量锁释放通知，未编译、未运行测试；同源验证脚本和框架尚待生成。后续实际执行与问题闭环记录如下；任何代码审核记录都不授予最终 Engineering PASS。

## 基线实现首次静态审核

已完整读取 `P1/scripts/validate_target.py`（157 行）与 `P1/src/autotuner.py`（457 行的首次生成版本）；以下行号对应该审核快照，修复后需再次核对。

验证生成器第 70–97 行先比较测量版/原版完整内核，再逐一检查唯一 marker 替换，最后再次比较；验证路径直接执行同一内核。第 20–34 行的参考为不分块的 dot product，使用 long double 累计，检查所有 C 元素有限性，并以 `1e-12 + 1e-11*|expected|` 为容差。第 109–111 行覆盖 n=128、129，各五 s、四 O、六组输入（3 个正随机种子、2 个符号随机种子、1 个单位矩阵）。全规模预定 O0/s24 与 O3/s128 各抽 24 点，明确是抽查。已读 owner 产生的 240 个小规模检查与五个 sanitizer 检查原始记录；它们不能代替审核者自己的运行。

| 位置（首次快照） | 严重性 | 证据与影响 | 已交 owner 的建议 |
| --- | --- | --- | --- |
| `P1/src/autotuner.py:179–189` | 中 | parse 只返回首行时间，`0.1\nchecksum=nan` 也会成为有效时间；本目标额外结果字段未被检查。 | 如出现 checksum 字段，严格要求唯一、有限，并保留一般小测试目标仅输出时间的兼容性。 |
| `P1/src/autotuner.py:79–85,98–104` | 高 | child spawn 后 on_start/持久化触发 OSError 时，异常分支未 kill/wait，可能留下未受控目标。 | 发生记录异常必须清理自身进程组并 wait，再抛出异常，不能伪造已完成记录。 |
| `P1/src/autotuner.py:89–103,311–317` | 高 | timeout/Ctrl+C 清理，但默认 SIGTERM 可留下独立 session 子进程；恢复直接标 interrupted，未拒绝仍存活的旧 PID，可能违反正式测量串行。 | SIGTERM 转为正常中断清理；恢复未完成 start 时核验 live PID 并拒绝，不盲杀可能复用的 PID。 |
| `P1/src/autotuner.py:379–381` | 中 | hard 退出遗漏未关闭 session/编译的真实时长；sum 完整记录可能输出 0 而没有未知标识。 | 在汇总标记成本不完整及已记录下界，不把未知当精确 0，也不把恢复间隔当计算时间。 |

owner 已确认处理 checksum、spawn 后异常清理、SIGTERM 与旧 PID 检测；成本标记建议已送达。尚未独立运行框架测试。必须修复并复核进程泄漏/恢复并发问题后再冻结基线。

## 审核者实际执行：目标

主控明确释放测量锁后，审核者独立执行了以下检查，未启动任何 n4096 计时或 full suite。

1. 分别执行 `gcc -std=c11 -Wall -Wextra -O3 -S` 原版与适配版，GCC 实际版本 `13.3.0`，均 exit 0 且 stderr 为空。原版两个 `gettimeofday` 调用在汇编第 117/248 行，`mulsd/addsd/movsd` 写 C 在第 190–192 行；适配版计时调用在第 150/278 行，乘加写 C 在第 220–222 行。两者有 4096 上界判断及内外循环回跳；不能声称原版发生整段计算消除。适配版全 C checksum 在第二个计时调用之后（第 299–312 行）。实际命令、源码/汇编 SHA 与完整计时区间保存于 `P1/evidence/environment/kernel_assembly.txt`。
2. 在自动清理的临时目录，使用已审阅的同源生成器重新编译 n128/n129 × O0/O1/O2/O3；各五 s、独立种子 2026 与 610、正随机/符号随机/单位矩阵三种输入，共 240 项，每项全元素检查。全部 exit 0，无编译告警和运行 stderr；同 n/seed/mode 的 checksum 字符串跨 s/O 一致。最大绝对误差 `4.720183e-14`，最大相对误差 `4.735401e-11`。相对误差近零分母较大时由绝对项约束，所有元素仍满足 `1e-12 + 1e-11*|reference|`，没有只按相对阈值判断。
3. 独立构建 n129/O1 ASan+UBSan，以 seed2026、符号随机输入执行全部五 s；五项均 exit 0、无 sanitizer stderr、全 16641 元素满足容差。

此次适配源码 SHA：`e321025e6097c9c8124c7e8624a6ae4132e2a54d426e135ae07d595a401be0b0`。生成 n128/n129 验证源 SHA 分别为 `5a5ce7991103ac12c594ab0c3ff4d4fc2b75b6d70071dff54f85ceab76d1f942`、`ce961697c315167526561e6e0207bf85e705bb10841b6bc6214fe91394dd0fe1`。使用系统现有 Python/GCC，未新增依赖。框架修复完成后仍需运行其单元测试、实际异常/恢复复测。

## 框架修复后首次独立执行

完整重读框架 524 行与 tests 341 行后，审核者执行 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s P1/tests -v`：18/18，实际 unittest 时长 3.332s，exit 0。这些夹具只检验逻辑，没有进入正式性能结果。

已核对首次四项问题的修复：checksum 有限/唯一且正式目标必须存在；on_start OSError 清理进程组并 wait 后抛出；CLI SIGTERM 进入中断清理；Evaluator 恢复拒绝仍存活的 group；缺失完整 build/session 结束记录时 cost 为 null，已记录下界单列。相关真实子进程 tests 通过。

继续发现并实际复现一项入口漏检：

| 位置（SHA `ece6a4efa24b8cd364138dd46dd3b55a078af5d75b4d5dd9c5ac585e7a8d32be`） | 严重性 | 实际证据 | 处理 |
| --- | --- | --- | --- |
| `P1/src/autotuner.py:496–501` | 高 | `build --resume` 直接调用 target.build，绕过 Evaluator 的旧 group 检查。审核者在 /tmp 用小 C 完成真实 build 后，构造 test-only 的 header+未完成 build_start，PID 指向自己的仍存活进程组，清理自己的临时 cache；resume exit 0、stderr 空、新增第二个真实 compiler build_start（共 2 个），原 group 仍活。临时进程已 kill/wait，临时目录自动清理。 | owner 确认并正在补 build 独立入口 live-group 检测及回归，同时补 build SIGTERM 后停止后续 opt。修复后需再复核。 |

因此框架尚未冻结；18 项测试通过没有掩盖额外发现。未再重复已完成目标数值套件。

## 第二次修复独立复核

完整重读框架 557 行/tests 371 行后，再执行相同 unittest 命令：20/20，实际 unittest 时长 3.597s，exit 0。框架 SHA `35c5436c4853e6917ae8bbe49d0f1fe855814740a58d813a15f8d43a1893b9dc`，tests SHA `60a3b6c55fe047abcb95bcebc948600cf3a27b000535776ee0187a25f0923bc8`。

- `unfinished_builds` 第 325–329 行按 build_key 与实际 compiler PID 匹配非 cached 完成记录；build 入口第 521–530 行检测遗留 group，且 interrupted 立即停止后续 opt。重复原审核者的独立临时 live-group 复现，现 exit 2、没有新编译、原 journal 两行不变；自己的临时 group 已清理。
- 第 345–349 行拒绝 completed trial ID 对不同 config 的错误复用；新增 trial/end-to-end 累计时间字段在正常试验用 monotonic，恢复的 trial wall 为 null，记录可确认的下界。单元测试有实际恢复和新增字段检查。
- 独立编译实际适配 n4096 源码（仅构建），运行无参数、0、负数、4097、8junk、nan、空参数、整数溢出、额外参数共九种输入；全部非零退出且没有进入 checksum/kernel。未执行任何合法 n4096 计时。
- 独立直接测试非有限与重复 checksum 解析，均拒绝。

此后主控指定在正式测量前将基础 Greedy 邻域改为离散索引相邻四邻居；owner 另自查发现 cached-build 的 emit 仍在缓存读取 try/except OSError 内，日志失败会被吞并意外重编译。正在按 owner 修改该两项并增加必要回归，待审核者再复核后才能冻结基础版本。目标 C 与数值验证未变，不重复无关套件。

## 基础版本审核关口

最新框架 SHA `e2e0baa908eb8d32771544b5102bca5ad8e358d2cc6aff9aafab6b4a7634fb27`；tests SHA `c14e68b69dde7c60bedfec98fe0fe577f4ff8b47866674ce9cc8a5aad8231458`。审核者再次完整核对改动及剩余代码，并执行同一 unittest 命令：23/23，实际 unittest 时长 4.971s，exit 0。

- `autotuner.py:67–74` 四邻域按参数列表中的相邻索引定义，输出保持固定 s-major 顺序。内点 24/O2 对应 16/O2、24/O1、24/O3、64/O2；角点 8/O0 对应 8/O1、16/O0。搜索以本次 seed 均匀选起点，完成尚未观测邻居后才比较，严格改进才移动，平局保持原点；预算在邻域中途耗尽时只使用已测配置的全局最优。没有读取网格参照，也没有预设好配置。
- `autotuner.py:162–174` cached 读取与 emit 分开；日志失败现在直接传播，不再落入 cache miss/recompile。新增 test 通过真实缓存准备和禁止 process 的 mock 验证没有隐藏重编译。
- `tests/test_autotuner.py:198–208,270–289` required checksum 缺失会成为 parse_error、不进入 best；Greedy 部分重复测量中断后恢复，用本次反馈重建相同轨迹且没有多计真实进程。
- 三个接口分别位于 ConfigSpace（52–74）、TargetProgram（119–245）、SearchStrategy（248–281）；Evaluator 统一负责编译复用、实际运行、重复中位数、记录与失败，Journal 提供轻量持久化。没有额外框架、数据库、继承层级或无用通用模块。
- 构建 identity 包含源码/编译器实际路径、版本、二进制 SHA 和完整 flags；s 仅作为运行参数。独立搜索使用独立 journal 与真实测量，缓存只复用编译产物。预算包含失败尝试；成功与失败过程数量有实际记录，硬退出的未知成本明确为 null，恢复不能将活旧进程与新目标并行。

本关口发现的关键问题已由实现 owner 修复并经审核者复核；未发现阻断主控串行 n4096 正确性抽查及预测试的剩余代码问题。审核者将停止编译/大量测试，待主控开启测量锁。本记录只批准进入下一必要工程步骤：n4096 同源抽查、协议冻结、正式实验、后续策略与最终冻结版本审核仍未由该记录替代；不宣称 Goal1 完成或最终 Engineering PASS。

## 预测试时钟异常与最小目标适配复核

测量锁开启期间仅仅读诊断，不编译或运行测试。审核者读取旧 pretest 00–03 原始 measurement，独立计算 UTC 与 monotonic 差值：

| 旧预试 | kernel s | process monotonic s | process UTC s | kernel − monotonic s |
| --- | ---: | ---: | ---: | ---: |
| 00/O3/s128 | 65.590950 | 61.350187 | 66.142915 | 4.240763 |
| 01/O0/s8 | 376.662109 | 349.048467 | 377.184083 | 27.613642 |
| 02/O1/s24 | 51.599155 | 46.956740 | 52.083949 | 4.642415 |
| 03/O3/s128 | 53.868687 | 51.914761 | 54.371650 | 1.953926 |

该秒级差异不能由 float 量化解释。`clock_probe.json` 五项 RAW/MONO 比值范围 `1.0910094508–1.0910097533`，显示计时关系需要诊断，不能据此认定 NTP/WSL 的具体根因，也不能用比值换算修正成绩。建议保留旧日志另列异常，正式比较建立新的统一 MONOTONIC 目标/构建/批次。CLOCK_MONOTONIC 不受墙钟离散跳变，仍受频率调整，统一时基不代表绝对时钟准确性已证明。[Linux clock_gettime 文档](https://man7.org/linux/man-pages/man2/clock_gettime.2.html)、[Python time.monotonic 文档](https://docs.python.org/3/library/time.html#time.monotonic)。

主控释放短编译/测试窗口后，审核者完整读取新 C（61 行）、格式规范化的精确 diff、同源生成器（161 行），并复核：

- 新 C SHA `cece4fd572c1d25e9f9a7d045c21e8d77b25079a6f71513de0385d0d85d44835`；第 44–50 行内核与原件按行尾空白规范化后完全相同；rand/default input/double/n4096 不变。第 42/52 行 CLOCK_MONOTONIC 位于原起止边界，两次错误均非零退出。tdiff 仍返回 float，纳秒差系数为 1e-9，第一行仍 `%0.6f`，checksum 仍在计时后。
- 生成器 SHA `189128c2c7e13db73c1dc516401c72a0eb053cacce74ae0db70ebd72dfc21a36`；第 13–18 行分别识别原件 gettimeofday 与适配件 clock_gettime 的结束边界，要求只出现一种边界类型；第 78–100 行先替换源程序唯一 return0，再插入含自身 return0 的参考函数，最终再比较完整内核。保留了此前 marker 失败的两个 header-only 原始文件，未将其计为正确性运行成功。
- 独立新建临时验证源并编译 128/129×四 O，五 s×seed2026/610×三输入共 240 项全元素比较，全部通过；最大绝对/相对误差仍为 `4.720183e-14`/`4.735401e-11`。每项同时检查 C kernel 时间不超 Python monotonic 的进程区间加 1e-5 舍入容差，全部通过（最大 kernel−process 为 `−0.0018693050s`，process 区间同时包含参考检查）。另独立 ASan/UBSan n129/O1/seed2026/符号输入全部五 s 通过。
- 新目标 `gcc -std=c11 -Wall -Wextra -O3 -S` exit 0、无告警；实际两次 clock_gettime 在汇编第 149/276 行，调用参数为 CLOCK_MONOTONIC（edi=1）；第 222–224 行乘加写 C，内外循环仍有 4096 边界回跳；checksum 在第 299–310 行。实际汇编追加至 `kernel_assembly.txt`，保留此前原版/旧适配版段落。未启动我方 n4096/full。
- 新生成 n128/n129 验证源 SHA 分别为 `0777d4d37b3ad3e33a7c75c142471a243beae41c8343870e1bd0c88f18a4db2e`、`ab4102037799962ea04c448ac885a14f7b9b013347c2bf7b01fc8d27bea4a706`。

独立短脚本最初打印“与旧目标 checksum 一致”时没有跨版本比较，该打印已明确撤回，不能作为独立 seed2026/610 的跨版本证据。随后实际对照 owner 保存的 `target_small.jsonl` 与 `target_small_monotonic.jsonl`：按 n/O/s/seed/mode 匹配的 240 项同集合、两版 source SHA 分别 e321…/cece…，checksum 字符串无差异；此结论只针对保存记录中的输入组。

目标计时适配与生成器的问题已闭环，代码允许主控进入新 n4096 抽查/预测试。框架的新候选与 clock_guard 仍待独立复核；短时 C/Python 时基一致性不能替代长 n4096 预测试，也不等于正式实验完成。

## 两个候选与时钟筛除规则独立复核

主控确认短测试窗口仍开放；同期主控 n4096 运行只用于数值抽查，不作为性能或成本样本。审核者完整读取最终框架 612 行、tests 580 行及实验 runner 334 行，不重复数值 240 套件，执行 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s P1/tests -v`：31/31，实际 unittest 时长 6.143s，exit 0。框架 SHA `0a71c2fdb0d3d41be261c9aecc86b87487990dbc3bfd4e6b34e79b7fbd75ab49`，tests SHA `ff3c73a7716fa3ee71baad096581fd27d045970fec586b12b8a20d0b587e0d9f`。

- `autotuner.py:273–281`：S1 为每个 O 独立 shuffle 五个 s，然后每轮 shuffle 四 O；完整 20 项无重复，每个前缀四 O 的次数相差不超过一，不依赖反馈改变顺序。tests 第 70–84 行对多 seed、成功/失败反馈、全部前缀进行核查。
- `autotuner.py:271–272,285–286,308–313`：S2 与同 seed Random 使用相同无放回排列；只有相对旧 best 的改善严格大于 delta 才重置 stale，任何更低的有效结果仍更新 best；失败计入尝试和 stale；同时满足 min_trials 与 patience 才停止，预算先耗尽时不额外运行。tests 第 86–116、224–272 行覆盖 0/1/20 预算、默认至少五项、阈值等值、失败、真实夹具的匹配 Random 前缀，以及部分 repeat 中断后恢复 stale/best/顺序。
- `autotuner.py:141–144,250–252`：源代码中的 comments/string/char 被剔除后识别实际 CLOCK_MONOTONIC 调用；只对该模式的合法有限输出应用 `kernel_s <= process_wall_s + 0.005s`。超出成为 clock_error，保留 stdout/kernel 原值；Evaluator 第 423–426 行只允许全部 repeats 的 status=ok 得分。tests 第 274–315 行实际构建 20ms MONOTONIC 小 C，并以明确 test-only mock 核查过大时间的记录/排除；注释和字符串不误触发。
- `autotuner.py:563–572`：min_trials、patience、delta 与实际 runtime_affinity 进入 journal fingerprint；affinity 仅作为运行设置，不改变编译缓存 identity。tests 第 558–576 行实际核查参数/seed 更改和 mock affinity 更改均拒绝 resume。恢复继续依据原始 completed trial 反馈重建搜索，复用已完成 repeat，不复用其他搜索的评分。
- cache 错误传播、SIGTERM 清理、build 独立入口 live-group 拒绝、编译失败/超时预算、未知 hard-exit 成本和真实矩阵的可观察结果等已有修复回归均继续通过。两候选只扩展现有策略分支，没有额外类层级、框架或复合候选。

当前无阻断主控新预测试的框架问题；审核者已停止编译/tests并通知主控可以上测量锁。以下事项在正式冻结前仍应关闭，不能因 31 项测试通过而省略：

| 位置与版本 | 严重性 | 证据/影响 | 后续处理 |
| --- | --- | --- | --- |
| `P1/scripts/experiment.py:114–139`，SHA `15c26276abd1a825bb4c00bb500cca4eceb3faecfba5b918bb2d8787b68c1433` | 高（正式接纳日志） | task_status 对已存在 summary 校 source/protocol、action/repeats/seed、algorithm/budget，却不校 min_trials/patience/delta、runtime_affinity、timeout/compiler/完整 space。其他 CLI 命令可携带同协议文件但不同设置生成已完成 journal；runner 直接认 complete 后跳过执行，不能依靠 CLI 的 resume fingerprint 防止此种误接纳。此项依据静态分支审查，尚未构造正式目录或执行目标复现。 | 已报主控；正式批准前按 frozen 设置核对 header。runner 第 152–154 行已正确传递冻结的候选参数，protocol 的 delta 仍为空时禁止 execute，不能以 CLI 默认 0 替代。 |
| `protocol_v1.json measurement.clock_health` 与 `autotuner.py:251` | 低（规则记录） | draft runner clock tolerance 为 0.01s，而 framework 实际筛除为 0.005s；正式记录若仍写 0.01s，将漏述 framework 的更严格判断。 | 在预测试结束后协议冻结时统一为实际执行规则。不要求放宽 framework guard。 |

读取时协议 SHA `03d07f464c8de4f03e8c8ce01fa74d1ee4cbcc384ec53c0a4eb6404bf08cd638`，state=draft，审批、阈值、资源上限、预热、compiler identity 与长预测试基准均未冻结；该状态真实记录为待审核，未称正式批准或 Goal1/Engineering 完成。

## 正式比较前代码关口：静态检查与待修复项

本工作包首先执行 `ls -la`；根目录仍为 A1/A2/P1、课程输入材料、AGENTS 和 P1 提示，审核限定 P1。主控再次授权锁 OFF 的短测试窗口，但实验 owner 尚在修改中，动态测试等待稳定 SHA 交接；未自行启动 n4096。

重新完整读取 production C、原 C、validate_target.py、实际生成的 verify_4096.c，源码 SHA 仍分别为 cece…、188d…、1891…；六层 kernel 未改，生成源仍在结束计时、完整 checksum 后才运行长 double 朴素参考。读取 `target_full_monotonic.jsonl`：主控 n4096/O0/s24 和 O3/s128 各 24 个边缘/确定随机位置检查均 exit 0、failures=0，最大绝对误差 `2.937539e-12`、相对误差 `2.814528e-15`。这是抽查，不是全矩阵证明；其 190.610977/40.906105 秒不计正式性能样本，同期短测试不会进入成绩。

审核者以只读 Python 重解析 9 个新预测试与 3 个噪声诊断原始 journal，并重新 hash 四个实际缓存 binary 与 manifest：所有 source、n4096、CLOCK_MONOTONIC、CPU0、原始第一行时间和有限 checksum 均对应；12 项时钟 guard 满足，目标 checksum 均为 `17180040496.458935`；12 个 journal 无 build_start。准备记录有且只有 O0/O1/O2/O3 四个目标构建，其 identity/key/binary SHA 均对应当前目标，完整 flags 仅公共选项+单项 O，identity 不含 s。该只读证据支持实际只按 O 构建，没有每 s 重编译。

读取当时实验 runner SHA `cf7f6b040810ea7ab18404402e58c6c7c96a6a3839a29be4fd5e09cc19bbee8a`（565 行）、summarizer SHA `4c73e73f7ab1ec539315496921fec365a9b62e48942bd5a8ddfb0968c3d7f2a1`（504 行）、tests SHA `c244085d9c396e5741cd4c1b29514b77248c8ff80649491a10fe6fa36d1c1bd1`（304 行），并完整读 protocol JSON/Markdown。owner 正在继续修改，因此这些 SHA 只是该次静态快照，不是最终冻结版本。

- task_status 第 171–191 行现在重建全部正式 metadata 及其 fingerprint，包括 compiler/flags/n/clock/space/timeout/cache/affinity/候选参数；已完成 summary 也不能绕过该校验。此前高优先级 metadata 漏检已补齐，待稳定版独立动态验证。
- commands 使用 argv 列表，未使用 shell=True 或 shell 字符串拼接；运行经 taskset CPU0、共同框架 CLI，只有 compile 的 O 项改变。tests 明示 temporary/synthetic，FakeTarget/mock/SYNTHETIC_NOT_EXECUTED 仅出现在 tests 且 /tmp 内，无 production mock 或测量回放混入。
- runner 每批计划保留 source/framework/driver/protocol/request SHA；资源统计跨 registered 批次，恢复只预留尚未启动的次数。hard exit 的 driver 真实 wall=null，保存已记录下界、同 boot 包含停机等待的资源上界以及至多一个未知 spawn 上界；拒绝仍活的 PID/group，不盲杀历史 PID。派生 summary 将未知 actual wall 与已知下界分别呈现。
- 参照/选择/留出/预热/冲突诊断由 role 分离；原参照三次中位数及确认分数不因冲突诊断替换。派生脚本检查原始 stdout/重复编号/中位数/best 前缀/计数/会话 wall，拒绝派生文件写入 raw 批次。收益单位是相同 t_ref 下 g 的百分点差，保留秒数 floor 与成本约束，样本端点明确不是 CI。

新发现并已通知主控和实现 owner 的必要修复：

| 位置（上述 runner 快照） | 严重性 | 证据/影响 | 状态 |
| --- | --- | --- | --- |
| `P1/scripts/experiment.py:484–490` | 高 | Popen 成功后，task_process 持久化在 wait 的 try 外；此处 OSError/KeyboardInterrupt 会退出 driver 而不清理已经启动的 framework，其真实 kernel 可以继续运行。与此前框架 on_start 问题同类。 | owner 正在补 spawn 后日志异常 cleanup 和回归；尚未运行独立动态复现。 |
| `P1/scripts/experiment.py:446–465` | 中 | partial JSON driver 尾只在 recorded_usage 时拒绝；若所有 task summary 已完成，循环全部 skip 而不调用资源统计，execute/resume 可返回 0 但留有 torn ledger/未知 driver wall。完整合法 JSON 无尾换行也需要保留该记录后先添加分隔，不能黏连。 | owner 已获通知，待稳定版无条件 ledger 校验与尾边界回归。 |

协议当前仍 draft，不能开始正式比较；目前是等待上述实现收敛及独立动态检查，不是最终批准。

## 正式比较前代码关口：修复后动态检查与结论

本关口最终源码身份：

| 文件 | SHA-256 |
| --- | --- |
| `src/autotuner.py` | `0a71c2fdb0d3d41be261c9aecc86b87487990dbc3bfd4e6b34e79b7fbd75ab49` |
| `src/matrix_multiplication.c` | `cece4fd572c1d25e9f9a7d045c21e8d77b25079a6f71513de0385d0d85d44835` |
| `scripts/validate_target.py` | `189128c2c7e13db73c1dc516401c72a0eb053cacce74ae0db70ebd72dfc21a36` |
| `scripts/experiment.py` | `9041accdee31d1fb7d822d1b43af4e090dc7c9308376c211533b3b552501a052` |
| `scripts/summarize.py` | `2630b8cead860d347b4cb67d5b04fade268969b5137f7c5462b8ed312340417c` |
| `tests/test_experiment.py` | `b6079145abf4a0bdce908c5550c02ef32a5a52a503dd8afe7d06e3bc8150ba32` |

主控给出 stable 交接后，审核者执行全量 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s P1/tests -v`：53/53、7.134s、exit 0。该次是 runner 9041…、summarizer f46f…、tests a85c… 的快照；随后实验审核者发现 ER08 的退出码/spawn/未匹配启动事件漏检，这个成绩不当作该遗漏已经关闭的证据。

ER08 只修改派生分析与实验 tests，runner/core/target 不变。owner 再交接上述最终 SHA 后，审核者重读受影响代码与回归，执行 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s P1/tests -p test_experiment.py -v`：23/23、1.491s、exit 0。不重复不变的 31 项 core 回归及已验证的矩阵 240 小例。实验夹具均只在临时目录，用明确 synthetic/mock 数据，不进入性能目录。

必要修复已经关闭：

- `experiment.py:171–198`：完整 frozen metadata/fingerprint 校验；完成日志也拒绝不同 compiler、flags、space、cache、affinity、timeout、repeat/seed/budget 或候选参数。实验测试实际篡改完成日志且同步其自有 fingerprint，仍被正式设置比较拒绝。
- `experiment.py:329–334,506–522`：Popen 后的 PID 持久化与 wait 进入同一 try；日志异常清理并 wait 真实 child 后传播原异常，不伪造正常 completion。除 owner mock 回归外，审核者把临时 driver 的 command 替换为真实 Python sleep 子进程，并在 task_process 写入时注入明确 test-only OSError：实际 returncode=-15、PID 不存在、ledger 仅 task_start。自建 child 均已回收，临时目录已清理。
- `experiment.py:462–469`：合法完整 JSON 缺少末尾换行时先补分隔并保留记录；partial JSON 尾不自动追加。进入循环 skip completed task 前无条件检查资源 ledger，故全部完成的 framework summary 也不能掩盖 torn driver cost。回归分别保留完整 end 行及其已知成本、拒绝损坏尾且保持原 bytes。
- `autotuner.py:323–349`：额外独立边界检查使用真实小 C fixture r=3，在第二次运行前中断，将临时 journal 截到第一个完整 measurement JSON 并去掉尾 newline。恢复只新运行剩余两次，总目标进程 3、repeat 编号 `[0,1,2]`、原 repeat0 对象逐字段不变、所有 JSON 行可读；旧未结束 session 的 tuning wall 仍为 null。该夹具只检验恢复语义，不是矩阵性能数据。
- `summarize.py:44–48,56–83,119–125`：valid sample 明确要求 returncode=0、spawned=true；唯一 trial/repeat/start/completion 相互匹配，有完成 summary 时不得遗留未完成 start，真实 process count 按启动事件重新求取。第 362–393 行新回归对 rc7、spawned=false 并篡改 summary count、未匹配/丢失/重复 start 和伪完整 summary 均拒绝，合法 partial journal 保留为 partial。
- `summarize.py task_driver_walls/run_tables`：成本接受使用完整 driver 各 attempt 实际 wall 的累加加共同返回确认，保留内部框架窗口单列；hard recovery 的实际 driver wall 不以内部窗口或资源上界回填。完整成本求和、未知成本、clone 派生表一致性、预算恰够剩余过程、预热排除、冲突次数上限与等值阈值等实验回归均通过。

两次额外短真实复核合计 exec wall 0.087s，exit 0；没有我方 n4096 运行，没有遗留测试 child，没有修改实现、正式 raw、系统时钟、依赖或 Git 发布状态。

自然性/规模复读：production C 保留老师代码结构，只作必要参数检查、可观察结果与已诊断计时兼容适配；三接口、统一 Evaluator 与 append-only Journal 对应明确任务要求。实验脚本保持普通函数和标准库，有限恢复、资源限制、冲突诊断各有实际用途；未添加泛用平台、数据库、层级继承、联合候选或未来作业内容。派生绘图按 raw 生成，统计脚本没有用 grid 分数回填在线曲线。

**代码关口：批准。** 上述冻结源码的原计算、缓存复用、候选预算/反馈、错误清理、恢复记录及派生分析已完成实际验证，未见阻断进入正式实验的未关闭代码问题。独立实验/设计关口仍由另一审核者给出；主控必须等两关口均批准后设置协议 state/approval 并记录最终协议哈希，才启动正式数据。审核者现在停止编译/tests，测量期间仅读；结果完成后仍须按最终文件和实际数据再次终审。此结论不是 Goal1 完成、不是性能改善结论，也不是最终 Engineering PASS。

此处读取的协议 JSON SHA `e071a1459c11f45e59705f7a60ef2fdff7f3b7b087d102e485e5a691e068d7ae`、MD SHA `905b81446f57cf7e4fbf8708911e6bcd636823a8c5f33fdf78a4bb239b6857a3`；JSON 的批准字段尚待主控设置，最终协议哈希会随这项已授权操作更新，不应把旧 draft hash 称为最终冻结 hash。
