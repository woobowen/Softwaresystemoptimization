# A3 正式统计独立复核

复核者：`review_math_code` 子代理。本文件复读已经回传的正式数据，通过本地 Python 标准库解析 trace、独立算术和 Perfetto SQL 交叉核对。没有访问服务器、运行 benchmark、修改原始结果或改动源码/README；只写本文件。结论不代替 ChatGPT 对最终 GitHub 文件的独立审核。

## 1. 输入与采样身份

实际读取 `cpu/cpu_naive.*`、`gpu/gpu_naive.*`、`gpu/gpu_triton.*` 的 metadata、statistics、完整 trace 和 Profiler 表，以及 `cpu/perfetto/cpu_queries.csv`。

- 三组主 Softmax 均为 FP32、100×5000、正式 200 次，5 次预热，`with_stack=True`。
- 三组种子均为 10245102410，CPU 生成后搬到目标设备；输入值的 SHA256 均为 `1a57e00830072c20cb012d9f68059ef143773be3786574eaa11e128e130456ed`。
- 两个 GPU 主实验均限制为 `GPU-dfff0e95-1db6-e2f4-3431-55bb852fa0ae`，trace 中逻辑设备 0、stream 7；设备记录为 RTX 4090、SM89、128 SM。
- Python 环境记录 torch 2.6.0+cu124、CUDA runtime 12.4、CPU 单线程，FP32 matmul precision=highest、TF32=false。
- 三组源码哈希一致，核心实现与前次独立代码复核一致；采样入口已更名 `profile_workload.py`，补充懒初始化、相对误差与 UUID 元数据。受影响部分已再次全文阅读。

trace 的独立 SHA256：

```text
574a0f1d541567265eced80464250d1018e6be458fa324b52d8e0e986445581b  cpu/cpu_naive.trace.json
c03f3057754cbe0d9747dd56fc3f56cf435f4e7353cc2f60932aad406bc19040  gpu/gpu_naive.trace.json
56568915a3cff1e0ed0ac4057bdc83a4c3e18167cfc734501d1d8c67fb5bd066  gpu/gpu_triton.trace.json
```

## 2. CPU 排名与 SQL

独立筛选全部 `aten::*` 行，再按 CPU total 降序，结果与 statistics 和原表一致。百分比分母为 Profiler 全部 Self CPU 之和 264.485312 ms，未累加嵌套 total。

| 算子 | 200 次 CPU total | CPU total % |
|---|---:|---:|
| aten::max | 98.112155 ms | 37.095502% |
| aten::exp | 49.893072 ms | 18.864213% |
| aten::div | 48.902566 ms | 18.489710% |

完整 CPU trace 含 4600 个 cpu_op 事件；五个主算子各出现 200 次。额外事件为 slice/unsqueeze/as_strided 及归约相关视图/填充操作，不是额外 Softmax 调用。

独立用 per-thread、时间包含关系求无其他 cpu_op 祖先的根区间，得到 1800 个根区间、总和 264.485312 ms，与 Profiler Self CPU 总和相差约 1e-10 µs（浮点舍入）。全部 cpu_op dur 简单求和为 268.688914 ms，全部 Python slice 的和更大，二者均不是正确分母。

另实际执行以下 Perfetto 查询（CLI v59.1），返回退出码 0：

```sql
SELECT COUNT(*) AS calls,
       printf('%.11f', AVG(dur)/1e9) AS avg_seconds_exact,
       printf('%.6f', SUM(dur)/1e6) AS total_ms
FROM slice
WHERE category='cpu_op' AND name='aten::exp';

WITH roots AS (
    SELECT s.* FROM slice s
    WHERE s.category='cpu_op'
      AND NOT EXISTS (
          SELECT 1 FROM ancestor_slice(s.id) a
          WHERE a.category='cpu_op'
      )
)
SELECT COUNT(*) AS root_calls,
       printf('%.6f', SUM(dur)/1e6) AS root_total_ms
FROM roots;
```

实际输出为 `200,"0.00024946536","49.893072"` 和 `1800,"264.485312"`。因此老师指定 SQL 对应平均 CPU total 时间，即 0.00024946536 s = 249.46536 µs；总时间 49.893072 ms，占比 18.8642127696%。CLI 默认 CSV 的浮点格式只打印六位小数，原输出的 0.000249 是显示精度，不能据此改成 249 µs。

trace 中首个 aten::exp 的祖先依次包含 built-in exp、`softmax.py(6): naive_softmax`、采样 lambda、main 和 module；源码对应关系来自实际栈，非推测。

