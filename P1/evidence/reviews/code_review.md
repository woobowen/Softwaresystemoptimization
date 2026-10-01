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
