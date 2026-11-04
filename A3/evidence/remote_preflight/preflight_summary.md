# A3 Remote Preflight

本文件只记录学校 GPU 服务器预检查，不是 A3 正式报告。未进行正式 200 次采样、完整 Online 性能实验或 Attention 规模对照。

## 1. 总体结论

**A3 Remote Preflight: READY**

本地 WSL Codex 可以通过既有 Windows OpenSSH 调用学校服务器，完成 A3 所需计算和性能分析。依据包括：双向传输与哈希一致；PyTorch CPU/CUDA 计算正确；老师原版 persistent Triton Softmax 在非二次幂列数及 `100×5000` 单次调用通过；真实 GPU kernel trace 已回传，由本地 Perfetto Trace Processor 实际解析并执行 SQL；Python→算子/launch→GPU kernel 的关联可追溯。Online 与 Attention 基础操作也已通过。

这里的 READY 表示具备安排正式实验的技术条件。正式 A3 实验尚未开始，后续应先由用户和 ChatGPT 审核本包；GPU 空闲状态只对应记录的观察时点。

| 层次 | 实际依据 |
|---|---|
| 硬件支持 | 两张 RTX 4090，Compute Capability 8.9；只使用物理 GPU 0 |
| 环境存在且兼容 | Python 3.10.22、torch 2.6.0+cu124、Triton 3.2.0、CUPTI 12.4.127；未替换版本 |
| 任务最小功能 | CPU/CUDA Softmax、教师 Triton、Profiler、Perfetto SQL、Online、Attention 均有实际输出 |
| 本次资源与权限 | 单卡测试前显存使用 1 MiB、利用率 0%；账户实际创建 CUDA context 并运行 kernel；未发现调度器或登录节点禁用提示 |

完整记录入口：[执行清单](checklist.md)、[最终检查](final_validation.json)、[trace 检查](trace_check.json)。

## 2. SSH 与远程操作

- 本地目录：`/home/addaswsw/lab/Software_system_optimization`。
- Windows SSH：`/mnt/c/Windows/System32/OpenSSH/ssh.exe`，版本 OpenSSH_for_Windows_9.5p1。
- 实际入口：`new-server` → `bwwu@49.52.5.92:22`；远端主机 `zwlab-01`，UID 1005。
- 复用 Windows 用户现有配置；有效 known_hosts 路径为 `C:\Users\lenovo\.ssh\known_hosts`。未读取或复制私钥，未改变认证、VPN、网络或 SSH 配置。
- 使用 `BatchMode=yes`、`StrictHostKeyChecking=yes`。最终桥接脚本另显式关闭 `UpdateHostKeys`；config 与 known_hosts 的修改时间分别为 2026-10-07 和 2026-09-16 UTC，均早于本任务，未发生变更。
- Linux 命令、脚本执行、stdout/stderr 保存和退出码回传通过。`transfer_probe.sh` 故意返回 17，WSL 实际收到 17；各功能阶段返回 0。
- 采用 SSH 标准输入/输出加 base64 传输，避免 Windows SCP 对 WSL 路径的差异；没有修改 SCP/SSH 认证配置。
- 79 字节脚本上传、远端执行、回传后 SHA-256 相同：`3e819ecd7bbaa764ebea994cacace70bef95cd802e4c69b1835e8cf5211982a7`。
- 远端结果压缩包 786926 字节，SHA-256 `b060c762c43b866aa8f8eb74b95e7310d5457dfbb1de16f2dfb5df49c89110fa`；下载后整体一致，内部 28 个文件逐项哈希一致。
- `nohup` 启动的 8 秒纯 CPU 命令在 SSH 退出后继续运行；再次连接读取完成日志和退出码 0，进程已经退出。

证据：[首次连接与系统查询](commands/inventory.txt)、[传输及退出码](commands/workflow_probe.txt)、[重新连接](commands/reconnect.txt)、[下载校验](transfer_verification.json)、[实际命令索引](commands/commands.jsonl)。

## 3. 系统与 GPU 资源

系统为 Ubuntu 26.04.1 LTS，Linux 7.0.0-31-generic。CPU 为 Intel Xeon Gold 6133 @ 2.50 GHz，2 sockets、80 个可用逻辑处理器。系统内存 247 GiB，首次检查约 239 GiB available。