## 3. GPU naive 排名与完整 kernel 聚合

CPU 排名分母为该 GPU Profiler 的 Self CPU 总和 23.760553 ms，包括 CPU runtime 的自身时间；不是 kernel 时间。

| 算子 | CPU total | CPU total % |
|---|---:|---:|
| aten::max | 7.919943 ms | 33.332318% |
| aten::sum | 4.094350 ms | 17.231712% |
| aten::sub | 3.421713 ms | 14.400814% |

GPU 排名按 Device total，分母为实际 kernel 时间总和 6.101630 ms：

| 算子 | 200 次 Device total | GPU 时间占比 | 每次 kernel 平均 |
|---|---:|---:|---:|
| aten::max | 3.032293 ms | 49.696442% | 15.161465 µs |
| aten::sum | 1.566347 ms | 25.670960% | 7.831735 µs |
| aten::div | 0.556635 ms | 9.122726% | 2.783175 µs |

剩余 sub、exp 分别为 0.543786 ms、0.402569 ms，单次 2.718930 µs、2.012845 µs。五者总和严格对应 6.101630 ms，单次完整 naive Softmax 为 30.508150 µs。没有将某个归约/exp kernel 时间当作完整计算时间。

从 trace 直接计数为 1000 个 `cat=kernel,ph=X` 事件，五种主 kernel 各 200 个；全部 1000 个 kernel 的 correlation 均有且只有一个对应 launch，两集合无差异。ATen 的 External id 将每个 launch 关联到相应 max/sub/exp/sum/div，聚合值与 Device total 相符。未把 ATen 和底层 kernel 再次相加。

实际 max/sum 的 grid 为 `[7,1,1]`、block 为 `[32,16,1]`，对 128 SM 的设备并行规模很小；这支持讨论小输入和归约并行利用率，不能仅据此宣布某种硬件资源已经饱和。

## 4. Triton 与有效带宽

Triton trace 直接计数为 200 个 softmax_kernel，总时间 781.126 µs，单次完整计算 3.905630 µs。全部 200 个 kernel 都有对应 `cuLaunchKernel` correlation，没有额外 ATen 计算 kernel。实际 grid `[100,1,1]`、block `[256,1,1]`，metadata 显示 80 registers/thread、32800 bytes shared memory，与 persistent/8 warps 的实现吻合。

| 指标 | naive | Triton |
|---|---:|---:|
| 单次完整计算 kernel 时间 | 30.508150 µs | 3.905630 µs |
| 每次 kernel 数 | 5 | 1 |
| 逻辑访问量 | 16,001,600 B | 4,000,000 B |
| 有效带宽 | 524.502469 GB/s | 1024.162555 GB/s |
| 相对 1008 GB/s | 52.033975% | 101.603428% |

