# A3 独立代码与公式复核

本记录由 `review_math_code` 子代理编写。只读检查实现、检查脚本、采样入口、教师六页 PDF、现有预检查和理论证据，仅写本文件。没有连接学校服务器、执行性能实验、安装依赖或改变 Git 状态。这里的静态结论不代替正式运行，也不决定最终 Engineering 状态。

## 阅读范围

首条命令为仓库根目录的 `ls -la`，确认已有 A1/A2/A3/P1/P2、AGENTS.md 和教师 PDF。全文阅读：

- `src/softmax.py`、`src/triton_softmax.py`、`src/attention.py`；
- `scripts/check_softmax.py`、`check_triton.py`、`check_attention.py`、`profile.py`、`perfetto_queries.sql`；
- 教师 PDF 全部提取文本，并查看第 5 页 Algorithm 3 的实际图片；
- `evidence/attention_model.md`、`performance/logical_models.json`、先前 `review_code.md`；
- 预检查的 `profiler_initialization.patch`、CPU 表和相关预检查统计。

## 核心实现

| 内容 | 静态结论 |
|---|---|
| naive Softmax | 五步顺序和表达式与教师一致；没有替换为融合 Softmax。 |
| Online Softmax | 初始化每行 `m=-inf,d=0`；列循环每次处理全部行；`new_m` 与旧 `m` 分开，`d` 的递推仍使用旧 `m`，随后更新 `m`；最终广播使用最终状态。对应 Algorithm 3，没有标量 `.item()` 或设备搬运。 |
| Triton kernel | 保留 persistent programs、行步进、8192 的正式 BLOCK_SIZE、mask、最大值/指数/求和/存储、8 warps、stages、warmup、资源与 occupancy、grid 计算。与老师相比，主要将设备属性延迟读取并移除了无作用全局变量，没有换算法或调优。 |
| Attention | 显式 QKᵀ、缩放、Softmax、PV；`q.shape[-1]` 是 dk，支持 Lq≠Lk 和 dk≠dv。K 的转置为视图。 |

当前单卡可见设备的使用前提下，没有发现核心公式或控制流的实际错误。Triton 的 `size_smem // shared` 原样继承教师代码，只有实际 metadata.shared 为 0 时才是兼容问题；本次没有实际编译，不将这种条件性风险写成已发生的失败。空行、空列或非浮点输入不属于本次要求。

## 正确性检查

Softmax 检查覆盖随机小矩阵、非二次幂列、单元素/单行/单列、同行相等、大幅度有限正负值和 100×5000；检查 shape/dtype/device、有限性、行和与 torch.softmax。Attention 使用相同 FP32 输入值转 CPU FP64 的稳定数学参考，覆盖非方形、dk≠dv、Q=0、长度 1 和三个分析长度。固定 `rtol=1e-4,atol=1e-6`，没有按结果放宽容差。

一个交付字段缺口：Softmax 的初始检查脚本只保存最大绝对误差和行和误差，用户明确要求 Triton 的最大相对误差。建议补充相对误差，明确近零参考值的处理（例如限定参考值大于阈值，另报近零区的绝对误差，或明确分母下界）。不需要改变通过判定的原定容差。

检查脚本的 `formal_100x5000` 输入在生成前已经消耗其他测试的 RNG，和 profile.py 从种子首次生成的性能输入并非同一矩阵。这不是正确性错误；性能对照应使用 profile.py 中相同种子的同一首个矩阵及其 SHA256，不能将检查用矩阵的标识冒充性能输入。

## 采样和统计

初始 profile.py 的边界整体正确：输入、传输、参考和目标函数首次编译在采样外；预热后同步；主 Softmax 各 200 次、Online 双方各一次、Attention 各 10 次；完整表保存不截断；先过滤 ATen/Triton 再按 CPU total / Device total 排序；完整 Softmax GPU 时间直接累加 trace 的 `cat=kernel,ph=X` 事件再除以调用数，不重复叠加 ATen 的父子归因。独立计时在 Profiler 退出后，每次调用前后同步，是包含框架提交与等待的完整墙钟延迟，须与 kernel 时间分列。

正式运行前应处理/检查：

1. 预检查实际验证过 `with_stack=True` 前先空跑一次 `with_stack=False` 的 Profiler，用于初始化 lazy imports；初始 profile.py 没有该修复。应复用已有成功机制，避免首次初始化栈进入正式采样。已向主代理指出。
2. `scripts/profile.py` 名称与标准库 `profile` 冲突，若依赖经 `cProfile` 导入该模块可能遮蔽标准库。静态阅读只能指出风险，不能声称已复现。改为更明确的采样脚本名可消除该命名冲突；若改名，必须同步入口和证据。
3. Attention 的两个 `aten::mm` 会被 key_averages 合并。必须从正式 trace 的每次调用顺序、External id/flow 等分别关联 QKᵀ 和 PV，再比较四阶段耗时。合并的 mm 总行不能单独回答哪一次矩阵乘最慢。
4. 统计最后须核对实际 kernel 类别、每种数量和正式调用数。naive 正式 kernel 总量必须覆盖五步全部 kernel，不能仅用 exp 的时间作全算法带宽分母。

