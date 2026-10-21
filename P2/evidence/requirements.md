# P2 要求与证据对应表

老师 DOCX 正文为 2026-10-21 布置、2026-11-18 24:00 截止（Asia/Shanghai）；页眉旧学年不覆盖正文。原题见 MIT 2018 HW2。当前用户明确把原选做 W2/W3/W7 纳入必须完成范围。Exercise 不提交，AWS/Git 教学不做；本地交付不涉及任何发布。

| 要求 | 老师属性 | 本次结果 | 正式位置 | 主要内部证据 |
|---|---|---|---|---|
| lscpu | 补充必做 | 完整输出和截图已保留 | `../lscpu.txt`、README 系统概况 | `environment/`、`../images/01-lscpu.png` |
| Checkoff Item 1 | 必做，增加最热源码行/指令/解释 | 原 isort DEBUG=1，10000/10；软件事件227样本，Self热点isort，行20归属63%，对应11ea等指令；解释和限制齐全 | README Checkoff Item 1 | `commands/checkoff1-build.txt`、`profiling/checkoff1/{report,annotate,opcodes}.txt`、`environment/perf-*-check.txt` |
| Checkoff Item 2 | 必做 | 原 U=10000000/N=100000000 已完整运行；固定N的三工作集和固定U的三个N（共享原配置），全局/逐行统计与实际模拟几何齐全 | README Checkoff Item 2 | `commands/sum-original.*.txt`、`profiling/checkoff2/`、`../scripts/sum_controls.py` |
| Write-up 1 | 必做 | 同修正驱动、同sort_a，O0/DEBUG与O3/NDEBUG成对重建；CG与正常时间分开，讨论指令数优缺点 | README Write-up 1 | `commands/writeup1-*-build.txt`、`profiling/writeup1/`、`performance/writeup1-{debug,release}/` |
| Write-up 2 | 原选做，本次必做 | sort_i，copy/merge真实内联；util候选已审查并保留共同外部函数；汇编核实原版O3已有自动内联，无稳定加速 | README Write-up 2 | `profiling/versions/inline-remarks.txt`、`*-assembly.txt`、`perf-versions/sort_i-*`、`performance/inline/`及`all-versions/` |
| Write-up 3 | 原选做，本次必做 | static inline递归尝试被实际Clang拒绝展开；noinline对照同.text，检查体积/调用/CG/正常时间，不虚构负面效果 | README Write-up 3 | `profiling/writeup3/`、`performance/recursive-noinline/` |
| Write-up 4 | 必做 | sort_p指针复制/归并，分配策略相同；汇编及CG/正常耗时比较，保留退化 | README Write-up 4 | `../homework/sort_p.c`、`profiling/versions/sort_recursive_p-assembly.txt`、`perf-versions/sort_p-*`、`performance/pre-coarsening/` |
| Write-up 5 | 必做 | 从预定综合指标测得最快a出发；安全插入排序，8/16/32/64有限比较选32，说明选择不具有通用最优性 | README Write-up 5 | `performance/thresholds/`、`commands/threshold-*-{build,correctness}.txt`、`../homework/{sort_c.c,isort.c,coarsen.h}` |
| Write-up 6 | 必做 | sort_m左缓冲/原地右侧，解释覆盖不变量及编译器问题、O(n)空间、奇数和子数组等检查 | README Write-up 6 | `../homework/sort_m.c`、`correctness/`、`profiling/cache-summary.*`、`review/check-extremes.c` |
| Write-up 7 | 原选做，本次必做 | sort_f入口分配/结束释放、static递归传递；实际分配计数及Perf/CG支持有限收益 | README Write-up 7 | `../homework/sort_f.c`、`profiling/versions/allocation-counts.txt`、`review/count-allocations.c`、`profiling/perf-versions/sort_{m,f}-*` |

## 横向要求

- 六版本外部签名一致，内部 static 保留，递归归并结构保留，无多线程、其他完整排序替换、LTO 或 march=native。sort_a/util.c 与官方逐字一致。
- 驱动计时、seed、失败状态与测试缺口修正见 `debug/fixes.md` 和 `debug/starter-changes.patch`。
- 六版共同有效域 qsort 对照共1656例：23长度×2偏移×6模式×6版本。Release、ASan/UBSan、Memcheck均执行；m/f另有78例完整uint32域。
- Release 受控错误算法虽输出有序仍被 qsort 检查捕获，退出1，见 `correctness/failure-propagation.txt`。这是负向诊断，不是正式算法的失败。
- 正式10个计时批次共245个独立进程、490个按输入区分的均值、2450条单次排序耗时；另49个预热进程不入统计。全部原始样本/构建对应保留在 `performance/`。
- 所有 Perf/CG/内存工具与正常计时分开，原始采样/匹配二进制保留在本地 `.cache/P2/`，哈希索引 `profiling/artifact-index.json`；可读导出全部进入审核包。
- 正式截图为实际 xterm/Xvfb/ffmpeg 捕获，命令与SHA在 `commands/screenshots.jsonl`。受控错误算法已从正式内存检查截图移除，旧图仅存本地缓存。
- 未新增其他作业，根AGENTS及已有A1/A2/P1未改，初始未跟踪文件保留。未 commit/push，未切换分支，未访问水杉远端。
- 原生独立技术和文档审查记录在 `review/`；这不是外部ChatGPT验收或Engineering PASS。最终本地文件/审核包检查见 `final/`。
