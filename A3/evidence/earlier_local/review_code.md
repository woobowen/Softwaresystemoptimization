# A3 独立代码与理论复核记录

本记录由独立复核 agent 编写。只读检查其他文件，仅编辑本文件；未执行性能实验、安装、Git 操作或修改实现。结论限于下列实际阅读的文件，不代替数值运行、Perfetto 分析、完整交付检查或最终工程审查。

## 1. 检查材料和边界

- 首个 shell 命令为仓库根目录的 `ls -la`，随后完整读取根目录 `AGENTS.md`，未发现 A3 内的覆盖规则。
- 阅读正式六页 PDF 的全部提取文本，并实际查看第 5 页图片中的 Algorithm 3。题名、日期与任务指定材料一致。
- 首轮全文阅读：`src/softmax.py`、`src/attention.py`、`scripts/check_softmax.py`、`scripts/check_attention.py`、`evidence/attention_model.md`。
- 此时尚无运行结果可用于数值或性能判断；没有将未运行项目标为通过。

## 2. 首轮逐项检查

| 项目 | 对应位置 | 静态检查结果 |
|---|---|---|
| 五步 naive Softmax | `src/softmax.py:7–12` | 最大值、广播减法、指数、求和、除法与老师代码一致；没有融合或更换算法。 |
| Online 初始状态 | `src/softmax.py:16–18` | 每行最大值为负无穷，归一化状态为零；dtype、device 继承输入。 |
| Online 递推 | `src/softmax.py:20–25` | 只沿 M 列循环，每次用 N 元素张量并行更新全部行；d 更新使用旧 m，随后才替换 m；符合 PDF 图片的递推式。 |
| Online 最终输出 | `src/softmax.py:27` | 使用最终 m、d 对完整输入广播求输出，保留了第二次输入访问；循环没有 `.item()`、NumPy 或设备搬运。 |
| Softmax 检查 | `scripts/check_softmax.py:14–74, 91–118` | 固定 FP32、seed、`rtol=1e-4, atol=1e-6`；检查形状、dtype、device、有限性、行和与参考误差；普通、同元素、大正负有限值、非二次幂、边界和 100×5000 均覆盖。 |
| Attention 四阶段 | `src/attention.py:8–13` | 显式 QKᵀ、除以 √dk、torch.softmax、PV；单头前向结构，没有替换为融合 API。 |
| Attention 参考 | `scripts/check_attention.py:20–25, 58–69` | 以同一批 CPU FP32 输入值转 FP64 做稳定数学参考；没有以相同 FP32 主实现充当唯一参考。 |
| Attention 性质和边界 | `scripts/check_attention.py:44–54, 61–65, 88–102` | 包含 Lq≠Lk 且 dk≠dv、零 Q 的均匀权重与 mean(V)、长度 1、三档分析尺寸。 |
| Attention 精度与判定 | `scripts/check_attention.py:15–17, 39–41, 70–102` | 固定原定容差，逐元素检查失败数量，保存绝对误差及误差/容差比；统一使用 `highest`。 |
| CPU 模块导入 | 两个核心模块及两个检查脚本 | 核心模块只导入 torch/math；检查脚本仅在明确请求 cuda 时检查 CUDA。CPU 路径没有导入 Triton 或查询 GPU properties。 |

首轮没有发现需要修改的实际代码缺陷。以上是静态结论，不能据此声称数值检查或 GPU 运行已经通过。

## 3. Attention 公式独立复核

`evidence/attention_model.md:14–28` 对四阶段分别计一次输入读取和输出写入，分数/概率矩阵的系数为 `1+2+2+1=6`。`K.T` 是视图，不计一份额外全量转置。简化逻辑字节模型与实际四阶段、FP32 一致：

```text
B = 4(Lq*dk + Lk*dk + Lk*dv + Lq*dv + 6Lq*Lk)
F_matmul = 2Lq*Lk*(dk+dv)
```

当 `L=512, d=64`，复核得到 `F=67,108,864 FLOPs`、`B=6,815,744 bytes`、`I=9.846153846 FLOP/Byte`。128、2048 两档表格中的流量、FLOPs、MiB 换算及强度数值也相符。

`attention_model.md:40–48` 的一般形状时间/空间复杂度及方形简化正确；已明确区分包含输入输出的空间、额外注意力矩阵空间和逻辑流量。`69–70` 注意到非原位缩放的短暂双 S，以及函数内保留 S、P 的生命周期，未把张量估算冒充 allocator/进程实测内存。

