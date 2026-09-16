> Historical checkpoint before FINALIZE-PUBLISH. Its PARTIAL status and NO COMMIT/PUSH rule have been superseded; see final/A1_2026_FINAL_VALIDATION.md.

# A1-2026-OFFICIAL-001 RESULT

## 1. Engineering Status

PARTIAL。报告、DOCX 命令练习和 MIT Write-up 2–8 已完成并验证；OpenCilk 官方包三种传输尝试均失败，无法验证版本或编译运行。DMI 与宿主频率/物理拓扑的实测限制如实披露。

## 2. Source Materials Used

A1 初试环境和工具.docx：主任务清单。A1 Getting Started.pdf：仅 W2–8。A1 代码材料.zip：七项 Write-up 的 starter，无额外任务。源文件 SHA256 见 [source_hashes.txt](environment_2026/source_hashes.txt)。补充资料仅为本机手册、题面指定 Conventional Commits、OpenCilk 官方安装说明和 Ubuntu 包源。

## 3. 2026 Delta from Previous A1

新增/补全当前 DOCX 子问题、OpenCilk 检查、隔离 Git、真实拓扑图及中断统计。当前 ZIP baseline→修复链重新实测；复用相符源码和正确性检查器。旧报告结构及 MIT 独立额外 Exercise 范围被最新要求替代；历史证据均保留。[逐项差异](A1_2026_DELTA.md)。

## 4. Environment

| 项目 | 当前实际值 |
|---|---|
| OS | Ubuntu 24.04.2 LTS / WSL2 |
| Kernel | 6.18.33.2-microsoft-standard-WSL2 |
| GCC | 13.3.0 |
| Clang | 18.1.3 |
| Python | 3.12.3 |
| Java / javac | 21.0.12 |
| Valgrind | 3.22.0 |
| perf | 6.8.12 |
| OpenCilk | BLOCKED：未安装 |

OpenCilk actual verification：UNVERIFIED；系统 Clang 不支持 -fopencilk，不能替代 OpenCilk。官方归档未下载完整，未执行安装或 smoke test。[失败证据](environment_2026/opencilk_status.txt)。

## 5. System Command Exercise

| 命令 | 状态 | 本轮证据 |
|---|---|---|
| uname | PASS | [uname.txt](linux_commands_2026/uname.txt) |
| os-release | PASS | [os_release.txt](linux_commands_2026/os_release.txt) |
| sysctl | PASS | [sysctl.txt](linux_commands_2026/sysctl.txt) |
| lscpu | PASS（可见字段；未暴露字段另列） | [lscpu.txt](linux_commands_2026/lscpu.txt) |
| dmidecode | PARTIAL | [dmidecode.txt](linux_commands_2026/dmidecode.txt) |
| numactl -H | PASS | [numactl_H.txt](linux_commands_2026/numactl_H.txt) |
| numactl --show | PASS | [numactl_show.txt](linux_commands_2026/numactl_show.txt) |
| free -h | PASS | [free.txt](linux_commands_2026/free.txt) |
| ps -aux | PASS | [ps.txt](linux_commands_2026/ps.txt) |
| top | PASS | [top.raw.txt](linux_commands_2026/top.raw.txt) |
| htop | PASS | [htop.raw.txt](linux_commands_2026/htop.raw.txt) |
| vmstat | PASS | [vmstat.raw.txt](linux_commands_2026/vmstat.raw.txt) |
| mpstat | PASS | [mpstat.raw.txt](linux_commands_2026/mpstat.raw.txt) |
| pidstat | PASS | [pidstat.raw.txt](linux_commands_2026/pidstat.raw.txt) |
| iostat | PASS | [iostat.raw.txt](linux_commands_2026/iostat.raw.txt) |
| sar | PASS | [sar.raw.txt](linux_commands_2026/sar.raw.txt) |
| uptime | PASS | [当前截图输出](report_2026/05-ps-uptime.terminal.txt) |
| /proc/interrupts | PASS | [interrupts_2.txt](linux_commands_2026/interrupts_2.txt) |
| /proc/softirqs | PASS | [softirqs_2.txt](linux_commands_2026/softirqs_2.txt) |
| lstopo | PASS | [lstopo.txt](linux_commands_2026/lstopo.txt)、[topo.svg](../images/topo.svg) |

## 6. WSL / Hardware Limitations

真实可见：22 logical CPU、11 guest core、2 thread/core、1 NUMA node；guest cache；约 15.42 GiB 内存；46/48 位 physical/virtual 地址。

UNVERIFIED：base/min/max frequency、Windows 宿主物理核与 P/E 布局。DMI 接口缺失，未取得宿主 DIMM 信息。perf 软件事件可用，cycles/instructions 不受支持。

