# A1 2026 当前正式 requirement matrix

最终依据：A1 DOCX 全部题目 + 老师最新补充“MIT 正式仅 Write-up 2～8”。PDF 只用于七项 Write-up；ZIP 只作为 starter code，不增加任务。

PASS 需有本轮真实证据。GDB、断言和内存定位作为 W5–W8 的过程证据，不单列独立正式任务。先前做过的 preprocessing、coverage 等证据保留，但不计入本表或正式报告要求，也不继续完善。

| ID | 老师要求 / 检查项 | 状态 | README 位置 | 当前 Evidence |
|---|---|---|---|---|
| ENV-OS | DOCX 环境：Ubuntu 20.04 LTS 及以上 | PASS | §1 | [environment_versions.txt](final/environment_versions.txt) |
| ENV-KERNEL | Kernel >=5.4 | PASS | §1 | [environment_versions.txt](final/environment_versions.txt) |
| ENV-GCC | GCC >=9.3 | PASS | §1 | [environment_versions.txt](final/environment_versions.txt) |
| ENV-CLANG | Clang >=10 | PASS | §1 | [environment_versions.txt](final/environment_versions.txt) |
| ENV-PYTHON | Python >=3.8 | PASS | §1 | [environment_versions.txt](final/environment_versions.txt) |
| ENV-JAVA | Java / javac >=11 | PASS | §1 | [environment_versions.txt](final/environment_versions.txt) |
| ENV-VALGRIND | Valgrind >=3.17 | PASS | §1 | [environment_versions.txt](final/environment_versions.txt) |
| ENV-PERF | perf >=5.4，版本与软件事件实测 | PASS | §1 | [environment_versions.txt](final/environment_versions.txt) |
| ENV-OPENCILK | OpenCilk >=1.0 且实际编译/runtime smoke test | PASS | §1 | [opencilk_validation.txt](environment_2026/opencilk_validation.txt) |
| CMD-UNAME | (1)a–b 全部字段、kernel release、ISA | PASS | §2 / (1) | [uname.txt](linux_commands_2026/uname.txt) |
| CMD-OS-RELEASE | (2) 本次发行版字段 | PASS | §2 / (2) | [os_release.txt](linux_commands_2026/os_release.txt) |
| CMD-SYSCTL | (3)a 功能、-a、真实列表 | PASS | §2 / (3) | [sysctl.txt](linux_commands_2026/sysctl.txt) |
| CMD-SYSCTL-MAPPING | (3)b–c /proc/sys 映射、kernel 与 distro 区分 | PASS | §2 / (3) | [proc_mapping.txt](linux_commands_2026/proc_mapping.txt) |
| CMD-SYSCTL-PARAMS | (3)d 实际存在的两个 perf 参数及手册 | PASS | §2 / (3) | [manuals.txt](linux_commands_2026/manuals.txt) |
| CMD-LSCPU | (4)a 型号、guest 核/线程及各级缓存 | PASS | §2 / (4) | [lscpu.txt](linux_commands_2026/lscpu.txt) |
| CMD-ENDIAN | (4)b 当前大小端与相反字节序应用 | PASS | §2 / (4) | [lscpu.txt](linux_commands_2026/lscpu.txt) |
| CMD-ADDRESS | (4)c physical/virtual 宽度与 64-bit ISA 区别 | PASS | §2 / (4) | [lscpu.txt](linux_commands_2026/lscpu.txt) |
| CMD-NUMACTL-H | (6)a–c -H、节点数、distance 及应用 | PASS | §2 / (6) | [numactl_H.txt](linux_commands_2026/numactl_H.txt) |
| CMD-NUMACTL-SHOW | (6)d --show 作用、每个输出字段、与 -H 区别 | PASS | §2 / (6) | [numactl_show.txt](linux_commands_2026/numactl_show.txt) |
| CMD-FREE | (7)a Mem/Swap 行与主要列 | PASS | §2 / (7) | [free.txt](linux_commands_2026/free.txt) |
| CMD-GIB-GB | (7)b GiB 与 GB 及 -h | PASS | §2 / (7) | [free.txt](linux_commands_2026/free.txt) |
| CMD-PS | (8) ps -aux 实际表头全部列 | PASS | §2 / (8) | [ps.txt](linux_commands_2026/ps.txt) |
| CMD-TOP | (9)a 交互运行、摘要/列含义、q 退出 | PASS | §2 / (9) | [top.raw.txt](linux_commands_2026/top.raw.txt) |
| CMD-HTOP | (9)b htop 交互运行、比较、q 退出 | PASS | §2 / (9) | [htop.raw.txt](linux_commands_2026/htop.raw.txt) |
| CMD-VMSTAT | (10) vmstat 1 实际采样、Ctrl+C、首份口径 | PASS | §2 / (10) | [vmstat.raw.txt](linux_commands_2026/vmstat.raw.txt) |
| CMD-MPSTAT | (11) mpstat -P ALL 1、interval、各 CPU | PASS | §2 / (11) | [mpstat.raw.txt](linux_commands_2026/mpstat.raw.txt) |
| CMD-PIDSTAT | (12) pidstat 1、interval、活动进程统计 | PASS | §2 / (12) | [pidstat.raw.txt](linux_commands_2026/pidstat.raw.txt) |
| CMD-IOSTAT | (13) iostat -xz 1、interval、扩展设备统计 | PASS | §2 / (13) | [iostat.raw.txt](linux_commands_2026/iostat.raw.txt) |
| CMD-CPU-COMPARE | (10–13) ps/pidstat/top/htop 对比及负载清理 | PASS | §2 / (13) | [cpu_comparison.txt](linux_commands_2026/cpu_comparison.txt) |
| CMD-SAR | (14)a–b 1 秒、-n DEV 当前全部列 | PASS | §2 / (14) | [sar.raw.txt](linux_commands_2026/sar.raw.txt) |
| CMD-UPTIME | (15)a–b 字段、1/5/15 分钟 load、R/D 含义 | PASS | §2 / (15) | [uptime.txt](linux_commands_2026/uptime.txt) |
| CMD-INTERRUPTS | (16)a–b 真实硬中断/核间中断，最高项与有限解释 | PASS | §2 / (16) | [interrupts_2.txt](linux_commands_2026/interrupts_2.txt) |
| CMD-SOFTIRQS | (16)a–b 两次快照、逐 CPU 求和和增量 | PASS | §2 / (16) | [irq_summary.txt](linux_commands_2026/irq_summary.txt) |
| CMD-LSTOPO | (17) SVG 生成、有效性与当前拓扑分析 | PASS | §2 / (17) | [lstopo.txt](linux_commands_2026/lstopo.txt) |
| CMD-MAN | 题面要求：查阅当前系统手册 | PASS | §2 | [manuals.txt](linux_commands_2026/manuals.txt) |
| CMD-DMIDECODE | (5)a–b 命令执行和字段问题已回答；具体 DIMM 信息 UNVERIFIED due WSL | PASS | §2 / (5) | [dmidecode.txt](linux_commands_2026/dmidecode.txt) |
| HW-FREQUENCY | (4)a 频率问题已回答；具体 base/max/min UNVERIFIED due WSL | PASS | §2 / (4) | [proc_mapping.txt](linux_commands_2026/proc_mapping.txt) |
| HW-HOST-TOPOLOGY | (4)a guest 核/线程已回答；宿主物理布局 UNVERIFIED due WSL | PASS | §2 / (4) | [lscpu.txt](linux_commands_2026/lscpu.txt) |
| GIT-CONFIG | (18)1 检查全局、仅 local identity | PASS | §2 / (18) | [git_transcript.txt](git_exercise_2026/git_transcript.txt) |
| GIT-INIT | (18)2 实测初始分支及两种改名说明 | PASS | §2 / (18) | [git_transcript.txt](git_exercise_2026/git_transcript.txt) |
| GIT-COMMIT | (18)3 空暂存区失败与正常成功提交 | PASS | §2 / (18) | [git_transcript.txt](git_exercise_2026/git_transcript.txt) |
| GIT-IGNORE | (18)4 提交图片→ignore→rm --cached→文件保留 | PASS | §2 / (18) | [git_transcript.txt](git_exercise_2026/git_transcript.txt) |
| GIT-CONVENTIONAL | (18)5 阅读指定官方链接并简述 | PASS | §2 / (18) | [EXTERNAL_REFERENCES.md](environment_2026/EXTERNAL_REFERENCES.md) |
| GIT-MERGE-REBASE | (18)6 历史结构、适用场景、共享历史风险 | PASS | §2 / (18) | [git_transcript.txt](git_exercise_2026/git_transcript.txt) |
| W2 | pointer baseline 六处 const 错误、问题逐项回答、注释后运行 | PASS | §3 / Write-up 2 | [c_primer_fixed.txt](mit6172_2026/c_primer_fixed.txt) |
| W3 | 全部指定类型及指针大小，数组/结构体取地址 | PASS | §3 / Write-up 3 | [c_primer_fixed.txt](mit6172_2026/c_primer_fixed.txt) |
| W4 | swap baseline 与指针修复、完整代码、verifier 通过 | PASS | §3 / Write-up 4 | [c_primer_fixed.txt](mit6172_2026/c_primer_fixed.txt) |
| W5 | 本轮 ZIP O1→O3、clean/make 输出、baseline SIGSEGV | PASS | §3 / Write-up 5 | [writeup5_baseline.txt](mit6172_2026/writeup5_baseline.txt) |
| W6 | 当前阶段 ASan 实际泄漏输出，使用系统 Clang 18 runtime | PASS | §3 / Write-up 6 | [writeup6_asan_system.txt](mit6172_2026/writeup6_asan_system.txt) |
| W7 | 实际正确矩阵输出、独立普通与零矩阵核对 | PASS | §3 / Write-up 7 | [matrix_correctness_final.txt](mit6172_2026/matrix_correctness_final.txt) |
| W8 | 先观察泄漏，再 free A/B/C、严格 Valgrind 全部 clean | PASS | §3 / Write-up 8 | [post_coverage_final.txt](mit6172_2026/post_coverage_final.txt) |
| README | 全部正式解答汇入当前 Markdown，环境限制明确披露 | PASS | 全文 | [README.md](../README.md) |
| LINKS | README 相对链接有效、SVG XML/引用有效 | PASS | 全文 | [A1_2026_FINAL_VALIDATION.md](final/A1_2026_FINAL_VALIDATION.md) |
| SCOPE | 仅 A1；GitHub main 发布获授权，水杉与后续作业未开始 | PASS | 全文 | [A1_2026_FINAL_VALIDATION.md](final/A1_2026_FINAL_VALIDATION.md) |
| STUDENT-INFO | 报告标题、真实学号 10245102410、姓名 吴博闻 | PASS | 报告开头 | [README.md](../README.md) |
| REPORT-ORDER | 系统信息仅 OS/CPU/Memory；DOCX 顺序；MIT 仅 W2–8 | PASS | 全文 | [README.md](../README.md) |
| REPORT-SCREENSHOTS | 当前真实终端截图，与文本证据和最终代码对应 | PASS | 全文 | [截图目录](../images/) |

PASS: 57; PARTIAL: 0; BLOCKED: 0; NOT_REQUIRED: 0; UNVERIFIED: 0.

## 具体硬件事实的限制

以上状态表示题目操作与回答是否完成，不表示取得了所有宿主硬件事实。

- DMI：已执行命令，guest 缺少 /dev/mem 和 DMI 表；DIMM 信息 UNVERIFIED。
- 频率：已读取 lscpu 并检查 cpufreq；base/min/max 具体数值 UNVERIFIED。
- 宿主拓扑：11 core / 22 PU 为 guest 实测；Windows 宿主物理核与 P/E 布局 UNVERIFIED。
- PMU：软件事件可用；硬件 cycles/instructions 不支持，不阻塞当前作业。

这些环境限制均已在 README 对应问题回答。OpenCilk 则已完成真实安装和 compile/run 验证。

Section 6、W9、W10、MIT Git、AWSRUN 未执行，不列为正式 requirement。DOCX 第 (18) 项 Git 已独立完成。