用户目录位于 `/dev/nvme0n1p3` 的 ext4 文件系统，容量 851 G、可用 575 G。家目录可写，独立目录创建成功；没有 `quota` 工具，挂载选项未显示 quota，不能据此保证没有管理员侧配额。

观察时间为 2026-11-04 17:24:21、17:25:41、17:34:32、17:41:11、17:42:30 UTC，分别对应纽约时间 12:24:21、12:25:41、12:34:32、12:41:11、12:42:30 EST。最后一次结果如下。

| 物理 GPU | 型号 | 总显存 MiB | 已用 MiB | 空闲 MiB | 驱动保留 MiB | 利用率 | 当时状态 |
|---|---|---:|---:|---:|---:|---:|---|
| 0 | NVIDIA GeForce RTX 4090 | 24564 | 1 | 24082 | 482 | 0% | 无计算进程；本次实际测试使用 |
| 1 | NVIDIA GeForce RTX 4090 | 24564 | 1 | 24082 | 482 | 0% | 无计算进程；只查询，未运行计算 |

GPU 0 UUID：`GPU-dfff0e95-1db6-e2f4-3431-55bb852fa0ae`。

GPU 1 UUID：`GPU-59cac3bd-3645-668b-79c8-839e0d878893`。

两卡驱动均为 595.91.07，驱动报告 CUDA 支持版本 13.2，Compute Capability 均为 8.9。驱动保留显存另列，因此 used 与 free 之和不等于 total。两张 24 GB 卡不是一张 48 GB 卡。

所有 CUDA 测试仅在测试进程内设置 `CUDA_VISIBLE_DEVICES=GPU-dfff0e95-1db6-e2f4-3431-55bb852fa0ae`，进程内逻辑设备为 `cuda:0`。未修改全局设备配置。未屏蔽设备的单独枚举得到 2 张卡，且 `torch.cuda.is_initialized()` 为 False。

未发现 `sbatch/srun/sinfo/squeue/qsub/bsub/condor_submit`、相关调度进程、Slurm/PBS 配置或 MOTD 中的禁止提示。依据用户授予的单卡轻量测试权限执行，没有证据显示必须经过调度器。本次未向管理员查询未公开的政策；正式运行仍应遵守学校和课题组的资源安排。

GPU 进程显存曾为 462–492 MiB，包含 CUDA context 和采集库。最大 PyTorch tensor allocator 使用约 13.36 MiB，最大 reserved 为 22 MiB；完整形状输入本身只有 2000000 字节。测试后两张卡恢复上述状态，未终止或重置任何任务。

证据：[系统/存储](commands/inventory.txt)、[稍后 GPU 快照](commands/dependencies_discovery.txt)、[最终资源复查](commands/final_bridge_check.txt)、[CUDA](remote/logs/cuda.json)、[Triton](remote/logs/triton.json)、[Attention/Online](remote/logs/extras.json)。

## 4. 软件依赖

复用 `/data/bwwu/envs/tiger/bin/python`，只运行代码和读取正常依赖元数据，没有向该环境写入依赖。另一个登记环境具有相同 torch/Triton 版本，未运行其研究代码或修改环境。

| 项目 | 状态 | 实际结果 |
|---|---|---|
| 选定 Python | AVAILABLE | 3.10.22；系统 `/usr/bin/python3` 为 3.14.4 |
| pip / venv | AVAILABLE | pip 26.2.1；venv 模块存在；未新建虚拟环境 |
| Conda CLI | MISSING | 检查入口未发现；已登记环境可以直接使用 Python 路径 |
| PyTorch | AVAILABLE | 2.6.0+cu124；系统 Python 无 torch |
| PyTorch CUDA Runtime | AVAILABLE | 12.4；实际 CUDA 计算通过 |
| Triton / triton.language | AVAILABLE | 3.2.0；实际编译及执行通过 |
| GCC / G++ | AVAILABLE | Ubuntu 15.2.0；Triton launcher 编译通过 |
| Clang | MISSING | PATH 中未发现；本任务未依赖 |
| 系统 CUDA Toolkit / nvcc | MISSING | PATH 和常见 `/usr/local/cuda*` 未发现；没有执行全盘搜索 |
| Triton 编译工具链 | AVAILABLE | 自带 ptxas release 12.4，V12.4.99，target cuda/sm89 |
| CUPTI | AVAILABLE | nvidia-cuda-cupti-cu12 12.4.127；真实加载 libcupti.so.12 |
| torch.profiler CPU / GPU | AVAILABLE | CPU ATen 统计、GPU kernel 时间及导出通过 |
| with_stack=True | AVAILABLE | 统计表/导出正常；真实 Python frame 和 Perfetto 父子链可用 |
| Perfetto CLI | CONFIGURED | 本地新增官方 Trace Processor v59.1，真实解析四个 trace 和 SQL |
| Windows Edge Perfetto GUI | UNVERIFIED | 本轮未操作 GUI；使用实际 CLI 解析完成分析链路验证 |
| tmux / screen / nohup | MISSING / AVAILABLE / AVAILABLE | screen 仅验证入口；nohup 实际断连测试通过 |
| Nsight Systems / Compute | MISSING | PATH 未发现；A3 指定分析使用 torch.profiler/Perfetto |