独立算式为 `bytes/(1000*time_us)`；kernel 时间比 7.811326。再次查看 NVIDIA 官方 [Ada GPU Architecture V2.02](https://images.nvidia.com/aem-dam/Solutions/geforce/ada/nvidia-ada-gpu-architecture.pdf#page=30)，Appendix A 表中 RTX 4090 的参考带宽确为 1008 GB/s。

Triton 逻辑有效带宽略超 DRAM 峰值不表示 DRAM 实际超出规格。测试反复使用同一 2 MB 输入，缓存可能参与；当前计算的是源码逻辑字节数/kernel 时间，未采集 DRAM 硬件流量。不能强改数值以限制为 100%，也不能仅凭这两项百分比严格认定访存受限或计算受限。融合减少中间张量和 launch 数的机制可由代码及 trace 支持。

## 5. CPU→launch→GPU 时间关系

naive 和 Triton 所有计算均位于逻辑 device 0 的 stream 7；从 kernel correlation 回查 launch，没有缺失。naive 的 launch 开始到 kernel 开始中位间隔约 7.455 µs，Triton 约 9.885 µs（原始 Chrome ts 为 µs）。这些是对应事件开始点之差，不是单独测得的调度器延迟。

少量 kernel 在其对应 CPU launch 调用返回前已经开始（naive 7 个，Triton 3 个），实际 trace 支持 CPU/GPU 可重叠、异步提交的解释。CPU 函数时间既不等于 GPU kernel 时间，也不能代表设备已经完成。正式区间结尾有同步，但每次五步之间没有显式同步。

## 6. kernel 加速与端到端延迟须分开

关闭 Profiler 的独立同步单次调用五个样本（单位 µs）：

```text
naive: 375.049, 134.425, 123.194, 133.998, 119.596
Triton: 437.074, 153.361, 131.088, 127.075, 123.233
```

中位数分别 133.998 µs、131.088 µs，比例仅 1.022199。样本量少，双方首个样本偏高，不能据此证明稳定的端到端显著加速，更不能将 7.811326 的 kernel 时间比称为端到端加速比。老师 Triton 包装每次仍执行 warmup/资源查询相关路径，CPU 成本在这些完整调用里保留；不得为了得到更好数字替换实现。

目前以上主 Softmax 统计与原始证据一致。

## 7. Online 正式完整尺寸对照

追加读取 `online/online_naive.*` 与 `online/online.*` 的完整 trace、metadata、statistics。双方均为 FP32、100×5000、相同上述输入 SHA256 和 GPU UUID，各正式一次、5 次预热、`with_stack=False`；并未拿小规模诊断 trace 替代完整递推。

原始 trace 独立 SHA256：

```text
d9124e238268c8ebe729fcb122f257c5bfe6119ff476a88b1c802bab1005aaeb  online/online_naive.trace.json
2ad3992637c6d0734d344ef27fd45265a300aac579869f47e61d805b214bfb40  online/online.trace.json
```

| 指标 | naive 对照 | Online |
|---|---:|---:|
| 正式完整调用数 | 1 | 1 |
| GPU kernel 数 | 5 | 35,005 |
| 原始 kernel 时间和 | 30.817 µs | 39,184.880 µs |
| 无 Profiler 同步调用五次中位数 | 0.126469 ms | 473.695438 ms |

原始 kernels 与 CUDA launch 的 correlation 集合一一相符，没有遗漏或重复。Online 的数量精确对应 `5000×7+2+3`：每列最大值、两次减法、两次指数、乘法、加法共七个 kernel；初始化 m/d 共两次 fill，最后广播减法、指数、除法三个 kernel。slice/select/unsqueeze/as_strided 是视图事件，不另计计算 kernel。

Online 对比 torch.softmax 的最大绝对误差为 2.2351741791e-8，相对误差（分母下界 1e-6）为 2.6749862616e-6，最大行和误差为 2.5629997253e-6，均符合原定固定容差，未放宽条件。

无 Profiler 的 Online 五个完整调用样本为 477.448069、473.695438、472.286069、476.216874、472.255787 ms，对照为 0.228425、0.140063、0.126469、0.122400、0.123107 ms；中位延迟比为 3745.545849。Online 明显更慢，不能以算法上的两遍输入读取推导出这个 eager 实现更快。列间 m/d 存在顺序依赖，逐列只处理 100 行数据，产生大量小张量和 launch；`x[:,j]` 还跨行使用 stride=5000 的视图，不能把它描述成连续按行读取。

这个对照里的 naive 单次 Profiler CPU `aten::max` total 为 2.989331 ms，明显高于前述 200 次主采样的单次 CPU 平均，存在采集启动影响；因此比较完整性能应采用单独同步墙钟样本，不能用两组单次 Profiler CPU total 代替稳定端到端比值。GPU kernel 时间与完整同步延迟也必须分列。

## 8. Attention 四阶段与三档规模

追加读取 `attention/attention_l{128,512,2048}.*` 的 metadata、完整 trace、statistics 和 `correctness/school_attention_cuda.json`。每档 FP32、dk=dv=64、正式 10 次、5 次预热、`with_stack=True`、最高 FP32 矩阵乘精度且 TF32=false，均在相同 RTX4090 UUID 上。每档 Q/K/V 输入 SHA256 分别保存，不把不同长度的输入说成相同矩阵。

独立 SHA256：

```text
e50da366d338bac0194a5127211be0c8a32636457f38fb658fd3cfde38549213  attention/attention_l128.trace.json
b414957be7b7c047155f4324c4cca0d113d77c14a8c51b0e2053bed8a6f98e2b  attention/attention_l512.trace.json
2e6adf72f3cd7677948ef2ea7d455918d6d04642676dfde5c614c96d87055dd4  attention/attention_l2048.trace.json
```

### 两次矩阵乘的归属

每档实际 CPU `aten::mm` 为 20 次，按每次 Attention 的先后顺序分 QKᵀ 与 PV。通过各 mm 的 External id 找对应 launch，再用 correlation 找 GPU kernel。这样将 splitKreduce 也归到发起它的矩阵乘，而不是假设每步只有一个 kernel。

| L | QKᵀ kernel 数/调用 | 缩放 | Softmax | PV kernel 数/调用 | 总 kernel 数/调用 |
|---:|---:|---:|---:|---:|---:|
| 128 | 2 | 1 | 1 | 2 | 6 |
| 512 | 1 | 1 | 1 | 2 | 5 |
| 2048 | 1 | 1 | 1 | 2 | 5 |

三个 trace 分别是 60、50、50 个真实 kernel，与 launch correlation 一一匹配。QKᵀ 与 PV 的 GEMM kernel 名分别带 tn、nn；实际出现的 cublasLt splitKreduce 同样计入对应阶段。没有漏算这些归约 kernel，也没有将父层 `aten::matmul` 和子层 `aten::mm` 的 Device total 相加。

独立累计并除以十次调用后的四阶段时间（µs/完整调用）：

| L | QKᵀ | 缩放 | Softmax | PV | 完整 kernel 时间和 |
|---:|---:|---:|---:|---:|---:|
| 128 | 5.0721 | 1.0115 | 1.6545 | 5.2512 | 12.9893 |
| 512 | 4.2401 | 1.3822 | 2.3649 | 5.6895 | 13.6767 |
| 2048 | 24.5057 | 9.3951 | 25.8752 | 24.3778 | 84.1538 |

主规模 L=512 中，PV 为最大阶段，占 41.599947%；QKᵀ 占 31.002362%，两次矩阵乘合计 72.602309%；Softmax 占 17.291452%，缩放占 10.106239%。这些比例与全部 kernel 和为分母，没有重复计入。

L=2048 中，Softmax 变成最大的单独阶段，占 30.747512%；两次矩阵乘合计仍占 58.088286%。因此不能一概写成所有长度始终由某一次 GEMM 主导，也不能将 512 的构成套到长序列。

### 完整延迟和规模结论

独立无 Profiler 同步调用中位数：

| L | 中位完整延迟 | 单个注意力矩阵 | 两次 GEMM 主要 FLOPs |
|---:|---:|---:|---:|
| 128 | 0.128631 ms | 0.0625 MiB | 4,194,304 |
| 512 | 0.114408 ms | 1 MiB | 67,108,864 |
| 2048 | 0.154027 ms | 16 MiB | 1,073,741,824 |

短输入的端到端时间不单调；五个同步单次样本都包含框架、提交与同步开销，且首个样本较高。理论上 L 每扩大四倍，分数矩阵和主要 FLOPs 增大十六倍，但 512→2048 的 kernel 时间比为 6.153078，墙钟中位比为 1.346296；不能声称已经测得平方比例时延。不同 kernel 选择、并行利用率及固定开销会影响有限规模下的增长；这些是解释方向，未由本次数据分别量化。

逻辑模型与第一个复核文件一致：L512 的 67,108,864 FLOPs/6,815,744 B=9.846154 FLOP/Byte；长序列带来二次物化矩阵和访存压力，不能将该逻辑强度称为实测 DRAM 强度。

### Attention 正确性证据

`school_attention_cuda.json` 的九种场景均通过固定 `rtol=1e-4,atol=1e-6`，包括非方形、dk≠dv、Q=0 与长度 1。全部场景最大绝对误差为 2.8438620206e-7，最大误差/逐元素容差比为 0.0642473464，小于 1；零 Q 权重均匀，输出符合 mean(V)。

三档性能输入另在 metadata 记录对应 FP64 参考的最大绝对误差，分别 1.6836359340e-7、9.5481049012e-8、1.7171422852e-7。它们与 correctness 脚本的随机输入不是同一批，不应将两个来源的误差数字混成同一个测试。Attention 输出可接近零，因此带分母下界的相对误差可能大于 rtol；通过判定仍是 `abs_error <= atol+rtol*abs(reference)`，不能只用最大相对误差单独判失败或声称纯相对误差全部小于 1e-4。

## 9. 复核结论与报告重点

已回传正式 CPU、GPU naive、Triton、Online、三档 Attention 的调用数、身份、核心时间和公式经独立解析一致。没有发现必须重做数值或正式性能实验的统计错误；原始数据未改变。

正式报告应保留三项关键区分：

1. Triton 约 7.811 倍是 kernel 时间比；完整无 Profiler 的两组五样本中位数接近，不能称端到端同倍加速。
2. 有效带宽是逻辑访问量估算，Triton 101.603% 不能解释为实测 DRAM 超规格，也不足以严格判定硬件瓶颈。
3. Attention 统计须合并同一 mm 的 splitKreduce、分开两次 mm，并如实保留短规模墙钟不单调；复杂度是理论增长，不是已测延迟拟合。

本文件只完成统计复核，不证明截图、README 链接、发布内容或远端回读已经完成，也不赋予 Engineering=PASS。
