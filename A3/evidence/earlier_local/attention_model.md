# Attention 四阶段逻辑模型

本文件只记录由源码推导的计算量、空间和逻辑访存，不含性能实测结论。

源码：[`../src/attention.py`](../../src/attention.py)。

## 尺寸与四阶段

设 `Q: Lq × dk`、`K: Lk × dk`、`V: Lk × dv`，输出 `O: Lq × dv`。
分数矩阵 `S` 和概率矩阵 `P` 的尺寸均为 `Lq × Lk`。

| 阶段 | 主要读取 | 写入 | FP32 逻辑字节数 |
|---|---|---|---:|
| `S = Q @ K.T` | Q、K | S | `4(Lq*dk + Lk*dk + Lq*Lk)` |
| `S = S / sqrt(dk)` | 未缩放 S | 缩放后 S | `4(2*Lq*Lk)` |
| `P = softmax(S)` | 缩放后 S | P | `4(2*Lq*Lk)` |
| `O = P @ V` | P、V | O | `4(Lq*Lk + Lk*dv + Lq*dv)` |

`K.T` 是视图；本模型不为转置单独分配张量或增加一次全量复制。
每阶段输入只计一次逻辑读取、输出只计一次逻辑写入，忽略矩阵乘内部分块访存、Softmax 内部额外访问及标量转换等操作。
因此

```text
B_logical ≈ 4 * (Lq*dk + Lk*dk + Lk*dv + Lq*dv + 6*Lq*Lk) bytes
```

系数 6 分别来自：第一次矩阵乘写入 1、缩放读写 2、Softmax 读写 2、第二次矩阵乘读取 1。
它是分阶段逻辑模型，不能解释为硬件实测 DRAM 流量。

## 时间、空间与计算密度

两次矩阵乘计一次乘加为 2 FLOPs：

```text
F_matmul ≈ 2*Lq*Lk*dk + 2*Lq*Lk*dv
         = 2*Lq*Lk*(dk+dv)
```

缩放、行最大值、指数、求和与归一化另外需要 `O(Lq*Lk)` 操作；指数的实际成本不能等同于一次加法。
总时间复杂度为 `O(Lq*Lk*(dk+dv))`。

包括输入、输出及注意力矩阵的总空间复杂度为
`O(Lq*dk + Lk*dk + Lk*dv + Lq*dv + Lq*Lk)`。
不计输入、输出时，显式物化注意力矩阵所需的额外空间为 `O(Lq*Lk)`。
当 `Lq=Lk=L` 且 `dk=dv=d`，分别化为 `O(L²d)` 和 `O(Ld+L²)`。

计算密度 `I = FLOPs / bytes`，单位为 FLOP/Byte。
以两次矩阵乘的 FLOPs 主项除以上述逻辑字节数得到估算值；该数值省略了 Softmax 与缩放的操作数，不能代替硬件计数器测量。

对于 `L=512, d=64`：

```text
F_matmul = 2*512*512*(64+64) = 67,108,864 FLOPs
B_logical = 4*(4*512*64 + 6*512*512) = 6,815,744 bytes
I ≈ 67,108,864 / 6,815,744 = 9.846153846 FLOP/Byte
```

## 三档长度的内存估算

以下统一为 FP32、`dk=dv=64`，1 MiB = 1,048,576 bytes。
此处只估算张量数据，未包括 BLAS 工作区、allocator 保留内存、CUDA 上下文和整个进程占用。

| L | 单个 S/P | S 和 P 合计 | Q/K/V/O 合计 | Q/K/V/O 与 S/P 合计 | 四阶段逻辑流量 | 两次矩阵乘 FLOPs | 主项计算密度 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 65,536 B = 0.0625 MiB | 0.125 MiB | 0.125 MiB | 0.25 MiB | 524,288 B | 4,194,304 | 8.000000 FLOP/Byte |
| 512 | 1,048,576 B = 1 MiB | 2 MiB | 0.5 MiB | 2.5 MiB | 6,815,744 B | 67,108,864 | 9.846154 FLOP/Byte |
| 2048 | 16,777,216 B = 16 MiB | 32 MiB | 2 MiB | 34 MiB | 102,760,448 B | 1,073,741,824 | 10.448980 FLOP/Byte |

该函数不进行反向传播。缩放是非原位操作，赋值期间旧 S 和新 S 会短暂同时存在，之后旧 S 可以释放。
第二次矩阵乘时，局部变量仍保留缩放后 S 与 P；上表的合计与这一张量集合相对应，实际峰值分配应另用内存 API 测量。
L 每扩大 4 倍，注意力矩阵和矩阵乘 FLOPs 主项扩大 16 倍，输入、输出张量仅扩大 4 倍。
是否表现为相同比例的时延变化，必须由后续实测判断。

## 正确性检查入口与精度

```bash
python scripts/check_attention.py --device cpu --threads 1 --output evidence/correctness/attention_cpu.json
python scripts/check_attention.py --device cuda --threads 1 --output evidence/correctness/attention_cuda.json
```

需在 A3 目录、已安装 PyTorch 的环境中执行。
脚本使用固定 seed `10245102410`，CPU 生成同源 FP32 输入，设置 `torch.set_float32_matmul_precision("highest")`。
参考结果在 CPU 使用相同输入值转为 FP64，并显式稳定指数归一化；零 Q 则使用 V 的行均值作为独立性质参考。
固定逐元素容差为 `atol=1e-6, rtol=1e-4`，保存最大绝对误差、最大容差比、失败元素数量与形状/dtype/设备/有限性检查。
覆盖非方形、零 Q 的均匀权重、单元素长度和三档正式尺寸。

实现阶段本地尚未安装 PyTorch，未在本文件中预填任何运行结果；通过与否以检查脚本的实际 JSON 为准。

精度 API 参考：[PyTorch `set_float32_matmul_precision`](https://docs.pytorch.org/docs/stable/generated/torch.set_float32_matmul_precision.html)。
官方文档将 `highest` 定义为内部使用 FP32，并说明 CUDA 矩阵乘对应关闭 TF32。
没有混用 `fp32_precision` 与 `allow_tf32` 两套配置。