版本概念分别为：驱动报告支持 13.2、系统 Toolkit 未发现、PyTorch runtime 12.4、Triton 自带 ptxas 12.4.99。它们并不矛盾，实际计算与编译已经通过。

驱动 `RmProfilingAdminOnly=1` 限制硬件计数器权限；本题所需 CUPTI activity/kernel 时间线已实际成功，无需修改驱动设置或获得 sudo。

补充元数据探测曾失败：`find_spec('pip')` 触发 setuptools 83.0.0 的 `_distutils_hack.spec_for_pip`，在同一解释器中随后导入 Triton 会出现 distutils AssertionError。已复现并读取该公开依赖的对应源码；普通 `import triton`、`import importlib.metadata; import triton` 及老师的 `import torch; import triton` 均成功。拆开包元数据和模块导入检查即可，不需要修改环境或安装软件。

证据：[版本与初始 imports](commands/remote_setup.txt)、[元数据](commands/dependencies_diagnostic.txt)、[原始探测错误](commands/dependencies.stderr.txt)、[针对性复现](commands/collection.txt)、[复现 stderr](commands/collection.stderr.txt)。

## 5. 实际执行的最小测试

所有输入均随机生成、FP32；CPU 测试线程为 1，没有下载数据集或模型。CPU 在修正 Profiler 首次加载后重复了受影响的小测试；GPU naive、Triton、Attention 各只有一次目标函数 Profiler 调用。没有 200 次循环或参数搜索。

| 检查 | 实际结果 | 证据 |
|---|---|---|
| CPU 五步 naive，4×127 | 最大绝对误差 3.7253e-9；最大行和误差 1.1921e-7；全部有限 | [cpu.json](remote/logs/cpu.json) |
| CPU Profiler | aten::max/sub/exp/sum/div 等存在；CPU trace 72009 字节 | [cpu.log](remote/logs/cpu.log) |
| CUDA naive，4×127 | 最大绝对误差 1.4901e-8；行和误差 0；显式同步完成 | [cuda.json](remote/logs/cuda.json) |
| CUDA GPU Profiler | 5 个真实 kernel，合计 9855 ns；5 条 launch→kernel flow | [CUDA SQL](perfetto/perfetto_cuda_naive.csv) |
| 教师 Triton 编译/API | warmup、_init_handles、n_regs、metadata.shared、device properties、persistent 启动全通过 | [triton.json](remote/logs/triton.json) |
| 非二次幂，4×127 | BLOCK_SIZE=128；最大绝对误差 1.4901e-8 | [triton.json](remote/logs/triton.json) |
| 教师 100×5000 单次 | BLOCK_SIZE=8192；最大绝对误差 9.3132e-10；最大行和误差 2.3842e-7 | [triton.json](remote/logs/triton.json) |
| Triton Profiler | 编译/预热在外；with_stack=True；1 个 softmax_kernel，1504 ns | [Triton SQL](perfetto/perfetto_triton.csv) |
| Online，4×32 CPU/CUDA | 最大误差分别 1.4901e-8 / 2.9802e-8；两次逐列遍历与图片递推一致 | [extras.json](remote/logs/extras.json) |
| Attention，L=16，dk=dv=64 | 输出 16×64；对照 CPU FP64 再转 FP32，最大误差 2.3842e-7 | [extras.json](remote/logs/extras.json) |
| Attention Profiler | 两次 mm、div、softmax 均捕获；4 个 GPU kernel、4 条 flow | [Attention SQL](perfetto/perfetto_attention.csv) |
| Perfetto | 四个 trace 实际导入，全部 10 个 kernel 的时间与 Python 祖先链可用 | [结构及 SQL 检查](trace_check.json) |