中断可读：CAL 累计/窗口增量最高；数字设备 IRQ 累计最高为 IRQ 25 virtio0-virtqueues，窗口增量为 0；Hyper-V HVS 单独说明；软中断 SCHED 最高。这些只代表 WSL guest，不能认定为 Windows 物理设备最频繁 IRQ。

## 7. Git Exercise

Demo repo path：/tmp/a1-git-exercise.ktyqj3et；无 remote。

- user.name/email config：读取 global，demo local 设置 woobowen / woobowen@gmail.com。
- git init branch：master；README 分别给出默认分支与当前分支改名命令。
- first commit behavior：空暂存区 exit 1。
- successful commit：59483d2。
- image commit：fba7a39。
- .gitignore / git rm --cached：提交 56395cf，图片保留，最终只跟踪 .gitignore 与 hello.txt。
- Conventional Commits：已阅读官方 Summary 并回答。
- merge vs rebase：已解释历史结构、ID 改变及使用场景。

[完整过程](git_exercise_2026/git_transcript.txt)。课程主仓库 NO COMMIT / NO PUSH。

## 8. MIT Starter Material

本次 ZIP：c-primer 6 个源码/构建文件；matrix-multiply 6 个源码/构建文件。提取时排除 __MACOSX / .DS_Store。与旧 A1 干净 starter 对比的 12 个文件全部 IDENTICAL，但本轮重新构建了可追溯实验链。最终源码与原已有修复一致，没有人为制造修改。[清单](mit6172_2026/starter_inventory.txt)、[对比](mit6172_2026/starter_vs_previous_source.txt)。

## 9. MIT 6.172 Scope

正式仅 Write-up 2–8，七项 PASS。Section 6 / W9 / W10：NOT_STARTED；MIT Git / AWSRUN：NOT_EXECUTED。GDB、断言与内存检查用于取得 W5–8 的真实结果。此前 preprocessing/coverage 等只保留历史证据，不列正式 requirement，也未继续完善。

## 10. Code Changes

下列均是本次 starter 到最终代码的修改，不表示本轮相对课程 HEAD 都有新增 diff。

| A1/mit6172/ 下路径 | 目的 |
|---|---|
| c-primer/pointer.c | 注释六处非法 const 赋值 |
| c-primer/sizes.c | 输出所需类型及指针大小 |
| c-primer/swap.c | 指针参数交换，main 传地址 |
| c-primer/verifier.py | Python 3 最小兼容，保留预期值与规则 |
| matrix-multiply/Makefile | release O3；调试模式正常切换；最终无 coverage instrumentation |
| matrix-multiply/matrix_multiply.c | calloc 初始化行数据 |
| matrix-multiply/testbed.c | 维度统一 4×4，退出前释放 A/B/C |

[当前 starter 到最终源码的 patch](mit6172_2026/final_from_2026_starter.patch)。

## 11. Build / Run / Debug Evidence

| 实际命令 / 阶段 | 结果 |
|---|---|
| baseline make pointer | exit 2，六条 const 错误 |
| 修复后 make / pointer / sizes / swap / verifier.py | exit 0，swap 为 2/1，LGTM |
| O3 make clean / make | exit 0；原矩阵程序 SIGSEGV，returncode -11 |
| gdb -nx -q -batch | 定位 i=0,j=0,k=4；A 4×5 / B、C 4×4 |
| make ASAN=1，系统 runtime | build 0；LeakSanitizer exit 1，224 bytes / 12 allocations |
| Valgrind track-origins | 定位 C 累加前未初始化 |
| 最终 make clean / make | exit 0，O3，4×4 |
| 最终严格 Valgrind，普通及 zero | exit 0，0 errors，0 bytes in use at exit |
| python3 -B A1/scripts/check_matrix.py | 6/6 PASS |

Coverage：修订前历史记录已保留，最终 Makefile 已恢复，不作为正式要求。最终 [Valgrind 截图对应全文](report_2026/writeup8-valgrind.terminal.txt)、[zero 再检查](mit6172_2026/final_zero_recheck.txt)、[系统 ASan](mit6172_2026/writeup6_asan_system.txt)、[runtime 归属](environment_2026/asan_runtime_resolution.txt)。

## 12. README

Path：[A1/README.md](../README.md)。全部 DOCX 题目及子问题均有对应答案；OpenCilk 缺项和无法实测的硬件事实未伪装成完成。MIT 正式仅 W2–8。21 张本轮真实 PNG 和 topo.svg；Markdown 82 个链接检查 PASS，SVG 校验 PASS。学号 10245102410，姓名 吴博闻。

## 13. Requirement Matrix

Path：[A1_REQUIREMENT_MATRIX.md](A1_REQUIREMENT_MATRIX.md)。

PASS 53；PARTIAL 1；BLOCKED 1；NOT_REQUIRED 0；UNVERIFIED 2。