精度说明已与 [PyTorch 官方 `set_float32_matmul_precision` 文档](https://docs.pytorch.org/docs/2.15/generated/torch.set_float32_matmul_precision.html) 对照：`highest` 使用 FP32 内部矩阵乘精度，CUDA 对应禁用 TF32。该 API 的语义支持脚本当前说明；最终仍需在实际运行版本记录配置。

## 4. 首轮内容标识

```text
1854aab2de72596243c0f76948cfea38a75226d6e8a01c3dcace99d2a5e6f5f1  src/softmax.py
44f02823b2a7599074ffb4d5a0b8ec151944fefe43b6640fea97dda04d0f9faa  src/attention.py
d1b6ca949db5dd8b51b16d9ae2fe483117e6a9cfb756fbefd34a0b05908399dc  scripts/check_softmax.py
b6c017d2409dad02317713c6a37c004cb01415be402e71acebab96b55c5684f0  scripts/check_attention.py
6d168ffb6fd878dda62703d0047d79cf3f4a272f2e01d6c4bf27da24f4e8ade0  evidence/attention_model.md
```

## 5. 后续复核范围

等待主 agent 完成 `triton_softmax.py`、profiling、environment 等脚本后进行追加只读检查。数值结果、SQL 范围/分母、实际 kernel 时间与带宽、正式截图和 README 尚不在本首轮结论中，不能使用本记录宣布 `Engineering = PASS`。

## 6. 新增 Triton 与环境脚本的静态检查

全文追加阅读 `src/triton_softmax.py`、`scripts/check_triton.py`、`scripts/environment.py`。

- Triton 核心仍保留老师的逐行 persistent program、next_power_of_2、mask、8 warps、shared-memory 决定的 stages、warmup 后查询资源和 occupancy 计算，没有重写算法。
- 设备属性查询位于 `softmax()` 内，仅在明确调用时进行，模块顶层没有初始化 active driver；CPU 主实现和检查脚本也没有导入本模块。
- 环境脚本 `24–53` 在 CPU 模式记录实际 OS/CPU/内存、PyTorch/构建 CUDA/Triton 元数据、线程、目录和 cgroup 限制；`torch.cuda.is_initialized()` 只查询状态。实际 GPU 属性探测只在 `54–68` 的 CUDA 分支进行。
- Triton 检查复用原定 seed、容差和全部 Softmax 场景；没有单独调宽容差或删除困难输入。

发现一个待实际 GPU 运行确认的兼容风险：`triton_softmax.py:54–56` 直接执行 `size_smem // kernel.metadata.shared`。小 BLOCK_SIZE 可能无需共享内存，若实际编译产物的 `shared=0` 则触发除零；这段原样继承自老师代码。建议先保留失败日志和实际 metadata，再按 `shared>0` 条件施加该资源上限，作为最小兼容修复。此处未实际编译 CUDA kernel，因此不将“可能”写成已经复现的故障。

## 7. Profiling 入口复核

第二次全文阅读 `scripts/profile.py`，并再次阅读上一节的三个新增文件。仍未运行性能任务；以下按当时 `profile.py` SHA256 `920b2a9a2b56b8f6c3a4a7eaa2193233295d707f42d517990f419cf14400e47d` 记录。

### 调用、采集与计时边界

- `84–88` 仅 `cpu-naive` 使用 CPU，CUDA 缺失直接停止，未自动把 GPU 任务换为本地 CPU；CPU 路径也不会因导入核心算法而初始化设备。
- `102–129`：三个主 Softmax 实验 200 次完整调用，Online 对照双方各 1 次、输入 100×5000；Attention 10 次，长度限定在 128/512/2048、维度 64。每个进程使用固定 CPU generator，从同源输入搬到设备，并保存输入哈希。
- `130–151`：先完整 preflight 数值检查和计时，然后 5 次预热并同步，最后才进入 Profiler；输入创建、搬运、参考计算、首次实际 Triton 编译都在正式采样外。Online 双方关闭栈采集，主实验保留 `with_stack=True`。
- `155–163`：Profiler 已退出，之后才做 5 次 `perf_counter_ns` 计时；GPU 每次完整调用前后同步，无逐算子同步。该数值是同步的完整调用墙钟延迟，不能与 Profiler kernel 累计时间混用。

### 排名和时间单位

- `30–44` 保存不截断的完整表和逐行 CPU/device/self 时间。`50–59` 先筛选 `aten::*` 与实际 CUDA `softmax_kernel`，再分别按 CPU total、device total 排序；GPU 排名排除设备时间为零的行，Python/launch 行不会进入题目排名。
- `45–49, 60–63` 直接从 Chrome trace 中完整的 `cat=kernel, ph=X` 事件求和，按 trace 的微秒单位除以完整调用数。没有叠加 ATen 父子归因或把 CPU 时间用作 GPU 分母。
- `54` 的 `profiler_self_cpu_total_us` 为全部 key_averages 行的 Self CPU 之和，适合提供给后续 SQL 的交叉核对；最终 SQL 仍需按真实 trace 嵌套关系计算非重复 CPU self 时间，不能拿全部 slice 总和替代。
- CUDA trace 没有 kernel 会显式报错，不能只凭 CUDA 可用性生成成功结论。最终 GPU 实测仍要核对类别、kernel 名、调用数和 trace 单位是否符合实际版本。

### 输出和单一来源

核心 Softmax、Online、Attention 均从 `src/` 导入；profiling 没有复制第二套被测算法。每个实验单独进程、独立 prefix，保存 trace、全表、逐项统计、输入哈希、源码哈希和采样参数；没有硬编码个人机器的目录。保存环境中的绝对 cwd 属于内部事实记录。

### 待主 agent 处理的两项具体意见

1. `profile.py:104,113` 的 `torch.randn` 没有显式 `dtype=torch.float32`，而 metadata 固定写 FP32。独立 CLI 的默认值通常是 FP32，但 Notebook 若改过全局默认 dtype，实际输入可与声明不符；建议在这两处明确 dtype，将本题硬要求直接固定。
2. `key_averages()` 会将 Attention 的两次 `aten::mm` 合并。当前统计足以保留原始 trace，但不能单凭合并行确定 QKᵀ 与 PV 谁更耗时。四阶段分析需要从真实 trace 按每次调用的顺序、栈或相关 external id 分别关联两次 mm 与其 GPU kernels；无须改写 Attention 算法。

## 8. 已生成的本地数值证据复读

只读检查主 agent 生成的 `evidence/correctness/local_softmax_cpu.json` 与 `local_attention_cpu.json`，未自行重跑。两者明确记录 `torch=2.15.0+cpu`、CPU 1 线程以及原定容差，属于本地调试结果，不能替代魔搭 CPU 正式实验或任何 GPU 结论。

- Softmax：16 项全部符合记录中的判定。100×5000 的 naive 最大绝对误差 `4.6566128730773926e-09`，Online 为 `2.2351741790771484e-08`；Online 行和最大误差 `3.2782554626464844e-06`，仍低于预先固定的行和容差。
- Attention：9 项无失败元素、形状/dtype/device/有限性均符合，零 Q 权重均匀。三档长度最大绝对误差分别为 `3.2184595927242654e-07`、`3.412128456448116e-07`、`2.0839328479516084e-07`，最大误差/逐元素容差比均小于 1。

上述数字是对已有真实检查产物的复读；没有 GPU 数据、正式云端测量或截图时，不能把本记录扩大解释为完整交付通过。

## 9. 字段兼容、云端运行与导出入口复核

第三次仅复读 `profile.py` 的字段兼容/FP32 修改及 `run_cpu.sh`、`run_gpu.sh`、`export_results.py`，未运行性能或更改实现。魔搭 CPU 启动仍需用户完成验证，尚无正式云端结果。

- `profile.py:107,116` 已显式指定 `torch.float32`，第 7 节第 1 项意见已处理。
- `profile.py:34–45` 以实际 Event 对象的属性决定 `device_time_total` 或 `cuda_time_total`，相应 Self 字段同步选择；`56,72` 在摘要保留实际字段，并用同一字段排序设备表。归一化后的内部 JSON 字段继续统一为 `device_total_us`，不会将字段兼容警告误当成 GPU 数据缺失。
- 原始 kernel 累计仍来自 Chrome trace 事件，因此字段兼容变更没有改变有效带宽分母的统计单位。
- 两个 shell 入口均设置 `set -euo pipefail`，切换到 A3 后串行执行，`tee` 同时保留实际命令和 stdout/stderr，失败可以向上返回；没有后台并行测量或远程发布操作。
- CPU 入口顺序为环境、两类 CPU 正确性、CPU 主 profiling；GPU 入口顺序为环境、三类 CUDA 正确性、四组 Softmax、三个 Attention 长度。每条命令和产物路径明确，不会将本地调试输出覆盖成魔搭结果。
- `export_results.py` 将 A3 中现有源码与证据按相对路径写入 ZIP，排除缓存、pyc 和已有 zip；检查目标不在 A3 内，避免递归打包；打印归档 SHA256。原始结果保持不动。

导出工具本身仍不生成逐文件清单/哈希，最终审查包需要另存 manifest 以满足任务要求。它只强制 ZIP 位于 A3 外，最终交付时还必须明确选择整个仓库以外的路径。GPU 入口没有自动逐组下载功能，实际云端调度仍需在实验组之间及时回传已保存证据，不能等会话结束才下载。

Attention 的两次 mm 仍需根据真实 trace 分别归属、统计；合并的 `aten::mm` 行不足以独自回答四阶段瓶颈问题。Triton `shared=0` 兼容风险仍待真实 GPU 复现。上述项目均未被本次静态复读标为已经完成。

```text
3d874baee3e55fa3d118caf13fb27bdbb0c25c73c0a0c7315ad4f9e12df3aa9e  scripts/profile.py
0b50e48265dc7dea383ad36d0e03d7dea19b81b9dc95cf73b0060991bd7f9ced  scripts/run_cpu.sh
810f372dd47329e0601ed2bf4bea78d4f30100220472f2d615094bbca05a54cb  scripts/run_gpu.sh
110dc04f6d37acbb087f45d67c11e33804ea0eb9ca255550be277dce9556a155  scripts/export_results.py
```
