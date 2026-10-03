# P1 运行入口

正式报告见 [report.md](report.md)。目标为 n=4096 的串行 `double` 矩阵乘法，保留原初始化和六层分块循环；配置为 `{8,16,24,64,128}` 与 `{O0,O1,O2,O3}` 的 20 个组合。

运行需要 Linux / WSL2、Python 3 和 GCC，Python 部分只用标准库。以下命令在 **P1 目录内**执行，输出写入 `.cache/`。一次完整矩阵运行可能需要数分钟。

```bash
# 列出完整配置空间，编译四个优化级别
python3 -B src/autotuner.py list
python3 -B src/autotuner.py build --output .cache/demo-build.jsonl

# 运行一个配置
python3 -B src/autotuner.py run --s 128 --opt O3 \
  --repeats 1 --timeout 1200 --output .cache/demo-run.jsonl
```

下面三条搜索命令按需选择。Grid 完整访问 20 个组合；Random 无放回打乱配置；Greedy 从 seed 决定的起点检查单参数相邻配置，无改善时停止。Random、Greedy 的示例预算为八次尝试，每次测量一次；失败的尝试也占预算。

```bash
python3 -B src/autotuner.py search --algorithm grid \
  --budget 20 --repeats 1 --timeout 1200 --output .cache/demo-grid.jsonl
python3 -B src/autotuner.py search --algorithm random \
  --budget 8 --seed 700001 --repeats 1 --timeout 1200 \
  --output .cache/demo-random.jsonl
python3 -B src/autotuner.py search --algorithm greedy \
  --budget 8 --seed 700001 --repeats 1 --timeout 1200 \
  --output .cache/demo-greedy.jsonl
```

`--target` 输入 C 源码，`--blocks` 与 `--opts` 输入候选值，`--algorithm` 选择算法，缺省为 Grid。例如 `list --blocks 8,24 --opts O1,O3` 列出四个组合。更换目标时需适配本项目的调用约定：可执行文件接受一个分块参数，第一行输出以秒为单位的耗时；框架不会自动识别任意程序的参数和计时区域。

`run` 和 `search` 缺省使用 `benchmark`，检查输出、退出码、超时和目标计时，并将有效耗时用于评分。`run --mode correctness` 或 `--mode diagnostic` 保存运行记录但不参与排名；数值正确性的检查方法与结果见报告。内核耗时只包含乘法循环，进程与搜索总耗时还包含初始化、输出和调优开销。普通运行不需要 Windows 时钟桥或截图工具；比较性能时应保持测量条件一致，在可用的逻辑 CPU 上可用 `taskset` 固定亲和性。

日志不能覆盖已有文件。继续中断任务时，用相同源码、配置、编译器和运行设置加 `--resume --output <原日志>`；框架核对完整元数据，不会自动终止身份不明的遗留进程。更换设置或重新实验时使用新日志路径。候选复核策略 `recheck` 的结果与取舍见报告，默认算法仍为 Grid。
