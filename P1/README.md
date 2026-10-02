# P1 运行入口

正式报告见 [report.md](report.md)。目标程序和调优器使用 GCC 与 Python 3.12，调优器只依赖 Python 标准库。数据图另需 matplotlib；真实截图测试需要 Xvfb、xdpyinfo、ffmpeg、ss（iproute2）和 xterm，可复用已有的本地工具。Windows 计时诊断的原生清理测试在可用的 WSL interop 中调用现有 PowerShell，其他环境会明确跳过这些测试。

以下命令从仓库根目录执行。正式目标固定为 n=4096，单次运行可能需要数分钟。演示输出放在忽略的 `.cache/` 中，避免混入保存的实验数据。

若 xterm 仅在另一个 checkout 的任务缓存中，运行图形测试前可用 `export PATH="/实际任务缓存/screenshot-tools/root/usr/bin:$PATH"` 为当前 shell 复用它；不要修改全局配置。没有这些工具时先安装本机缺少的依赖，再执行相应原生测试。

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

输出日志不允许直接覆盖。同一目标、编译器、完整参数和协议下可加 `--resume` 恢复；改变这些条件须使用新日志。四级构建缓存位于 `P1/.cache/build/`，搜索测量每轮重新执行。`grid`、`random`、`greedy` 是基础算法；`recheck` 是六次探索加两次候选复核的单项实验。旧 `stratified`、`patience` 的独立负结果保留，不作为默认方案。

`scripts/experiment_v2.py` 负责按冻结协议生成和串行执行批次，使用实际文件锁和资源账本；`scripts/summarize_v2.py` 从原始日志重算数据。在线搜索、完整参照、共同返回确认分别记录，确认数据不会修改在线轨迹。协议和实验记录见 [证据索引](evidence/README.md)。

本次性能扩展受时钟可比性阻塞：新的完整参照、六组在线比较、候选复核对照、确认和起点面板均未完成。原 20 配置数据保留，正文采用同一参照按配置身份重新评价；旧确认秒数和原判定不改写。`recheck` 是未获性能准入的实验入口，CLI 缺省仍是原 `grid`；目标恢复原 `CLOCK_MONOTONIC`，并不表示时钟问题已解决。

配置身份评价可从已验证的旧派生表重生成，输出必须使用新目录：

```bash
python3 P1/scripts/identity_quality.py --output-dir P1/.cache/identity-quality
```

RAW 失败批次必须用其匹配提交重算，不能在已恢复 MONOTONIC 的工作树冒充旧构建。下列分析只读取原始日志和已闭合的成本快照，不启动目标程序；应得到 47 次累计矩阵调用、RAW A/A 一次启动但零有效、七项未启动，以及 `formal_admission=false`。

```bash
mkdir -p P1/.cache
git worktree add --detach P1/.cache/reproduce-raw-stop 5c78049a22fa3422f2b23dddd634f2e7a3d73f9d
python3 P1/.cache/reproduce-raw-stop/P1/scripts/summarize_v2.py \
  --protocol P1/.cache/reproduce-raw-stop/P1/evidence/protocol_raw_aa.json \
  --raw-aa P1/.cache/reproduce-raw-stop/P1/results/raw_aa_v3 \
  --ledger P1/.cache/reproduce-raw-stop/P1/evidence/measurement/raw_timing/aa_ledger_snapshot.jsonl \
  --output-dir P1/.cache/reproduce-raw-stop/P1/.cache/derived
```

旧结果须使用匹配提交的脚本，不能由更新后的源码冒充旧版本。以下只读 detached worktree 将新派生输出放到各自缓存，保留旧日志和身份检查：

```bash
mkdir -p P1/.cache
git worktree add --detach P1/.cache/reproduce-goal1 3ac0c4688b964c873379d012cbcf09afb7ed0937
python3 P1/.cache/reproduce-goal1/P1/scripts/summarize.py \
  --reference P1/.cache/reproduce-goal1/P1/results/reference_v1 \
  --runs P1/.cache/reproduce-goal1/P1/results/selection_v1 \
  --runs P1/.cache/reproduce-goal1/P1/results/conflict_selection_v1 \
  --runs P1/.cache/reproduce-goal1/P1/results/holdout_v1 \
  --output-dir P1/.cache/reproduce-goal1/P1/.cache/derived \
  --plots P1/.cache/reproduce-goal1/P1/.cache/derived-images

git worktree add --detach P1/.cache/reproduce-initial 2fc0c334039bb6696c4d83acbe029ce65ca66ab9
python3 P1/.cache/reproduce-initial/P1/scripts/summarize_v2.py \
  --protocol P1/.cache/reproduce-initial/P1/evidence/protocol_diagnostic.json \
  --diagnostic P1/.cache/reproduce-initial/P1/results/diagnostic_v2 \
  --clocks P1/.cache/reproduce-initial/P1/evidence/measurement/clocks \
  --ledger P1/.cache/reproduce-initial/P1/evidence/measurement/resource_ledger.jsonl \
  --output-dir P1/.cache/reproduce-initial/P1/.cache/derived

git worktree add --detach P1/.cache/reproduce-followup c247e900d3f9c4d46e4abf06092939a0a9480429
python3 P1/.cache/reproduce-followup/P1/scripts/summarize_v2.py \
  --protocol P1/.cache/reproduce-followup/P1/evidence/protocol_clock_followup_r1.json \
  --clock-followup P1/.cache/reproduce-followup/P1/results/clock_followup_v2_r1 \
  --initial-root P1/.cache/reproduce-initial/P1 \
  --initial-derived P1/.cache/reproduce-initial/P1/.cache/derived \
  --ledger P1/.cache/reproduce-followup/P1/evidence/measurement/resource_ledger.jsonl \
  --output-dir P1/.cache/reproduce-followup/P1/.cache/derived
```

原始日志中的绝对路径是测量出处；分析核对哈希和计划，允许在新 checkout 只读重算。已经触发时钟停止条件的批次不得继续恢复；其他正式批次的执行恢复要求原测量目录及冻结环境一致。在新机器上重新测量须另建协议和批次。图中误差线表示已测样本的最小值与最大值，在线时间轴不含共同返回确认；完整搜索及项目成本分别保存。