Triton 保留 `num_warps=8`、`num_stages=4 if SIZE_SMEM>200000 else 2`、原始 mask/reduction 和 occupancy 计算。设备属性为 128 SM、每 SM 65536 registers、共享内存 101376 字节、warp size 32。小形状为 n_regs=24/shared=528/公式 occupancy=10/programs=4；完整形状为 n_regs=80/shared=32800/公式 occupancy=3/programs=100。这里 occupancy 是老师公式的计算值，不是硬件实际驻留测量。

老师核心代码与 PDF 第 4–5 页转录结果 AST 相同，无算法或兼容 API 修改，见 [PDF 对齐记录](pdf_alignment.json)。完整形状仅启动一次；Triton Profiler 使用已经编译的小形状，不对完整形状再次采样。

with_stack=True 下 FunctionEvent.stack 列表为空，但四个 trace 分别包含 237/324/606/322 个真实 Python frame。Perfetto 中可沿 naive_softmax→aten::exp→cudaLaunchKernel→GPU exp kernel，以及老师 softmax→Triton driver→cuLaunchKernel→softmax_kernel 追溯。未把“没有异常”当作调用关系通过的唯一依据。

实际执行的原题 SQL：

```sql
SELECT AVG(dur) / 1e9
FROM slice
WHERE name = 'aten::exp';
```

CPU 结果按整数时间查询为 9736 ns，即 0.000009736000 s，与表中 CPU time avg 9.736 µs 一致。默认 CSV 六位小数显示为 0.000010，补充精度查询保存了精确数值。这里只验证采集/解析功能，不据这些单次时间作正式性能结论。

四个正式保留的预检查 trace 共 449762 字节：

- [CPU naive](remote/traces/cpu_naive.trace.json)：72009 字节。
- [CUDA naive](remote/traces/cuda_naive.trace.json)：106890 字节。
- [Triton](remote/traces/triton.trace.json)：168869 字节。
- [Attention](remote/traces/attention.trace.json)：101994 字节。

保留的诊断与警告：

1. 最初 CPU trace 混入首次 Profiler 模块加载，约 10.1 MB。远端保留在 `logs/cpu_initial.trace.json`，本地对应 `remote/logs/cpu_initial.trace.json`；添加无计算的 Profiler 初始化后，CPU 复测缩小至 72 KB。修改见 [诊断 patch](profiler_initialization.patch)。
2. CPU 阶段显式隐藏 GPU，因此 Kineto 记录 `gpuGetDeviceCount failed with code 100`。CPU 功能通过，实际 CUDA 阶段成功，不将该日志解释成服务器 GPU 不可用。
3. Triton 首次编译出现 `_POSIX_C_SOURCE` 重定义 warning，编译和执行均成功。
4. Perfetto 每个 trace 保留 1 个 `slice_spill_overlapping_complete_event` 提示。原始 JSON 显示自加 `record_function` 范围与其 Python enter/exit 帧交叠；Perfetto 将该范围移至 overflow track，没有丢弃事件。SQL 导入后的 ATen/Python/kernel 数量与原始 JSON 完全相同，所有目标 GPU kernel 的 flow 和 Python 祖先链均匹配，其他 error/data_loss 计数为 0。原始 trace 未编辑；后续正式脚本可省去自加 scope，沿实际 Python/ATen 链分析。
5. `profiler_cuda_duration_us` 是原始所有 CUDA 类型事件的合计，含 `gpu_user_annotation`，不应当作 kernel 总时间；实际 kernel 时间以 `trace_kernel_duration_us` 及 Perfetto 的 `category='kernel'` 查询为准。

## 6. 配置变更与预算

