# A3 正式测量协议

输入为老师 PDF 共 6 页（SHA-256 见 environment/local_formal.json）。本轮明确授权学校服务器替代魔搭计算、全部 A3 实验、自审后 GitHub main 发布；不提交水杉。

- 唯一调度者：主代理。子代理 review_math_code 只复核代码/公式，perfetto_browser 只处理本地真实 UI；均不运行远端实验。
- 远端 /home/bwwu/lab/SSO_A3；复用 /data/bwwu/envs/tiger/bin/python，不安装研究环境依赖。
- 每组 GPU 实验前保存 nvidia-smi 状态；所选 UUID 存在计算进程时停止。当前选 GPU-dfff0e95-1db6-e2f4-3431-55bb852fa0ae → 进程 cuda:0。同一比较不换卡。
- 所有输入 FP32；CPU Generator seed=10245102410；相同 Softmax 形状由同一生成过程产生，metadata 保存值的 SHA-256。CPU 线程固定为 1，OMP/MKL 线程 1。Attention matmul precision=highest、TF32 disabled。
- CPU naive、GPU naive、Triton：100×5000，预检查正确性、5 次预热（Triton 编译在外），200 次正式调用，with_stack=True。先空 Profiler 初始化再正式采集；输入创建与传输不计入。
- Online 与其 naive 对照：同一 100×5000 输入；均正式 1 次、with_stack=False，保留完整 trace；另均无 Profiler 同步计时 5 次，分别报告，不混合带宽计算。
- Attention：L=128/512/2048、dk=dv=64；每档 10 次正式调用、with_stack=True；另无 Profiler 同步计时 5 次。L512 为主要分析规模。
- Profiler 原表全部保存；筛选 aten::* 与 softmax_kernel 后按 CPU total 或 device total 排名。父子 total 不相加作为耗时总和。
- GPU 单次完整调用时间 = trace 中实际 kernel 事件 dur 之和 / 调用数；CPU launch/Python/同步不混入。核对 kernel 数与 flow/External id，Attention 两次 mm 分开按时间顺序/关联统计。
- 带宽为逻辑字节数/完整调用 GPU kernel 时间；naive 16,001,600 B，Triton 4,000,000 B；峰值参照 NVIDIA RTX4090 官方 1008 GB/s。它们不是硬件 DRAM 流量计数，低于峰值不能单独证明计算受限。
- CPU SQL 分母采用无 cpu_op 祖先的 cpu_op 区间并与 Profiler Self CPU 总和核对，避免 Python/ATen 嵌套重复。
- 固定 FP32 容差 rtol=1e-4、atol=1e-6；不为失败任意放宽。相对误差明确以 max(abs(reference),1e-6) 为分母。
- 结果允许变快、变慢或无法严格判定；不预设性能结论。若实验失败，保留原记录，定位后最多三种实质不同修复路径。

## 正式前修正

已复用预检查已证实的 lazy Profiler imports 初始化；将 profile.py 改名 profile_workload.py 防止标准库遮蔽；补相对误差与 UUID 元数据。核心算法无性能优化/自动调优。

## 本地 Git 安全集成

main 安全快进至 origin/main d56ed615d3adb772380a3a25a2eb4aa57aeccf90。P2 原有 534 文件逐字节保留，唯一相异 manifest 仍作为用户未提交修改保留；未纳入 A3。备份及过程见 git_integration.json。
