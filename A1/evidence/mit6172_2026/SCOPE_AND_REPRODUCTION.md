# 最终范围修订

正式 MIT 仅 Write-up 2–8。下文是修订前已执行步骤的历史记录，不是额外正式 requirement。coverage/preprocess/Section 7 不再继续完善。最终 ASan 见 writeup6_asan_system.txt，已直接使用用户安装的系统 Clang 18 runtime；本地解包方案仅保留历史证据。

# 当前材料范围与复现

1. `official_pdf.txt` 是本轮 18 页 PDF 的提取文本。Section 1 后直接到 4，未提供 2/3。不从网络补做缺失章节。
2. Section 1 软件工程建议已阅读；Section 4 preprocess、sizes、pointer、swap 均真实练习；Section 5 从 baseline、O3、GDB、断言、维度、内存检查到 coverage；Section 7 阅读风格建议。ZIP 不含 clint.py，PDF 仅建议使用，因此没有补找可选 linter。
3. Section 6、1000×1000、循环交换、W9/W10、AWSRUN 与 MIT Git 指令未执行。DOCX 第 (18) 项独立 Git 练习已在 /tmp 隔离仓库执行。
4. `starter_inventory.txt` 列出当前 ZIP 12 个有效源码的 SHA256。`starter_vs_previous_source.txt` 逐文件比较旧 starter，全部 IDENTICAL。`starter_vs_existing.patch` 比较当前 starter 与本轮开始时课程代码。
5. 本轮从干净当前 starter 在临时工作目录真实逐步修复；最终源码恰好与旧最终实现一致，因而没有人为制造源码 diff。`final_from_2026_starter.patch` 是相对当前 ZIP 的最终全部更改。
6. 顺序证据：`c_primer_baseline.txt` → `c_primer_fixed.txt`；`matrix_O1_baseline_build.txt` → `writeup5_baseline.txt` → `gdb_release.txt` → `gdb_debug_plain.txt` → `gdb_assertions.txt` / `gdb_assertion_frame.txt` → `dimensions_fixed.txt` → `writeup6_asan.txt` → `valgrind_uninitialized.txt` → `initialized_before_free.txt` → `final_work_build.txt`。
7. ASan 因 runtime 缺失延后到保存的“维度修复但未初始化/未释放”副本运行；该副本路径见 `asan_stage_path.txt`。这不是在已经修好泄漏的最终程序上伪造错误。runtime 由 Ubuntu libclang-rt-18-dev 解包，链接显式指定 resource-dir。
8. GDB 第一次加载了用户美化插件，后续加 `-nx` 获得干净文本，不修改用户配置。局部源码路径/帧号以本次 backtrace 为准。
9. `check_matrix.py` 复用前已检查：按三个打印块解析 A/B/C、独立计算点积，检查 4×4 与 zero；无需修改。
10. 最终源码只包含题目要求：const 注释、尺寸打印、指针 swap、Python 3 verifier 兼容、O3、恢复断言、4×4、calloc、free_matrix。无 loop interchange，无性能结论。
