# P1 运行入口

正式报告见 [report.md](report.md)。目标程序、调优器和测试均可在 Linux 上使用 GCC 与 Python 3.12 运行；调优器只使用 Python 标准库。图表重生成另需 matplotlib。

以下命令从仓库根目录执行。正式目标固定为 n=4096，单次运行可能需要数分钟。演示输出放在忽略的 `.cache/` 中，避免混入保存的实验数据。

```bash
python3 P1/src/autotuner.py list
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s P1/tests -v
python3 P1/scripts/validate_target.py --suite small --output P1/.cache/check-small.jsonl
python3 P1/scripts/validate_target.py --suite sanitizer --output P1/.cache/check-sanitizer.jsonl

python3 P1/src/autotuner.py build --output P1/.cache/demo-build.jsonl
taskset -c 0 python3 P1/src/autotuner.py run --s 128 --opt O3 \
  --repeats 1 --timeout 1200 --output P1/.cache/demo-run.jsonl
taskset -c 0 python3 P1/src/autotuner.py search --algorithm random \
  --budget 8 --seed 104729 --repeats 1 --timeout 1200 \
  --output P1/.cache/demo-search.jsonl
```

输出日志不允许直接覆盖。同一目标、编译器、完整参数和协议下可加 `--resume` 恢复；改变这些条件须使用新日志。四级构建缓存位于 `P1/.cache/build/`，搜索测量每轮重新执行。`grid`、`random`、`greedy` 是保留的基础算法；`stratified` 与 `patience` 仅保留为两个独立实验变体，尚未证实收益，不作为推荐规则。

`scripts/experiment.py` 负责按照冻结协议生成、串行执行和恢复批次，`scripts/summarize.py` 从原始日志重算表格和图。具体协议、批次和复现命令在报告与 [证据索引](evidence/README.md) 中列出。

保存结果的汇总可在另一个目录重生成，不重新运行长实验：

```bash
python3 P1/scripts/summarize.py \
  --reference P1/results/reference_v1 \
  --runs P1/results/selection_v1 \
  --runs P1/results/conflict_selection_v1 \
  --runs P1/results/holdout_v1 \
  --output-dir P1/.cache/recomputed \
  --plots P1/.cache/recomputed-images
```

原始计划与日志保留测量时的路径、命令和哈希；汇总允许在新 checkout 中分析这些历史记录，并核对源码和协议。正式批次的 `execute/resume` 要求原测量目录与冻结环境一致；在新机器上重新测量须另建协议和批次，不能改写旧日志。图表生成后与保存表格一起阅读，在线图的时间横轴不含返回确认，完整成本见 `results/summary/search_summary.csv`。
