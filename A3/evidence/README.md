# A3 实验与审查证据索引

正式报告为 [A3/README.md](../README.md)。这里是内部证据，不作为老师报告正文。

## 快速入口

- [逐题要求矩阵](requirements.md)：覆盖原题每个小问及平台差异。
- [冻结的测量协议](review/measurement_protocol.md)：输入、次数、线程、精度、统计方式和执行角色。
- [全部复算数据](review/derived_results.json)：带宽、两种计时、Attention四阶段和模型。
- [正确性](correctness/)：5份学校服务器结果，58项固定容差检查。
- [独立代码/公式复核](review/independent_code_math.md)、[独立统计复核](review/independent_statistics.md)、[报告全文复读](review/independent_report.md)、[主代理完整自审](review/self_review.md)。
- [最终文件检查](review/final_validation.json)、[正式trace清单](review/trace_manifest.json)、[截图记录](commands/screenshots.jsonl)、[Perfetto真实GUI记录](review/browser_setup.md)。
- [GitHub远端回读](review/github_verification.json)：发布后生成，核对远端main和内容哈希；不替代ChatGPT的最终审核。

## 实际执行与结果

| 内容 | 原始证据 |
|---|---|
| 本地WSL / 学校实际环境 | [local_formal.json](environment/local_formal.json)、[school_cpu.json](environment/school_cpu.json)、[school_gpu.json](environment/school_gpu.json) |
| SSH与目录/版本确认 | [remote_initial.sh](commands/remote_initial.sh)、[对应输出](commands/remote_initial.txt)、[全部远程命令索引](commands/commands.jsonl) |
| 上传同一份源码与哈希 | [remote_source_manifest.json](review/remote_source_manifest.json)、[远端源码哈希](commands/remote_setup.txt) |
| 断线可保留的独立作业 | [实际worker.sh](commands/jobs/worker.sh)、同目录5份退出码和日志；全部退出0 |
| 每组GPU占用检查 | commands/gpu_before_*.txt；各记录UUID→cuda:0及两卡状态 |
| CPU正式200次 | [cpu/](cpu/)，完整表、metadata/statistics、完整trace.gz、Perfetto SQL原始输出 |
| GPU naive/Triton正式200次 | [gpu/](gpu/)，包含全部kernel、相关launch及逐行Profiler数据 |
| Online完整100×5000 | [online/](online/)，各1次完整profile、各5次无Profiler同步计时；完整35005kernel trace，未缩小/裁剪 |
| Attention三档 | [attention/](attention/)，各10次profile、各5次独立计时；两MM依据External id/correlation归属 |
| 双向传输验证 | review/{cpu,softmax,online,attention}_transfer.json，tar整体及逐文件SHA-256 |
| 最终设备空闲 | [remote_attention_collect.txt](commands/remote_attention_collect.txt)；两卡1MiB/0%，无计算进程 |
| 安装与改动记录 | [installation_log.json](review/installation_log.json)：无新增依赖或系统配置，记录任务目录 |
| Git集成与用户工作保护 | [git_integration.json](review/git_integration.json)：main安全快进，P2原有534文件逐字节保留，原有差异未提交 |

学校执行环境：`/home/bwwu/lab/SSO_A3`，Python `/data/bwwu/envs/tiger/bin/python`。任务本地源文件上传后哈希一致；服务器只运行任务私有目录中的代码、日志和cache，没有修改共享环境或其他研究项目。

## 复算与重新运行

只使用标准库复算已发布数据（无需GPU）：

```bash
python3 -B A3/scripts/analyze_results.py
python3 -B A3/scripts/validate_artifacts.py
```

8份正式trace均为原始完整Chrome JSON的无损gzip，原始与压缩SHA及字节数见 [trace_manifest.json](review/trace_manifest.json)。浏览器截图保存的是对应原JSON的SHA；直接解压再加载 [Perfetto](https://ui.perfetto.dev/)。为避免覆盖已有文件，可把所需trace解压到仓库外临时目录：

```bash
gzip -dc A3/evidence/cpu/cpu_naive.trace.json.gz > /tmp/a3-cpu-naive.trace.json
.cache/a3-remote-preflight-tools/trace_processor_shell query --format csv \
  -f A3/scripts/perfetto_queries.sql /tmp/a3-cpu-naive.trace.json
```

GPU查询为 [perfetto_gpu.sql](../scripts/perfetto_gpu.sql)，其中`avg_one_kernel_us`是单个kernel平均，不能当完整Softmax时间。完整调用时间由所有kernel求和后除以调用次数获得。

重新采集使用 [run_cpu.sh](../scripts/run_cpu.sh) 和 [run_gpu.sh](../scripts/run_gpu.sh)，或直接调用 [profile_workload.py](../scripts/profile_workload.py)。请在干净的独立副本/新的输出目录运行，以免覆盖本次测量。GPU入口必须显式选择一个物理UUID，先查资源再串行测量，不能并发benchmark：

```bash
PYTHON_BIN=/data/bwwu/envs/tiger/bin/python bash scripts/run_cpu.sh
CUDA_VISIBLE_DEVICES=GPU-dfff0e95-1db6-e2f4-3431-55bb852fa0ae \
PYTHON_BIN=/data/bwwu/envs/tiger/bin/python bash scripts/run_gpu.sh correctness
# correctness完成后，按顺序选择softmax、online、attention阶段。
```

本次后台作业还在进程内固定OMP/MKL线程和任务私有CUDA/Triton cache，完整命令见worker.sh。既有环境可复用；不得为重新实验降级/改写共享研究环境。截图脚本仅操作实际xterm或官方Perfetto UI，复现信息在相应记录中。

## 历史材料

- `remote_preflight/` 是本轮之前的完整环境/功能预检查，不冒充正式200次实验。该总结保留当时READY结论及当时已清理ZIP的文字引用；用户本次已明确确认外部审核PASS，不重新生成预检查ZIP。
- `earlier_local/` 是早期本地CPU/魔搭连接阻塞记录，没有用它们替代学校正式实验。移动记录见 [evidence_moves.json](review/evidence_moves.json)。
- 两份较大的历史诊断trace也仅无损压缩发布，原始SHA/路径见 [historical_trace_compression.json](review/historical_trace_compression.json)。它们不是本次性能结果。

正式数值和原始失败信息均未编辑。只有最终GitHub实查才能进入外部最终审核；这些内部自检不赋予Engineering PASS，也没有水杉提交。
