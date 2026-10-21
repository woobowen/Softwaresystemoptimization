# 原始采样与构建对应

仓库根为 `/home/addaswsw/lab/Software_system_optimization`。

- Checkoff 1：`make -C P2/recitation isort DEBUG=1`，`-Wall -O0 -g`，原 isort.c 未改。采样：`/usr/lib/linux-tools-6.8.0-147/perf record -e cpu-clock:u -F 999 -o .cache/P2/checkoff1-probe.data -- P2/recitation/isort 10000 10`。之后原文件移到 `.cache/P2/profiles/checkoff1/perf.data`，匹配 isort、源码和 Makefile 同目录。227 samples，lost=0。导出 report --stdio --no-children 和 annotate --stdio -l --source --symbol=isort 保存在 `checkoff1/`。
- Checkoff 2 首次原配置：`make sum` 实际 `-Wall -O1 -DNDEBUG`，Cachegrind 明确 cache-sim=yes、branch-sim=yes。原始文件 `.cache/P2/profiles/sum-original/cachegrind.out`，匹配 sum、sum.c、Makefile 同目录。初始无-g不能给源码行号，日志/导出另保留。
- Checkoff 2 统一控制变量批次：`scripts/sum_controls.py` 生成原始源码两处常量替换、统一 `-Wall -O1 -DNDEBUG -g`，原设置也重跑。原始 cg、源码、匹配二进制全部保存在 `.cache/P2/sum-controls/`；每个 case 命令、各 SHA、实际模拟配置在 `checkoff2/provenance.json`。
- W1：`.cache/P2/builds/writeup1-debug-sort` 和 `writeup1-release-sort`；同一套修正后驱动，只注册到当时已完成的 a/i/p，选择单独 sort_a。同一源码快照 `.cache/P2/profiles/writeup1/source/`。原始 cg 在 `.cache/P2/profiles/writeup1/`；原 flags 与执行输出在 `../commands/writeup1-*-build.txt` 和 `writeup1/`。后续六版本统计不替代 W1 这组严格成对数据。

所有正常耗时目录 `metadata.json` 都绑定二进制 SHA，并保留 warmup、逐次命令/输出、单次排序和每进程平均数。分析工具中的耗时不用于正常加速比。

## 最终六版本与递归对照

- 最终正常构建和正式 all-versions 样本的匹配二进制：`.cache/P2/builds/final-release-sort`，完整 homework 源码快照 `.cache/P2/profiles/final/source/`。恢复 sanitizer 后使用 cmp 确认重新生成的二进制逐字相同。
- 每个版本 Cachegrind 原件 `.cache/P2/profiles/final/sort_{a,i,p,c,m,f}.cg`，统一 N32768/R1/seed42/random；导出为 `versions/*-cachegrind*.txt`，汇总 `cache-summary.csv` 与 `cache-summary.txt`。全进程计数包含初始化、生成、正确性检查和库调用，源码/函数明细另看 annotate。
- 最终 Perf：`taskset -c 2 /usr/lib/linux-tools-6.8.0-147/perf record -e cpu-clock:u -F 999 --call-graph dwarf,8192 -o .cache/P2/profiles/perf-versions/<version>.data -- .cache/P2/builds/final-release-sort -b -s 42 -v <version> -t random 1048576 20`。版本 a/i/p/m/f 串行执行；采集日志、Self 平表、调用栈表和 i/p/m/f annotate 均在 `perf-versions/`。平表由 report --stdio --no-children --call-graph none 导出，不把递归 Children 累计当 Self。
- W3 诊断仅把 `static inline void sort_recursive_i` 改为 `static __attribute__((noinline)) void sort_recursive_i`，其余排序代码不变，diff 在 `writeup3/noinline.diff`。源码 `.cache/P2/variants/sort_i_noinline.c`，二进制 `.cache/P2/builds/recursive-noinline-sort`，CG 原件 `.cache/P2/profiles/final/recursive-noinline.cg`。正常耗时按同一协议另测，release qsort 用例先通过。objcopy 导出的两个完整 .text SHA 相等，因此正常耗时小差异不能归因为递归内联。
- 分配次数使用 `../review/count-allocations.c` 的链接时 malloc/free 包装单独测得，计数窗口仅排序入口，不用于计时。N1048576、threshold32，m 的 malloc/free 各32767，f 各1；与完全二叉分解的结构推导一致。harness 的数据生成和最终 free 不计入。

最终 `artifact-index.json` 将绑定所有本地二进制、源快照和原始采样的 SHA-256；审核包不带这些二进制，但保留对应可读导出及准确重建命令。

原地构建路径在清理后可能不存在，计时批次的匹配保留路径另见 `../performance/binary-resolution.json`。最早inline批次经保存源快照重建后完整二进制SHA与原记录一致，恢复方法和命令在 `../debug/fixes.md` 与 `../commands/inline-binary-reconstruction.txt`；94项本地构建/源/采样哈希现已统一索引。所有原始计时未被替换。

`.cache/P2/` 中二进制、原始 Perf/Cachegrind、原始下载是本地材料，不进入 Git/老师提交/审核 ZIP；审核 ZIP 提供可读导出、命令、哈希及复现脚本。不会删除本地唯一原始证据。
