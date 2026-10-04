# Matrix Multiplication Autotuner

这个 Autotuner 为老师提供的矩阵乘法程序选择循环分块大小和 GCC 优化级别。C 程序负责计算，Python 调优器负责提出配置、编译、运行和比较耗时；默认配置空间包含五种分块大小与四种优化级别，共 20 个组合。

项目实现了 Grid Search、Random Search 和 Greedy Search。可以完整查看每个组合的性能，也可以给定测量预算，让搜索算法返回已尝试配置中耗时最小的一项。框架设计、正确性检查、完整配置实验和算法比较见 [report.md](report.md)。

## 项目结构

```text
report.md                         设计说明与实验分析
src/
  autotuner.py                    Python 调优器
  matrix_multiplication.c          可供调优器调用的目标程序
  matrix_multiplication.original.c 老师提供的原始程序
images/                           报告使用的框架图、结果图和终端截图
results/                          保存的实验结果与统计表
```

原始程序保留作对照；普通运行使用 `matrix_multiplication.c`，两者的初始化与六层乘法循环相同。运行时产生的可执行文件与示例日志放在 `.cache/`，查看已有结果可直接使用文末的入口。

## 环境与依赖

实际使用的环境是 Ubuntu 24.04.2 LTS / WSL2，CPU 为 Intel Core Ultra 9 185H，GCC 13.3.0，Python 3.12.3。Python 部分只使用标准库，无需安装 pip 包；编译 C 程序需要 GCC。

目标程序默认计算 `n=4096` 的串行 `double` 矩阵乘法。一次运行包含矩阵初始化和完整乘法，因此 `run` 与 `search` 都会执行真实的大矩阵计算。只想了解配置和实验结果时，可以先使用 `list` 或阅读已有统计表。

## 快速开始

在包含 `src/`、`images/` 和 `report.md` 的目录中执行。以下命令使用不同的日志路径，便于分别查看构建、单配置运行和三种搜索的结果。

### 查看配置空间

`list` 列出全部配置，不编译、不运行矩阵。输出中的 `s` 是分块大小，`opt` 是优化级别；第二条命令演示怎样缩小输入的候选集合。

```bash
python3 -B src/autotuner.py list
python3 -B src/autotuner.py list --blocks 8,24 --opts O1,O3
```

### 编译

`build` 分别准备 O0—O3 四个可执行文件。同一优化级别可供不同分块大小复用；输出中的 `cached` 表示这次是否使用了已有构建。

```bash
python3 -B src/autotuner.py build --output .cache/demo-build.jsonl
```

### 运行一个配置

`run` 指定一个配置，下面运行 `s=128/O3`。成功运行后查看返回结果的 `best.score` 可找到乘法内核耗时，原始目标输出保存在日志中。

```bash
python3 -B src/autotuner.py run --s 128 --opt O3 \
  --repeats 1 --timeout 1200 --output .cache/demo-run.jsonl
```

### Grid Search

Grid 按分块大小在外、优化级别在内的顺序逐项访问。默认空间有 20 项，预算设为 20 时可完整遍历；预算较小时只测枚举顺序的前缀。

```bash
python3 -B src/autotuner.py search --algorithm grid \
  --budget 20 --repeats 1 --timeout 1200 --output .cache/demo-grid.jsonl
```

### Random Search

Random 根据 seed 打乱全部配置，再无放回访问。八次预算只覆盖部分空间，结果需结合实际访问的配置理解；相同 seed 决定相同访问顺序，但不会固定每次运行的耗时。

```bash
python3 -B src/autotuner.py search --algorithm random \
  --budget 8 --seed 700001 --repeats 1 --timeout 1200 \
  --output .cache/demo-random.jsonl
```

### Greedy Search

Greedy 从 seed 决定的起点检查单参数相邻配置，收齐当前点的邻居结果后向更快者移动，无改善时停止。查看 `stop_reason` 可以区分预算耗尽与局部停止。

```bash
python3 -B src/autotuner.py search --algorithm greedy \
  --budget 8 --seed 700001 --repeats 1 --timeout 1200 \
  --output .cache/demo-greedy.jsonl
```

## 主要参数

| 参数 | 用途 |
| --- | --- |
| `--target` | 输入 C 源码；默认是 `src/matrix_multiplication.c`。 |
| `--blocks` | 逗号分隔的分块候选值，默认 `8,16,24,64,128`。 |
| `--opts` | 逗号分隔的优化级别，默认 `O0,O1,O2,O3`。 |
| `--algorithm` | 选择搜索规则；上述三种取值为 `grid`、`random`、`greedy`，默认 `grid`。 |
| `--budget` | 最多进行多少次配置评估，包含失败的尝试。 |
| `--seed` | 控制 Random 的访问顺序和 Greedy 的默认起点。 |
| `--repeats` | 每次配置评估的重复次数；全部有效时按内核耗时中位数评分。 |
| `--timeout` | 每次目标进程允许的最长等待时间，单位秒。 |
| `--output` | 保存 JSONL 日志的路径；每次新运行使用新文件。 |

`--budget 8 --repeats 1` 最多启动八次目标计算；若将 `--repeats` 改为 3，最多可能启动 24 次，某次失败也可能使该项提前结束。`run` 的 `--s` 和 `--opt` 必须属于输入的候选空间。要更换目标程序，其可执行文件需接受一个分块参数，首行输出以秒为单位的正有限耗时；框架不会自动识别其他程序的参数和计算区间。

比较性能时还需保持运行条件一致。报告中的实验固定在 WSL2 逻辑 CPU 0；可在同样的命令前加 `taskset -c 0`，其他环境应选择实际可用的逻辑 CPU。固定亲和性仍不能消除系统负载造成的波动。

## 输出怎么看

搜索结束后打印的 JSON 中，`best.config` 是返回配置，`best.score` 是搜索期间对该配置取得的内核耗时估计。内核计时只包围乘法循环，不含初始化和计时后的 checksum；checksum 用来消费计算结果，不是逐元素正确性的证明。

`tuning_raw_s` 是调优器内部记录的搜索耗时，包含目标进程、构建检查和调优器开销；报告中的搜索总耗时从命令外部测量，还包括 Python 进程启动和退出，二者的起止范围不同。它们都回答“调优花了多久”，不能当作返回配置执行一次乘法的时间。`attempted_trials` 和 `stop_reason` 帮助判断测了多少项、为何停止，失败的运行不会被选成最快配置。

日志保存每次调用的配置、目标输出、耗时和失败信息，可回看搜索为何返回某项，而不用仅凭最后一个数字判断。已有日志不会被覆盖；再次运行示例时更换 `--output` 文件名。

## 实验结果入口

- [完整报告](report.md)：三个接口、矩阵程序适配、20 配置分析及搜索方法比较。
- [配置统计表](results/goal2r_summary/grid_summary.csv)：每个配置的三个样本、中位数、范围与离散程度。
- [搜索统计表](results/goal2r_summary/search_summary.csv)：返回配置、在线估计、真实调用数与搜索总耗时。

统计表保留了本项目已经完成的实验。想理解性能差异时先读报告；想检查某个数值时再回到对应表格。
