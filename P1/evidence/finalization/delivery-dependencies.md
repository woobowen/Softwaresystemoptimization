# Goal3 运行依赖与候选文件边界

本记录区分课堂运行与完整研究复算。`candidate-files.txt` 是 P1 目录内的候选白名单，供忽略缓存内的隔离演练；不是已通过外部验收的正式教师提交包。本阶段不访问水杉。

## 课堂运行

Linux / WSL2、Python 3 标准库、GCC 即可列出配置、构建四级优化、运行目标和使用 Grid / Random / Greedy。`taskset` 是可选的亲和性工具。源码使用 Linux 的 `CLOCK_MONOTONIC_RAW`、`resource`、进程组和 `sched_getaffinity`，没有承诺可直接在原生 Windows Python 上运行。

必要运行文件为 `src/autotuner.py`、`src/matrix_multiplication.c` 和 README。原始 C、正式报告、六图和报告引用的两个 CSV 组成文稿说明闭包，共 13 个文件。PNG 已是展示结果，不需要把绘图实现、matplotlib 或全部历史 raw 放进课堂目录。SVG 没有外部资源依赖。

`--target` 是适配 C 目标的接口：构建后程序接受单个分块参数，首行输出耗时秒数。P1 目标另外输出 checksum 及两个整数内核端点，框架按源码标识要求这些字段。不能据此声称可自动理解任意程序或证明任意目标的时钟域；源码时钟识别为 unknown 的通用适配目标不能作为 P1 正式 RAW 测量依据。

普通 CLI 的 run/search 默认 `benchmark`，不读取冻结 protocol、证据目录、Windows QPC 桥或 Git 历史。`correctness` / `diagnostic` 的运行仍记录输出和异常，但不评分；checksum 不是全量数值正确性证明。输出和构建缓存默认位于当前 P1 目录，无私人绝对路径运行依赖。日志中解析后的真实绝对路径只用于保存该次出处。

## 实际源码阅读

本次交付 owner 直接阅读了完整 `src/autotuner.py`（853 行）、当前 C（67 行）、原始 C（47 行），以及 `experiment_v2.py` 的构建身份、受控执行、恢复、轨迹校验、共享面板、冻结规则和 Goal2R 路由。源码 SHA-256 在受审基点 `c22d856b8fa2f0b37aff4f436a856cf3a74bb37a` 与本次阅读时一致：

| 文件 | SHA-256 |
| --- | --- |
| src/autotuner.py | e3a563264994f4875da955ad87ff4ce1dd0c6c180aad3da750e1ae7d5beb02ec |
| src/matrix_multiplication.c | aad89170e8d0ca80c1dbc8dc1d8d5e69bab354af86128021be163c91e5a72b50 |
| src/matrix_multiplication.original.c | 188d011109c4470e1f41829216e8677a5c2d8f2b7c8a44215652320dbdf6de15 |

- C 保留 n=4096、double、原初始化、六层乘加和尾块边界。计时是整数纳秒差再除 1e9；checksum 与整数端点打印在计时后。没有更改分块、矩阵布局或计算方案。
- ConfigSpace 明确枚举五个分块与四个优化级别；Grid 的完整顺序与八次固定前缀有区别。Random 无放回且只用自己的 seed；Greedy 的移动依据是已观察到的严格改善，邻居或预算限制不等于真实全局最优。
- 基础控制流为 suggest → evaluate → observe。Evaluator 统一构建、重复测量及失败记账，只有有效 benchmark 样本成为分数；recheck 首六项与两次候选复核分开，只有成功复核的候选可返回。
- 构建键只含源码、编译器及实际 flags，恢复指纹仍含完整运行设置与亲和性。缓存二进制读前核对 hash；源码改变会中止。日志 append 后 flush/fsync，已完成与失败调用仍占预算。
- 超时和中断清理本次拥有的进程组。恢复时未闭合调用保存 interrupted，不擅自杀身份不明的 PID。正式批次额外核对冻结身份、唯一启动/完成与完整在线轨迹；共享面板只在搜索返回锁定后创建。
- `controlled(mode="correctness")` 拒绝性能 guard；Goal2R 仅检查预定块前后的 QPC 对齐区间，旧 2% 辅助时钟守卫仍保存在对应历史分支而不作用于 Goal2R。未闭合或失败的 QPC 块不得自动续跑。

没有发现要求修改稳定生产行为的具体问题。上述是直接源码检查结论，不能替代主控的新运行、独立 reviewer 或外部工程验收。

## 完整工程复算与回归

完整工程复算需要完整仓库中匹配的源码、冻结协议、四个 Goal2R raw 目录、共享面板、QPC 保存读数、原账本快照和相应历史声明；不能从 13 文件课堂候选目录复算缺失的全部 raw。只读复算用保存的 QPC 整数计算，不启动 Windows 桥。对已有 Goal2R 汇总使用新的未存在目录：

```bash
python3 -B P1/scripts/summarize_v2.py \
  --protocol P1/evidence/protocol_goal2r.json \
  --reference P1/results/goal2r_reference \
  --runs P1/results/goal2r_comparison \
  --runs P1/results/goal2r_starts \
  --runs P1/results/goal2r_confirmation \
  --ledger P1/evidence/measurement/goal2r/final-results-resource-ledger.jsonl \
  --output-dir P1/.cache/goal3-recomputed
```

