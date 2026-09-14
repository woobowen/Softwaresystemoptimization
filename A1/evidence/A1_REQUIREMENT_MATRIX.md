# A1 requirement matrix

Task: A1-FULL-001。依据当前两份老师 PDF；环境冲突以新版环境文档为准。

PASS 表示题目要求的操作与回答已完成，不表示受限硬件信息已成功取得。dmidecode 的真实失败与接口缺失、sysctl 部分受保护参数、PID namespace、PMU 限制均在 README 披露。

| ID | 老师要求 | 状态 | README位置 | Evidence |
|---|---|---|---|---|
| ENV | 新版环境要求及快速复查 | PASS | §1 | [environment_final_check.txt](final/environment_final_check.txt) |
| UNAME | uname -a 输出组成、kernel 与 ISA | PASS | §2.1 | [uname_a.txt](linux_commands/uname_a.txt) |
| SYSCTL | sysctl -a、参数与 /proc/sys 对应 | PASS | §2.2 | [proc_sys_mapping.txt](linux_commands/proc_sys_mapping.txt) |
| TOP | 实际交互运行、q 退出及字段解释 | PASS | §2.3 | [top.txt](linux_commands/top.txt) |
| DMIDECODE | 实际执行并说明内存观察及 DMI 缺失 | PASS | §2.4 | [dmidecode.txt](linux_commands/dmidecode.txt) |
| NUMACTL | numactl -H、用途与节点数量 | PASS | §2.5 | [numactl_H.txt](linux_commands/numactl_H.txt) |
| LSCPU | 型号、guest 核数/线程、拓扑限制 | PASS | §2.6 | [lscpu.txt](linux_commands/lscpu.txt) |
| CPUINFO | 实际读取并与 lscpu 比较 | PASS | §2.6 | [cpuinfo.txt](linux_commands/cpuinfo.txt) |
| FREE | 两行含义、各列及默认 KiB 单位 | PASS | §2.7 | [free.txt](linux_commands/free.txt) |
| VMSTAT | vmstat 1、Ctrl+C、首份与后续区间 | PASS | §3 | [vmstat.txt](linux_commands/vmstat.txt) |
| MPSTAT | mpstat -P ALL 1、Ctrl+C、CPU 统计 | PASS | §3 | [mpstat.txt](linux_commands/mpstat.txt) |
| PIDSTAT | pidstat 1、Ctrl+C、活动任务筛选 | PASS | §3 | [pidstat.txt](linux_commands/pidstat.txt) |
| IOSTAT | iostat -xz 1、Ctrl+C、扩展/无活动筛选 | PASS | §3 | [iostat.txt](linux_commands/iostat.txt) |
| SAR | sar -n DEV 1、间隔与网络指标 | PASS | §4 | [sar_network.txt](linux_commands/sar_network.txt) |
| MAN | 查阅所有指定工具的本机 man 文档 | PASS | §2–4 | [man_vmstat.txt](linux_commands/man_vmstat.txt) |
| MIT-SOURCE | 使用官方 Fall 2018 HW1 PDF 与 starter ZIP | PASS | §5 引言 | [download_source.txt](mit6172/download_source.txt) |
| MIT-S1 | 阅读第 1 节软件工程建议 | PASS | §5 引言 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-S2 | 公开 PDF 未提供第 2 节正文，不猜测补做 | NOT_REQUIRED | §5 引言 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-S3 | 公开 PDF 未提供第 3 节正文，不猜测补做 | NOT_REQUIRED | §5 引言 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-S4 | 第 4 节预处理、类型、指针、参数传递 | PASS | Write-up 2–4 | [c_primer_validation.txt](mit6172/c_primer_validation.txt) |
| MIT-S5 | 第 5 节构建、GDB、断言、内存及覆盖率 | PASS | Write-up 5–8 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-S6 | 整个第 6 节跳过 | NOT_REQUIRED | §5 引言 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-S7 | 阅读第 7 节风格建议并沿用 starter 结构 | PASS | §5 引言 | [final_from_official.patch](mit6172/final_from_official.patch) |
| MIT-LINT | clint.py 官方明确建议但不强制 | NOT_REQUIRED | 不作为提交项 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-AWS | 忽略 AWSRUN | NOT_REQUIRED | §5 引言 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-GIT | 忽略 Git；无 clone/commit/push | NOT_REQUIRED | §5 引言 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-W9-W10 | 属于跳过的第 6 节，不完成 Write-up 9/10 | NOT_REQUIRED | §5 引言 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-EXERCISES | 必要 Exercise 实际练习，完整答案不作为正式提交 | PASS | §5 各 Write-up 的支撑结果 | [SCOPE_CHECKLIST.md](mit6172/SCOPE_CHECKLIST.md) |
| MIT-COVERAGE | 第 5 节 gcov 实际执行并撤销插桩 | PASS | §6 注明已撤销；细节仅内部 | [coverage_run.txt](mit6172/coverage_run.txt) |
| W2 | const/指针问题及修复后运行 | PASS | Write-up 2 | [writeup2_evidence.txt](mit6172/writeup2_evidence.txt) |
| W3 | 全部指定类型及指针大小输出 | PASS | Write-up 3 | [writeup3_evidence.txt](mit6172/writeup3_evidence.txt) |
| W4 | 指针 swap、修改代码及官方 verifier | PASS | Write-up 4 | [c_primer_validation.txt](mit6172/c_primer_validation.txt) |
| W5 | O3 clean/rebuild 真实输出 | PASS | Write-up 5 | [writeup5_evidence.txt](mit6172/writeup5_evidence.txt) |
| W6 | 实际 ASan/LeakSanitizer 输出 | PASS | Write-up 6 | [writeup6_evidence.txt](mit6172/writeup6_evidence.txt) |
| W7 | 初始化修复后的正确矩阵输出 | PASS | Write-up 7 | [writeup7_evidence.txt](mit6172/writeup7_evidence.txt) |
| W8 | 释放后 Valgrind 无错误、无泄漏 | PASS | Write-up 8 | [writeup8_evidence.txt](mit6172/writeup8_evidence.txt) |
| CODE-CHECK | 代码编译运行、独立数学核对和重复性 | PASS | Write-up 4、7、8 | [matrix_correctness.txt](mit6172/matrix_correctness.txt) |
| README | 正式 A1/README.md 包含全部指定答案 | PASS | 全文 | [README.md](../README.md) |
| LINKS | README 相对链接真实存在 | PASS | 全文 | [submission_validation.txt](final/submission_validation.txt) |
| SCOPE | 没有开始 A2–A5 或 P1–P3，无远程提交 | PASS | §5–6 | [SELF_CHECK.md](final/SELF_CHECK.md) |

PASS: 33; PARTIAL: 0; BLOCKED: 0; NOT_REQUIRED: 7.