- 新建远端 `/home/bwwu/lab/SSO_A3_preflight`，权限 700；原来不存在。包含本轮脚本、logs、traces、cache 和结果回传包。
- 所有临时环境变量只作用于本轮进程：CUDA_VISIBLE_DEVICES、线程限制、PYTHONDONTWRITEBYTECODE 和独立 XDG/TRITON/CUDA/Inductor cache 路径。
- 未创建新虚拟环境。**远端未安装额外依赖**；没有 apt/pip/conda 安装，没有 sudo，没有修改驱动、全局 CUDA、默认 shell 或研究环境。
- WSL 仅新增官方 Perfetto v59.1 native CLI 和官方 manifest wrapper，位于 `.cache/a3-remote-preflight-tools/`。下载量分别为 15885448 与 10698 字节，总计 15896146 字节（约 15.16 MiB）。native 二进制 SHA-256 与官方 manifest 一致，详见 [安装记录](installation_log.json)。
- 最后检查远端目录共 11720174 字节，cache 为 283176 字节，远低于本轮预算。没有复制整个研究环境或下载 PyTorch/CUDA 安装包。
- 本地只新增预检查证据及七个辅助脚本。原有 41 个 A3 文件未变，老师 PDF 未变，其他作业和 Git 历史未变。
- 没有删除既有文件；只清除了本轮新生成的一份 preflight_ssh Python bytecode。旧 A3 缓存未动。

用户可在审核后决定是否保留本地 Perfetto 工具和远端预检查目录；本轮未擅自清理这些证据。

## 7. 魔搭替代分析

| 能力 | 是否可迁移 | 依据/边界 |
|---|---|---|
| GPU 计算 | 可以 | FP32 Softmax、在线递推和小 Attention 正确 |
| 教师 Triton | 可以 | 原逻辑及 100×5000 单次通过，无 API 补丁 |
| CPU/GPU Profiler | 可以 | ATen、CUDA kernel、CUPTI activity 与导出均实际成功 |
| 本地 Perfetto | 可以 | WSL native Trace Processor 真实解析和 SQL 已验证；Edge GUI 尚未操作 |
| A3 所需其他计算功能 | 无发现无法替代的技术功能 | 本次只验证最小功能，正式 200 次与规模对照尚未执行 |
| Step 1 的魔搭登录/Notebook/创建环境 | 不能据此声称已完成 | 这是题目指定的平台操作；计算迁移与该项作业要求不同，应向老师确认接受的替代方式 |

服务器使用 RTX 4090、torch 2.6/cu124、Triton 3.2，与参考 A10/torch 2.13/cu130/Triton 3.7.1 不同。实际版本应如实写入后续正式报告，正式结果不可与 A10 数值直接等同。

