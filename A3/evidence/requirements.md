# A3 要求矩阵

教师输入：根目录 HW3异构编程作业(1).pdf，共6页，SHA-256 `546edfed40e024ae4401af617628dbeadc404033f25e87ba097a1679d594db41`。全文及六页渲染图（含Algorithm 3和附录A）均已阅读。

本轮用户明确授权学校服务器替代魔搭计算，复用已审核环境，串行完成正式实验、源码、报告、真实截图、自审后直接发布GitHub main并回读。不提交水杉、不自行给Engineering PASS，不创建长期设计/计划文件。

| 题号 | 要求 | 实现文件（A3/下） | 实际结果与证据（evidence/下） | README位置 | 满足情况 / 尚存问题 |
|---|---|---|---|---|---|
| Step1 | 平台与实际环境 | scripts/environment.py | environment/school_cpu.json；environment/school_gpu.json；commands/remote_initial.txt；images/01-environment.png | Step1 | 学校环境完成并实际运行；魔搭Notebook未创建，按用户选择替代，老师是否接受该平台差异未确认 |
| 2.1 | 五步读写表与总计 | src/softmax.py；scripts/analyze_results.py | review/derived_results.json；review/independent_code_math.md | 2.1 | 完成：读2,500,200、写1,500,200元素，16,001,600B |
| 2.2(1) | CPU 200次、CPU total前三 | scripts/profile_workload.py | cpu/cpu_naive.{metadata,statistics}.json；cpu/cpu_naive.cpu_table.txt | 2.2(1) | 完成：max、exp、div；200次、单线程、固定输入 |
| 2.2(2) | 按读写和实际排名解释 | src/softmax.py | cpu/；review/independent_statistics.md | 2.2(2) | 完成；区分归约、指数与完整矩阵读写 |
| 2.2(3) | Self CPU与CPU total | scripts/perfetto_queries.sql | cpu/perfetto/cpu_queries.csv | 2.2(3) | 完成；避免父子total重复 |
| 2.3(1) | 真实CPU调用栈/源码 | src/softmax.py；scripts/capture_perfetto.py | cpu/cpu_naive.trace.json.gz；review/perfetto_cpu.json；images/03-cpu-perfetto.png | 2.3(1) | 完成：五步及视图操作真实GUI观察 |
| 2.3(2) | 指定AVG SQL/对应列 | scripts/perfetto_queries.sql | cpu/perfetto/；images/04a-cpu-sql-average.png | 2.3(2) | 完成：0.00024946536s，对应CPU time avg |
| 2.3(3) | exp总时间/比例，无重复分母 | scripts/perfetto_queries.sql | cpu/perfetto/；images/04b-cpu-sql-total.png | 2.3(3) | 完成：49.893072ms / 264.485312ms =18.864213% |
| 2.4(1) | GPU naive CPU前三及原因 | scripts/profile_workload.py | gpu/gpu_naive.statistics.json；images/05-gpu-profiler.png | 2.4(1) | 完成：max、sum、sub；明确CPU提交开销 |
| 2.4(2) | GPU前三及kernel | src/softmax.py | gpu/gpu_naive.{cpu_table,device_table}.txt；gpu/perfetto/ | 2.4(2) | 完成：max、sum、div；独立归约和除法 |
| 2.4(3) | CPU/launch/GPU时间关系 | scripts/perfetto_gpu.sql | gpu/gpu_naive.trace.json.gz；review/perfetto_gpu_naive.json；images/06-gpu-timeline.png | 2.4(3) | 完成；1000 kernel全部存在launch关联 |
| 2.5(1) | 教师persistent Triton、正确性/200次、融合分析 | src/triton_softmax.py；scripts/check_triton.py | correctness/school_triton.json；gpu/gpu_triton.*；images/07-triton-profiler.png；images/08-triton-timeline.png | 2.5(1) | 完成：BLOCK8192、8warps、occupancy/grid保留；200 kernel；7.811倍仅指kernel |
| 2.5(2) | 完整kernel时间、逻辑带宽/峰值与瓶颈判断 | scripts/analyze_results.py | review/derived_results.json；review/independent_statistics.md | 2.5(2) | 完成：524.502/1024.163GB/s，52.034/101.603%；逻辑估计不能严格二分硬件瓶颈，报告明确解释 |
| 2.6(1) | PyTorch真实在线递推、旧m顺序和稳定性 | src/softmax.py；scripts/check_softmax.py | correctness/school_softmax_{cpu,cuda}.json；online/online.metadata.json | 2.6(1) | 完成；完整输入最大绝对误差2.235e-8，无.item/NumPy/传输混入递推 |
| 2.6(2) | 完整尺寸对照、Profiler/Perfetto、调用/计算密度分析 | scripts/profile_workload.py | online/online*.trace.json.gz；online/perfetto/；images/09a-online-profiler.png；images/09-online-timeline.png | 2.6(2) | 完成：各1次完整profile、各5次独立计时；35005 vs5 kernel；无缩小输入替代 |
| Step3(1) | Attention实现和四阶段瓶颈 | src/attention.py；scripts/check_attention.py | attention/attention_l512.*；review/derived_results.json；images/10-attention-profiler.png；images/11-attention-timeline.png | Step3(1) | 完成：QK/PV用External id分开且包含splitKreduce；两MM合72.602% |
| Step3(2) | 一般形状内存访问模式 | src/attention.py | review/independent_code_math.md；attention/ | Step3(2) | 完成：四阶段表、转置视图、物化中间矩阵 |
| Step3(3) | 时间/空间复杂度、FLOP/Byte | scripts/analyze_results.py | review/derived_results.json；review/independent_code_math.md | Step3(3) | 完成：一般形状与等长；L512为9.846FLOP/Byte逻辑模型 |
| Step3(4) | 三档序列和长序列挑战 | scripts/profile_workload.py | attention/attention_l{128,512,2048}.* | Step3(4) | 完成：kernel12.9893/13.6767/84.1538us；同步延迟短输入不单调，未伪称平方实测 |
| 逐题报告 | 教师编号、身份、全部回答、自然简洁 | README.md | review/independent_report.md；review/self_review.md | 全文 | 完整连续通读、修正三处实际问题；最终措辞判断仍待外部审核 |
| 真实图片 | 13张来自真实xterm/Perfetto，最终数据一致 | scripts/capture_terminal.py；scripts/capture_perfetto.py | commands/screenshots.jsonl；review/perfetto_*.json；review/final_validation.json | 对应题目 | 完成：13/13链接与哈希正确；未使用预检查图冒充 |
| 原始证据 | 全部正式trace/日志/SQL可复算 | scripts/analyze_results.py | review/trace_manifest.json；commands/；cpu/；gpu/；online/；attention/ | 按题引用 | 完成：8份完整trace无损压缩，解压前后SHA核对 |
| GitHub发布/回读 | 仅A3正常提交main、不force、核对远端所有文件 | Git | review/github_verification.json | 不在正式报告写审核流程 | 已完成内容提交edba395的GitHub API回读：372文件blob全部一致，17份直接字节回读一致；回读记录随证据提交发布，最终HEAD/main再核对并在最终回复报告 |
| 最终审核/提交 | 外部审核与水杉边界 | 无水杉操作 | review/self_review.md | 不写入报告 | Engineering等待ChatGPT；Submission NOT_READY；未猜分支/提交水杉 |

## 限制

- Step1学校计算替代不等于魔搭平台操作已完成；报告直接说明实际平台。
- 有效带宽采用逻辑模型，不是实测DRAM；没有硬件计数器支持严格二分硬件瓶颈。
- 五次独立同步计时只用于本次小规模对照，不声称端到端显著性；完整样本保留。
- 原始预检查总结的READY和旧平台阻塞均为历史状态；本次用户已明确确认预检查审核PASS，正式结果位于本矩阵列出的学校实验目录。
