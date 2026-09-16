# 2026 正式题面与旧 A1 差异清单

依据：本轮 DOCX（范围）、Getting Started PDF（MIT 题目）、代码 ZIP（starter）。
本清单在重新实验前建立，已按老师最终范围修订更新；标记描述相对旧 A1 的处理方式，不代表验证已通过。

| 当前题面要求 | 分类 | 本轮处理 |
|---|---|---|
| Ubuntu 20.04 LTS / Kernel 5.4+ | NEEDS_RECHECK | 实测发行版、内核；替换旧环境文档阈值 |
| GCC 9.3+、Clang 10+ | NEEDS_RECHECK | 版本检查与实际编译 |
| Python 3.8+、Java 11+ | NEEDS_RECHECK | python3、java、javac |
| Valgrind 3.17+、perf 5.4+ | NEEDS_RECHECK | 版本及当前内存检查；不沿用旧 PASS |
| OpenCilk 1.0+ | NEW | 检查、必要时独立安装、编译运行 smoke test |
| (1) uname：字段、kernel、ISA | NEEDS_RECHECK | 当前输出及解释 |
| (2) /etc/os-release：发行版字段 | NEW | 当前输出，与 kernel 区分 |
| (3)a–b sysctl：功能、-a、/proc/sys | NEEDS_RECHECK | 完整列表、路径映射 |
| (3)c–d kernel 对比、两个 perf/sched 参数 | NEW | 从真实列表选取，查手册 |
| (4)a CPU 型号、核、线程 | NEEDS_RECHECK | 仅报告 guest-visible topology |
| (4)a base/max/min、L1d/L1i/L2/L3 | NEW | 缺失频率明确 UNVERIFIED，缓存说明汇总口径 |
| (4)b–c 大小端场景、物理/虚拟地址宽度 | NEW | 结合当前 lscpu |
| (5) dmidecode 功能、内存字段 | NEEDS_RECHECK | 保留真实失败，理论字段和实测分开 |
| (6)a–b numactl -H、节点数 | NEEDS_RECHECK | 重新执行 |
| (6)c–d distances、应用、--show | NEW | 逐项解释当前策略与硬件查询区别 |
| (7)a free -h 两行和列 | NEEDS_RECHECK | 重新执行 |
| (7)b GiB / GB | NEW | 二进制/十进制及 -h 单位 |
| (8) ps -aux | NEW | 当前列头、每列含义 |
| (9)a top | NEEDS_RECHECK | 实际 PTY 交互、q 退出 |
| (9)b htop、比较 | NEW | 缺工具则安装，实际 PTY 交互 |
| (10)–(13) vmstat/mpstat/pidstat/iostat | NEEDS_RECHECK | 原命令采样、Ctrl+C，查各自 man |
| (10)–(13) CPU utilization 对比 | NEW | 可控短时工作负载，保存 PID、窗口及退出证据 |
| (14) sar -n DEV 1 | NEEDS_RECHECK | 当前字段与间隔解释 |
| (15) uptime、load average | NEW | 实测，说明 1/5/15 分钟、R/D 任务 |
| (16) interrupts / softirqs | NEW | 两次快照、计数求和、增量、限制 |
| (17) lstopo topo.svg | NEW | 实际生成、验证 SVG、对照 console 分析 |
| (18)1 identity | NEW | 检查 global，仅 demo local 配置 |
| (18)2 init / branch | NEW | 实测默认分支，说明两种修改命令 |
| (18)3 commit | NEW | 隔离仓库先失败后成功 |
| (18)4 图片 / ignore / rm --cached | NEW | 提交测试图、取消跟踪、验证仍存在 |
| (18)5 Conventional Commits | NEW | 阅读指定官方链接，简述 |
| (18)6 merge / rebase | NEW | 概述历史结构与共享历史风险 |
| MIT 非 Write-up 独立 Exercise | SUPERSEDED | 最终正式仅 W2–8；已产生证据保留，不作为独立要求 |
| W2 pointer | NEEDS_RECHECK | 当前 ZIP 编译失败，再注释非法赋值并运行 |
| W3 sizes / pointers | NEEDS_RECHECK | 全部类型，数组与结构体取地址，真实输出 |
| W4 pointer swap / verifier | NEEDS_RECHECK | baseline 按值不交换，再修复；Python 3 最小兼容 |
| W5 O3 编译及 baseline crash | NEEDS_RECHECK | 当前 ZIP 新建干净 baseline，重新构建执行 |
| GDB、断言、维度修复 | NEEDS_RECHECK | 原始 crash → debug → assertion → 4×4 |
| W6 ASan | NEEDS_RECHECK | 维度修复后真实报告 |
| W7 初始化 / 正确矩阵 | NEEDS_RECHECK | Valgrind 定位，calloc，普通与 zero 核对 |
| W8 内存释放 | NEEDS_RECHECK | 先观测 leak，再 free A/B/C，严格 Valgrind |
| Coverage Exercise | SUPERSEDED | 修订前已真实执行并撤销；现仅保留历史证据，不继续完善 |
| 旧代码思路、check_matrix.py、工具安装 | REUSE | 与本次 starter 对照后只复用相符部分 |
| 旧题面 README / requirement matrix | SUPERSEDED | 重做当前 2026 版本，旧证据仍保留 |
| 旧 CPUinfo 独立问题、旧环境标准 | SUPERSEDED | 不作为当前正式要求；必要诊断不当作额外作业 |
| MIT Section 6 / W9–10 / AWSRUN / Git | SUPERSEDED | 当前明确不做；独立 (18) Git 必须做 |
| Markdown 所有答案、相对链接、拓扑图 | NEEDS_RECHECK | 更新 README、链接与 SVG 验证 |

限制：仅本地工程。课程主仓库不 commit/push，不提交，不开始 A2–A5/P1–P3。

最终报告新增要求：学号 10245102410、姓名 吴博闻；系统信息仅 OS/CPU/Memory；正文逐题及子问题；真实终端截图统一 A1/images/。系统已安装 htop/hwloc/llvm-18/compiler-rt，最终 ASan 使用系统 runtime。