`summarize_v2.py` 的 Goal2R 分支导入 `goal2r_analysis.py`，并依赖 `experiment_v2.py`、`experiment.py`、`identity_quality.py`、`host_clock_probe.py` 等同提交脚本。`--plots` 另需 matplotlib；本次文字/布局改图使用展示层，不改冻结分析代码。无 `--plots` 时 summary 缺 images 元数据应与数值变化分别检查。

历史只读重生继续使用原对应提交：Goal1 `3ac0c4688b964c873379d012cbcf09afb7ed0937`，初始诊断 `2fc0c334039bb6696c4d83acbe029ce65ca66ab9`，追加诊断 `c247e900d3f9c4d46e4abf06092939a0a9480429`，MONOTONIC 停止 `a39f348e6cf0c7466900ec739a797753f4d93f0b`，RAW 停止 `5c78049a22fa3422f2b23dddd634f2e7a3d73f9d`。已有两侧重生记录位于 `evidence/reproduction/goal2r/`，本次不重跑历史矩阵实验。历史证据里的实际绝对路径是出处，不是课堂运行依赖。

完整回归命令为 `python3 -B -m unittest discover -s P1/tests -v`，在无构建缓存的干净导出根目录执行。测试使用小 C 夹具及保存 raw，不新增 n4096 样本；正常测试数量、失败与 skip 以本次日志为准。四项原生截图集成依赖 Xvfb、xdpyinfo、ffmpeg、ss、xterm；五项 Windows 清理集成依赖既有 WSL interop/PowerShell，代码在不可用时标 skip。

已有 xterm 是原工作区 `P1/.cache/screenshot-tools/root/usr/bin/xterm`；干净导出回归通过单次进程 PATH 复用，不修改全局配置或安装软件。`P1_HOST_CLEANUP_LOG` 可指定干净导出内的本地输出。截图测试另向干净导出自己的 `evidence/commands/goal2r_screenshot_cleanup_tests.jsonl` 追加，收集本次片段时不回写原历史文件。

## 隔离演练检查规则

主控唯一调度全部编译、测试、目标运行与截图，并保存命令、整数计时端点、退出和成本。执行结果由同目录的主控复现记录记录；本文件的源码检查不预先标记执行通过。

1. 按候选清单装配于被忽略的 `.cache/` 新目录，逐文件 SHA-256 与候选工作树对照；不带 `.git`、evidence、脚本/测试、AGENTS、提示词、PDF/ZIP 输入、缓存或其他任务。
2. 打开 report/README，验证全部本地相对引用闭包与图像存在。课堂命令只依赖包内源码，不承诺原始研究复算。
3. 冷构建 O0—O3，每项要求编译退出 0、`cached=false`。完整工程导出与最小目录各作一次完整 n4096/s128/O3，后者与最后真实终端截图复用；不进入正式性能排名。
4. 在最小目录的 `.cache/` 从同源 C 只将 n 改为 129，保留计算循环；使用原样 autotuner 对 Grid/Random/Greedy 各运行最多 20 次小矩阵，检查完整枚举、seed 顺序、邻居/停止、预算和逐条调用。此项只验证控制流，不是正式性能或新增在线算法。
5. 清单、终稿文件 hash、来源基点与实际结果分开保存。终稿 report/README、src 与演练目录必须同字节；最终外部验收后才能从通过版本准备正式教师提交。

## 主控执行后的交付读回

图文冻结后，交付 owner 重新读包内 13 文件并与当前工作树逐字比较，13 项一致，包外新增文件仅在本次生成的 `.cache/` 内。报告和 README 共 13 个本地相对引用均存在且在白名单中；三份 src 与受审基点逐字一致。[candidate-files.json](candidate-files.json) 保存每个文件的字节数、SHA-256、Git blob 和源代码基点；发布回执将清单 hash 绑定最终提交，不要求清单包含它自身的发布 SHA。

直接读取 [完整回归日志](full-regression.stderr.txt)：254 tests、12.943 秒、OK，0 skip。读取 [全工程冷构建](full-cold-build.jsonl) 与 [最小目录冷构建](minimal-cold-build.jsonl)，各有 O0—O3 四项 `cached=false`、编译退出 0、相同公共 flags，两个导出所得四级 ELF 的 hash 逐级相同。

[最小目录控制流](minimal-control-check.json) 的 n=129 同源夹具只改变 n 宏；Grid、Random 各完成 20 个不重复配置，Greedy 完成 8 个配置并停于 local_optimum，共 48 次小矩阵调用，失败 0。读回逐条启动/完成身份、真实 argv、退出、整数端点及首行解析值，并检查 Grid 枚举、seed=17 的 Random 顺序和 Greedy 终点的全部邻居；没有把小矩阵时长用于正式 n4096 结果。

两份新鲜 n4096 日志各有一个真实目标启动及唯一完成，s=128/O3、目标退出 0、无失败。全工程采用 [correctness](full-fresh-n4096.jsonl)，整数内核差 45.362831808 秒、进程 RAW 46.039513505 秒，评分为空；最小目录采用 [benchmark](minimal-fresh-n4096.jsonl)，整数内核差 33.338204624 秒、进程 RAW 33.952249174 秒，与最后真实终端截图复用。内核端点均嵌套于本进程 RAW 端点，checksum 均为 17180040496.458935；这两次用于运行可复现性，不进入原 60 样本参照或新的性能比较。新增目标数为 2，受控费用以主控闭合记录为准，不能把内核和外层费用相加。

本次交付 owner 自己未编译或启动实验，只读回主控真实执行日志与当前文件；这些读回结论仍需独立 reviewer 和外部验收。
