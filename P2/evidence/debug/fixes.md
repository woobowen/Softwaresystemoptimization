# 驱动与调试修正

## 归档时的历史构建路径检查

最终检查最初直接读取各metadata.json的binary路径，因正式源码目录已经make clean而得到FileNotFoundError。该字段记录的是当时执行路径，不保证后续原地重建/清理后仍存在，不能拿当前同名程序代替旧构建验证。

按原记录的整个二进制SHA查找，最终六版、阈值、W1及noinline构建均有匹配缓存；粗化前批次与W1 release完全相同。最早a/i批次原二进制已被下一阶段覆盖。利用保留的W1源码快照，仅恢复当时sort_p官方stub及未启用的函数表行，采用当时flags、原debug compilation directory重新构建，得到的**完整二进制SHA**与原metadata的 `7b6eaca3379fe858b36738ce2a8393cf46852a21f3137a62024ab01cf89f4371` 完全相同。

这不是用新实验代替旧结果；所有时间样本保持不变。重建件和恢复源码保存在 `.cache/P2/builds/inline-sort-recovered` 与 `.cache/P2/recovered-inline-source/`，并用该件做了单版本qsort复现。准确命令/一致SHA见 `../commands/inline-binary-reconstruction.txt`。新增 `../performance/binary-resolution.json` 将10个批次关联到内容完全匹配的保留路径，最终校验不再依赖易被重建覆盖的原路径。原始Perf对应的二进制始终单独保存，没有受到此问题影响。

## 官方 starter（已逐项从源码复核）

- Clang 18 实际报 `unknown argument: -always-inline`：删除遗留参数，正常优化仍为 O3，保留 g/gdwarf-3。
- tests.c 的 sum_time 跨输入类型累积：改 double，并在每个 gen 开始清零。每次排序 TIME 和每进程 AVG 都保留，脚本复算均值。
- main.c 的 srand 与 tests.c 的 rand_r 状态不连通：set_test_seed 接到原 randomSeed；默认与正式 seed42。小规模打印输入已核对跨进程相同、换 seed 不同、试次间不重置。
- TEST_FAIL 只打印：维护 test_failures，main 根据实际失败返回非零。Release 下检查不依赖 assert。
- 重复 sort_a 表项删除，逐步注册各实现；-v/-t/-b 为原驱动轻量选择，-b 只跳过额外边界用例，不移走排序所需分配。
- 原 zero 测试实际排序单元素，且边界判断用 &&：改为空区间 [0,-1] 及 ||，one 测试同时检查中间值。
- 新增少量长度、模式、偏移的 qsort 全数组对照，覆盖排列保留及区间外不变；启用原 subarray 测试。
- `make run` 实际规模修正为文字所示 2^17 附近；stat 显式开启缓存模拟。clean 之前已读规则，证据保存在源码构建目录之外。

## 实现中发现的问题

第一次生成 sort_i 时把字符串 `_a` 全局替换为 `_i`，误将 `mem_alloc` 变成 `mem_illoc`，Clang 拒绝编译。日志 `inline-first-build.txt` 保留。后续 shell 未立即停止，运行的是原先仅注册 sort_a 的旧二进制；测量脚本在 sort_i 预热时报 unknown version 并停止，没有形成正式样本。该未完成批次移至本目录 `inline-build-failed/`，不参与结果。修复名称，后续所有依赖构建的命令采用 fail-fast；重新构建、运行正确性后从新目录重新测量。

## 数据域与原样分析对象

sort_a 使用 UINT_MAX 哨兵，在该值同时作为真实输入时存在耗尽后越界风险。保持原算法基线，全部版本共同对照使用原 [0,2^31) 输入域。不要把基线此限制当作优化新缺陷。粗化用边界安全插入排序；recitation/isort.c 保留老师指定的原始分析对象（其中形成 left-1 指针的问题不移入正式排序实现）。

## Checkoff 2 的源码关联

首次严格 `make sum` 的默认 O1/DNDEBUG 构建没有 `-g`，已完成原 U/N 全量运行，原输出完整保留，但 cg_annotate 显示 main 为 `???`，不能给逐行分析。为补足源码关联，控制变量批次统一使用相同 O1/DNDEBUG 再加 `-g`；原设置也重新完整运行，表格来自该统一批次。只加入调试信息，不把第一次无行号的采样与新二进制混用。所有生成源码、原始 cg 和匹配二进制保留在 `.cache/P2/sum-controls/`，源码由 `scripts/sum_controls.py` 的两处常量替换完整复现。
