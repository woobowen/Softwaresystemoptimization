# P1 运行入口

正式报告见 [report.md](report.md)。目标固定为 n=4096、double、原初始化和六层分块乘法循环，配置为五个 s 与四个 GCC 优化级别。调优器只依赖 Python 标准库；保存数据的绘图另需 matplotlib。

以下命令从仓库根目录执行。单次大矩阵运行可能需要数分钟。演示和重算输出使用新的缓存目录，不覆盖实验原始文件。

```bash
python3 -B P1/src/autotuner.py list
python3 -B P1/src/autotuner.py build --output P1/.cache/demo-build.jsonl
taskset -c 0 python3 -B P1/src/autotuner.py run --s 128 --opt O3 \
  --mode correctness --repeats 1 --timeout 1200 \
  --output P1/.cache/demo-run.jsonl
taskset -c 0 python3 -B P1/src/autotuner.py search --algorithm random \
  --budget 8 --seed 700001 --repeats 1 --timeout 1200 \
  --output P1/.cache/demo-search.jsonl
```

`--target` 输入 C 源码，`--blocks` 与 `--opts` 输入配置候选，`--algorithm` 选择搜索规则。CLI 缺省算法仍为 Grid。Random 无放回打乱配置，Greedy 检查单参数邻居；`recheck` 是与 Random 同 seed 前六项探索、两个候选各一次新复核的单项比较，不组合其他增强策略。

运行用途分为 `correctness`、`diagnostic`、`benchmark`。正确性运行保留参数、输出、退出、资源和超时检查，不因辅助时钟比值变化被中止，也不自动成为排名分数。正式内核、进程与搜索 driver 使用显式 RAW 时间字段；原 wall 字段仍表示 MONOTONIC，CPU 时间和 REALTIME 是辅助读数。当前 P1 的正式入口另外核对 RAW 源码边界、整数区间、冻结身份及实验块前后的 QPC 对齐检查。普通演示命令本身不提供这些长期测量依据。

输出日志禁止覆盖。相同源码、构建和运行设置的未停止任务可用 `--resume`；已停止的旧时钟批次、未闭合的 QPC 实验块不能借新规则续跑。不同源码或协议须建立新的批次。构建缓存只用影响产物的源码、编译器及选项作为键，恢复仍核对超时等运行设置。

## 检查与真实截图

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s P1/tests -v
python3 -B P1/scripts/validate_target.py --suite small \
  --output P1/.cache/check-small.jsonl
python3 -B P1/scripts/validate_target.py --suite sanitizer \
  --output P1/.cache/check-sanitizer.jsonl
```

小矩阵检查包括 n=128、129 的逐元素独立 long double 点积和尾块；大矩阵数值抽查的适配、预定位置及实际输出保存在[数值证据目录](evidence/measurement/goal2r/)。checksum 用于发现输出异常，不当作全量正确性的证明。

原生截图测试需要 Xvfb、xdpyinfo、ffmpeg、ss 和 xterm。现有任务缓存中的 xterm 可通过当前进程的 PATH 复用，不改全局配置。`scripts/safe_screenshots.py` 使用私有 Unix 授权和受控进程清理；Windows 桥的原生清理测试使用已有 WSL interop/PowerShell，不可用时明确跳过。已保存正式截图的命令与清理记录见证据索引。

## 保存实验与重算

[protocol_goal2r.json](evidence/protocol_goal2r.json) 固定代码与构建身份、主辅时间域、随机访问顺序、种子、真实调用预算、共同确认、接受规则和资源上限。[方法说明](evidence/measurement/goal2r_method.md) 说明旧规则为何修改，以及有限样本结论的适用范围。原 Goal 2 的 raw、协议、停止记录、原判定和费用保留，不回写为成功。

`scripts/experiment_v2.py` 是唯一新批次入口，生成计划并持有实际性能锁串行执行；`scripts/summarize_v2.py` 读取 raw 重算，Goal 2R 路由到简明的 `goal2r_analysis.py`。正式窗口只有一个矩阵进程，在线搜索只读自己的反馈。共同参照、搜索、外部确认和起点面板分开保存，共享面板按物理调用计费一次。

当前数据目录为 `results/goal2r_reference/`、`goal2r_comparison/`、`goal2r_starts/` 和 `goal2r_confirmation/`；[汇总表](results/goal2r_summary/summary.json)及图由这些新 raw 产生。60 个完整配置样本、六组主实验、四个 Greedy 起点和三个 Random 新种子确认均已完成。S3 的成本节省伴随三组明确观察退化，因此不保留，CLI 默认仍为 Grid。实验状态、实际成本和两类审核见[证据索引](evidence/README.md)。分析输出须使用未存在的新目录；使用保存的闭合账本快照可以重新得到相同成本表：

```bash
python3 -B P1/scripts/summarize_v2.py \
  --protocol P1/evidence/protocol_goal2r.json \
  --reference P1/results/goal2r_reference \
  --runs P1/results/goal2r_comparison \
  --runs P1/results/goal2r_starts \
  --runs P1/results/goal2r_confirmation \
  --ledger P1/evidence/measurement/goal2r/final-results-resource-ledger.jsonl \
  --output-dir P1/.cache/goal2r-recomputed --plots
```

图中范围为所测样本的最小值与最大值，不是总体置信区间；在线曲线来自当时实际反馈，外部确认不回填搜索轨迹。三基础算法使用同一配置参照；S3 与 Random 的质量差另用块内共同面板，搜索效率用各自实际 RAW driver 时间。外部评价与一次性构建另记项目成本。

历史数据只读重生成使用对应提交：Goal 1 为 `3ac0c4688b964c873379d012cbcf09afb7ed0937`，初始诊断为 `2fc0c334039bb6696c4d83acbe029ce65ca66ab9`，追加诊断为 `c247e900d3f9c4d46e4abf06092939a0a9480429`，MONOTONIC 停止为 `a39f348e6cf0c7466900ec739a797753f4d93f0b`，RAW 停止为 `5c78049a22fa3422f2b23dddd634f2e7a3d73f9d`。实际历史复算记录保存在 `evidence/reproduction/`；当前源码不冒充全部历史实现。原始证据中的真实绝对路径是运行出处，报告和可运行入口使用相对链接。

GitHub 保存工程与审核材料。此次未操作水杉；教师提交须在外部工程验收后另行准备。
