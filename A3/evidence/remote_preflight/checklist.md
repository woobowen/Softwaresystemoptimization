# A3 Remote Preflight 清单

仅本次预检查；非正式 A3 实验。所有结论待真实执行更新。

- [x] 全文阅读六页 PDF（含第 5 页算法图片）并保护旧文件
- [x] Windows SSH 连接、身份、远端退出码
- [x] 系统、存储、配额、调度政策与两次 GPU 快照
- [x] 发现并只读复用 Python/PyTorch/Triton 环境
- [x] 小文件双向传输、SHA-256、短 CPU 后台作业
- [x] CPU/CUDA naive Softmax 正确性与同步
- [x] 教师 persistent Triton 原逻辑、小规模及 100×5000 单次
- [x] CPU/GPU Profiler、Triton trace、with_stack=True 调用证据
- [x] 4×32 Online 与小 Attention 基础算子
- [x] trace 回传、本地 Perfetto 实际解析和 SQL
- [x] 变更/下载/占用登记、总结、轻量审核包及最终 Git 状态

全部勾选指本次 Remote Preflight 的检查已执行。Perfetto 使用实际 CLI 解析与 SQL；GUI 未操作，trace 的非丢失 overlap warning 已保留说明。正式 A3、200 次采样和提交均未开始。