SQL 中的 CPU 根事件集合排除了有其他 `cpu_op` 祖先的事件，避免 Python 和 ATen 父子层重复计数。对当前没有用户 annotation 的 CPU 路径，该和应与 Profiler 的 Self CPU 总和核对；在正式 trace 未产生前，不能先声称分母相等。SQL 的 `dur` 以 ns 计，`/1e9` 是秒，`/1e6` 是 ms，`/1e3` 是 µs。

## 公式独立复算

逐步逻辑访问合计：

```text
读：NM + (NM+N) + NM + NM + (NM+N) = 5NM+2N
写：N + NM + NM + N + NM = 3NM+2N
合计：8NM+4N
```

N=100,M=5000 时，读 2,500,200 元素，写 1,500,200 元素，共 4,000,400 元素；FP32 共 16,001,600 bytes。融合 Triton 的一次输入读取和一次输出写入为 4,000,000 bytes。这里沿用教师张量级模型，不额外计 argmax 索引、缓存或硬件事务。

时间为微秒时，`GB/s=bytes/(1000*time_us)`。分别用完整 naive 和完整 Triton 的单次 kernel 时间作分母，加速比为 `t_naive/t_triton`。根据逻辑流量得出的有效带宽不等于 DRAM 实测；只靠低于峰值不能严格区分计算受限和访存受限，超过峰值也可能来自缓存重用，不能改动真实数值来贴合预期。

Attention 每阶段输入计一次读取、输出计一次写入时：

```text
QKᵀ：4(Lq*dk+Lk*dk+Lq*Lk)
缩放：4(2Lq*Lk)
Softmax：4(2Lq*Lk)
PV：4(Lq*Lk+Lk*dv+Lq*dv)
B=4(Lq*dk+Lk*dk+Lk*dv+Lq*dv+6Lq*Lk)
F_matmul≈2Lq*Lk*(dk+dv)
```

系数 6 为 `1+2+2+1`，公式与四阶段源码相符。缩放及 Softmax 还有 O(Lq*Lk) 运算；以 matmul 主项除以上述字节数得到估算强度，不是完整操作精确计数或硬件测量。

| L，dk=dv=64 | matmul FLOPs | 逻辑字节数 | 主项 FLOP/Byte | 单个 L×L FP32 矩阵 |
|---:|---:|---:|---:|---:|
| 128 | 4,194,304 | 524,288 | 8.000000 | 65,536 B |
| 512 | 67,108,864 | 6,815,744 | 9.846154 | 1,048,576 B |
| 2048 | 1,073,741,824 | 102,760,448 | 10.448980 | 16,777,216 B |

一般时间复杂度 O(Lq·Lk·(dk+dv))；包括输入输出及注意力矩阵的空间 O(Lq·dk+Lk·dk+Lk·dv+Lq·dv+Lq·Lk)。等长等维时分别为 O(L²d)、O(Ld+L²)，额外注意力矩阵空间 O(L²)。L 扩大四倍，主要 FLOPs 和分数矩阵元素数扩大十六倍；时延比例要由正式结果判断。

## 复核内容标识

以下为本次初始阅读时的 SHA256，后续修改应由主代理重新复核受影响内容：

```text
1854aab2de72596243c0f76948cfea38a75226d6e8a01c3dcace99d2a5e6f5f1  src/softmax.py
44f02823b2a7599074ffb4d5a0b8ec151944fefe43b6640fea97dda04d0f9faa  src/attention.py
5f532a1d0038012f4873a8190bb6c1d05ea6bac010bfc7261711febf9d702bea  src/triton_softmax.py
d1b6ca949db5dd8b51b16d9ae2fe483117e6a9cfb756fbefd34a0b05908399dc  scripts/check_softmax.py
f5c78cf39cc6bf7e94aa5f44cde343c61ba953cb238fd86c97ab77752401381b  scripts/check_triton.py
b6c017d2409dad02317713c6a37c004cb01415be402e71acebab96b55c5684f0  scripts/check_attention.py
3d874baee3e55fa3d118caf13fb27bdbb0c25c73c0a0c7315ad4f9e12df3aa9e  scripts/profile.py
d2cd3d9d490a4e073fe182f2350f01c64d62d463a42a19e8280e6cd8f2ae5a6f  scripts/perfetto_queries.sql
```

正式结果、截图、README 和发布核对尚不属于本次初始静态复核结论。最终仍须由主代理完成真实运行和自审，再由 ChatGPT 对 GitHub 实际成果独立审核。