2.5 后续峰值带宽参照应使用桌面 RTX 4090 的官方 **1008 GB/s**（规格值，不是本轮实测），不再直接使用 A10 约 600 GB/s。来源：[NVIDIA Ada GPU Architecture V2.02，Appendix A / Table 2，第 30 页](https://images.nvidia.com/aem-dam/Solutions/geforce/ada/nvidia-ada-gpu-architecture.pdf#page=30)。

## 8. 后续推荐执行流程

审核通过并得到正式实验授权后，采用：WSL `A3/` 编辑 → Windows SSH 上传 → 远端独立作业目录执行 → 保存日志/exitcode/trace → SHA-256 回传 → 本地 Perfetto 分析 → 编写 A3 正式报告。

远端现已验证的 Python 为 `/data/bwwu/envs/tiger/bin/python`。本次预检查目录继续保留，正式实验建议使用另一个明确命名的运行目录，避免覆盖这些证据。本轮没有创建正式作业目录或脚本。

每次 GPU 运行前再次查询设备利用率、显存和计算进程，按课题组规定选一张卡；使用该卡 UUID 限制单进程可见设备。首次编译、预热、输入生成和传输放在正式采样区间外。

本轮已实际使用的命令形式：

```bash
# 查询及脚本执行：Windows OpenSSH 通道；使用新的日志 label。
python3 -B A3/scripts/preflight_ssh.py run \
  A3/evidence/remote_preflight/commands/final_remote_state.sh \
  --label final_bridge_check --timeout 30

# 已运行的双向传输形式；本工具拒绝覆盖已有文件，重用时须换新目标/label。
python3 -B A3/scripts/preflight_ssh.py put \
  A3/scripts/preflight_smoke.py \
  /home/bwwu/lab/SSO_A3_preflight/preflight_smoke.py --label upload_smoke
python3 -B A3/scripts/preflight_ssh.py get \
  /home/bwwu/lab/SSO_A3_preflight/remote_results.tar.gz \
  A3/evidence/remote_preflight/remote_results.tar.gz --label download_results

# 已完成的本地 Perfetto 查询；此命令只读取本地 trace。
.cache/a3-remote-preflight-tools/trace_processor_shell query \
  --format csv -f A3/scripts/preflight_perfetto.sql \
  A3/evidence/remote_preflight/remote/traces/cpu_naive.trace.json
```

这些是已验证机制及历史调用形式；不能原样重跑需要新文件/新 label 的传输命令。后台执行可采用本轮实际验证的 `nohup` 加 stdin=/dev/null、stdout/stderr 文件重定向、独立 exitcode 文件；具体实现见 [后台启动命令](commands/workflow_probe.sh)。存在正式调度规定时应改按规定提交，不能用 nohup 绕过调度。

本地 GUI 入口为 [Perfetto UI](https://ui.perfetto.dev/)，可在 Windows Edge 选择回传的 JSON。这个 GUI 动作本轮未执行；实际解析和 SQL 是在 WSL CLI 完成，使用方式依据 [Perfetto 官方命令行文档](https://perfetto.dev/docs/getting-started/command-line-analysis)。

## 9. 问题、风险与停止点

无已知技术阻塞；无需大型安装或系统修改。已经解决/解释的探测错误与 trace warning 原样保留，见第 4–5 节。

正式实验前需要：

1. 用户和 ChatGPT 审核本包，再授权正式实验。
2. 核对老师是否接受 Step 1 平台操作的替代方式；本预检查不代替此项。
3. 再查 GPU 占用与课题组资源安排；当前空闲不是预约或长期保证，SSH 也不保证永不掉线。
4. 复核复用环境版本是否变化；只读复用研究环境，不往其中安装 A3 依赖。
5. 正式统计只选 ATen/Triton 计算行，区别 CPU/GPU annotation 范围与真实 kernel 时间；小规模预检查时间不作为性能实验数据。
6. 若希望浏览器可视化验收，打开回传 trace 查看时间线。CLI SQL 解析链已经通过；GUI 尚未操作。

没有遗留 GPU 作业、常驻进程、待处理安装或必须先批准的技术变更。本轮到此停止，不推进正式实验。

## 10. 文件与审核信息

- 本地证据：`/home/addaswsw/lab/Software_system_optimization/A3/evidence/remote_preflight/`。
- 远端独立目录：`/home/bwwu/lab/SSO_A3_preflight/`。
- 辅助脚本：[SSH 桥接](../../scripts/preflight_ssh.py)、[系统清单](../../scripts/preflight_inventory.sh)、[阶段执行](../../scripts/preflight_run.sh)、[功能检查](../../scripts/preflight_smoke.py)、[教师原版核心](../../scripts/teacher_softmax_preflight.py)、[Perfetto SQL](../../scripts/preflight_perfetto.sql)、[trace 核对](../../scripts/preflight_trace_check.py)。
- 主要日志位于 `commands/` 和 `remote/logs/`；四个小 trace 位于 `remote/traces/`；SQL 原始输出位于 `perfetto/`。
- 轻量包：`A3/evidence/remote_preflight/a3_remote_preflight_review.zip`。包括本总结、真实日志/错误、版本/资源快照、七个脚本、四个小 trace、初次 CPU 诊断 trace、SQL 结果、校验清单。排除环境/cache、工具二进制、老师 PDF、旧 A3 材料及冗余回传 tar。
- ZIP 的准确大小与 SHA-256 见 ZIP 旁 `bundle_metadata.json` 及最终回复；该旁文件不嵌入 ZIP，避免自引用哈希。
- **GPT_UPLOAD_REQUIRED: YES**。本轮没有发布 GitHub 或其他可供另一 GPT 直接访问的证据入口，需用户上传 ZIP 供独立审核。
- Git：`main`，HEAD `65c2128e142bf59a6e19ff635b760be3729abbac`，相对本地缓存 origin/main 落后 2 次提交。既有未跟踪项仍在，A3/ 也仍未跟踪；没有更改 tracked 文件、commit、fetch/pull 或 push。
- 没有 GitHub 或水杉网络操作，没有水杉提交；没有修改 GRID/SID 或其他研究代码、依赖、模型、数据、checkpoint 或进程。

这是预检查结论，不是正式 A3 完成结论，也不是独立审核给出的 Engineering=PASS。