非 PASS：OpenCilk BLOCKED；dmidecode PARTIAL；CPU base/min/max frequency UNVERIFIED；宿主物理拓扑 UNVERIFIED。环境限制已经逐题说明。[48/48 最终一致性检查](environment_2026/final_selfcheck.txt)不代表整体作业 PASS。

## 14. Files Created / Modified

正式材料：A1/README.md、A1/images/、A1/assets/topo.svg；完整源码继续位于 A1/mit6172/。

内部材料：A1/evidence/ 下 2026 各目录、matrix、delta、本 RESULT；修改 A1/scripts/check_environment.sh 与 .gitignore。旧 evidence 全部保留。AGENTS.md 当前未跟踪，系用户提供的仓库规则，不是本任务新增交付。

## 15. External References Used

- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/#summary)：DOCX 明确指定阅读，未扩展范围。
- [OpenCilk 官方安装](https://www.opencilk.org/doc/users-guide/install/)与[入门说明](https://www.opencilk.org/doc/users-guide/getting-started/)：确认官方包及最小 compile/run 用法，因 DOCX 未提供安装细节；未扩展范围。
- 本机 man、Ubuntu 发行包：解释列及补足缺失工具，未扩展范围。

[完整来源记录](environment_2026/EXTERNAL_REFERENCES.md)。

## 16. Git Status

branch：main。working tree：保留本轮未提交变更和输入材料。HEAD 始终为 2d0289aa392abfa1bfac062f60e8a030ea3f9c9f。

NO COURSE-REPO COMMIT。NO COURSE-REPO PUSH。

## 17. Known Limitations

OpenCilk 三种下载方法失败（HTTP/2、TLS、传输不完整），未安装、未完成 smoke test。DMI、CPU 频率、宿主拓扑与 PMU 限制如第 6 节。无性能加速结论；4×4 用例计时过小，不用于性能论证。

## 18. Out-of-Scope Confirmation

A2 / A3 / A4 / A5 / P1 / P2 / P3：全部 NOT_STARTED。

MIT Section 6：NOT_STARTED；Write-up 9：NOT_STARTED；Write-up 10：NOT_STARTED；MIT Git：NOT_EXECUTED；AWSRUN：NOT_EXECUTED。

## 19. Reviewer Notes

1. OpenCilk 真实缺失，不能以系统 Clang 或成功 HEAD 请求替代 smoke test。
2. lscpu 只描述 guest，频率及宿主物理核未猜测。
3. interrupts/softirqs 可读，区分 CAL、HVS、数字 IRQ 与宿主设备。
4. topo.svg 有效，11 guest cores / 22 PUs 与 console 一致。
5. Git commit 均仅在无 remote 的隔离 demo，课程 HEAD 不变。
6. 当前 ZIP 的 12 个 starter 文件比对、阶段 patch 与最终源码哈希可查。
7. W5 baseline→GDB→维度修复→ASan→初始化/释放完整链可查。
8. 最终普通及 zero Valgrind clean；独立矩阵核对 6/6。
9. matrix 只覆盖 DOCX + W2–8；报告顺序、身份、图片与链接均已核对。
10. 旧临时 runtime/workaround 证据保留，最终已换成系统 runtime。

安装记录：用户本轮安装 htop、hwloc、llvm-18、libclang-rt-18-dev 及依赖，共 20 个新增系统包；无 pip/npm/cargo 安装，无 shell rc、系统默认编译器、全局 Git identity、apt 源或 kernel 修改。仅增加本地 .gitignore 规则并保留历史 A1/.tools/ubuntu 与 /tmp 下载片段。[安装日志](environment_2026/INSTALLATION_LOG.md)。默认保留，不自动清理。

## Teacher Clarification Compliance

A1 DOCX complete: NO（OpenCilk 未完成；DMI 实测受限）

MIT formal scope: WRITE-UP 2–8 ONLY

Extra MIT exercises treated as formal requirements: NO

MIT Section 6: NOT_STARTED

Write-up 9: NOT_STARTED

Write-up 10: NOT_STARTED

MIT Git: NOT_EXECUTED

AWSRUN: NOT_EXECUTED

A1 DOCX Git exercise: PASS

## Environment Compatibility

Used actual current environment: YES

Downgraded system to match teacher sample: NO

Environment difference documented: YES

System info in README limited to: OS / CPU / Memory

OpenCilk: 未安装，version UNVERIFIED；actual compile/run smoke test BLOCKED。

## Report Compliance

Assignment name: PRESENT

Student ID: PRESENT（10245102410）

Student name: PRESENT（吴博闻）

Follows teacher question order: YES

Code/result screenshots: COMPLETE

Screenshot links: PASS

Obvious AI/template wording review: PASS

## Course Repository

NO COMMIT

NO PUSH
