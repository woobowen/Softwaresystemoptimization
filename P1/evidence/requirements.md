# P1 Goal 1 requirement matrix

状态对应实际产物，不等价于最终 Engineering PASS。四批正式实验及独立原始数据审核已结束；最后产物审核、干净复现与发布仍待完成。

| 来源 / 条目 | 代码或文档 | 实测 / 证据 | 状态 |
|---|---|---|---|
| PDF 1(1) 目标接口 | src/autotuner.py TargetProgram | 真实四级构建、缓存/失败测试；reviews/code_review.md | 已实现；冻结代码只读终审已做，干净动态复现待结束 |
| PDF 1(2) 配置接口 | ConfigSpace | 20无重复、非法输入、s24检查 | 已验证 |
| PDF 1(3) 搜索接口 | SearchStrategy、统一Evaluator | Grid/Random/Greedy +预算/seed/平局/恢复测试 | 已实现；冻结代码与候选单因素已实查，干净动态复现待结束 |
| PDF 1 框架图、优劣 | report.md第1题、images/framework.svg | 与实际接口对应的图，实际渲染查看 | 已整理；完整报告/图终审进行中 |
| PDF 2 老师Matrix目标 | src/matrix_multiplication.original.c / matrix_multiplication.c | 原件SHA188d0111…、target_adaptation.diff、同源验证 | 已保留；small/sanitizer/full通过 |
| PDF 3 五s四O，共20 | ConfigSpace、协议space | [8,16,24,64,128] × O0..O3 | 正式20表每3有效，已独立重算 |
| PDF 4(1) Grid完整覆盖与分析 | experiment reference、report第4(1) | 20配置每3有效样本、预定3随机轮次；summary/grid_summary.csv | 实测与独立原始逐样本重算均已完成 |
| PDF 4(2) 自实现另两算法比较 | Random/相邻坐标Greedy、report第4(2) | 三基础算法在线多seed、共同确认和成本 | 选择/留出实际执行与全部原始逐值审核已完成 |
| PDF 提交1/2 重点代码/Markdown/图片 | report.md、src、images | 完整通读与relative link检查 | 报告/图/两截图已整理，最终通读及构建运行截图待结束 |
| PDF 提交3 OS/CPU/compiler、用户memory | environment/initial_environment.txt | 真实OS/kernel/lscpu/meminfo/GCC/Python | 已记录 |
| PDF 提交4 project01需自建 | current_plan.md | 本阶段不访问水杉、不创建分支 | 本阶段不执行 |
| PDF 截止 2026-10-28 24:00 | current_plan.md | 不加正式报告顶部 | 已记录 |
| Goal A 真多代理、滚动计划、owner | current_plan、capabilities.json、reviews | 主控+3原生线程；实际spawn限制已记录 | 主控+三子代理实际执行，独立两类终审继续 |
| Goal B 简洁可运行三接口/评估器 | src/autotuner.py | 框架31项（含原23+新增8）及实验/汇总23项 | 框架31项及实验23项已独立通过；阶段动态终审待做 |
| Goal C 同源全元素和full抽查 | scripts/validate_target.py | 128/129×5s×4O×6输入=240；独立另外240+5sanitizer；full两组24点 | 全部既定正确性用例通过，full明确是抽查 |
| Goal C 高O保留计算、目标差异 | kernel_assembly.txt、target_adaptation.diff | 原/适配O3实际汇编；单调timer边界相同 | 已核查 |
| Goal C 错误/预算/恢复 | tests/test_autotuner.py、test_experiment.py | compile/timeout/parse/nonfinite/SIGTERM/livegroup/cache、budget0/1/20、partial repeat恢复 | 框架独立31及实验23回归通过；源码只读终审已完成 |
| Goal D 20正式配置三重复基线 | results/reference_v1 | 60正式+warm1，20配置每3有效，失败0；median/range/MAD保留 | 60正式样本和20统计已逐项独立核对 |
| Goal E 三基础算法在线初评 | results/selection_v1 | 共同B8/r1、预定3探索seed、真正best-so-far与wall；另3返回确认 | 三基础×三seed及共同确认已实测并逐值独立重算 |
| Goal F 2021—2026原论文筛选 | literature.md | 原文必要章节/元数据/2025&2026检索/获取限制 | 已完成资料工作包 |
| Goal F 两单项闭环 | stratified / patience；协议acceptance | 共同Random基线、两个独立因素、KEEP/REJECT/INCONCLUSIVE | 两单项及9次有界诊断已实测并独立审核；均INC，无采用 |
| Goal G 留出seed确认、两类独立审核 | holdout_v1、reviews | 3新seed；代码审核≠实现；报告审核≠报告作者 | 三新seed实际34进程，0/3近优；两类冻结产物终审继续 |
| Goal G 干净隔离复现 | 最终reproduction证据 | 测试/构建/1真实4096/已存数据重生成 | 待最终冻结 |
| Goal H 报告、图表、真实截图、证据 | report.md/images/results/evidence | 原生xterm截图能力已确认，最终画面待捕获 | 数据图、SVG和两截图已整理，构建运行截图待复现捕获 |
| Goal H GitHub内部审核后发布 | Git main | 初始fetch/ls-remote匹配；当前仅本地基础checkpoint | 待最终发布和远端实查 |
| 根长期规则合并 | 根AGENTS.md | filename以老师为准；滚动规划/责任分离/自修复/单项优先/逐轮审核 | 已更新 |
| 实验完整性和边界 | protocol/current_plan/异常原始记录 | 不混模拟夹具、旧异常计时或策略组合；不改其他作业 | 持续遵守 |

新目标计时适配的旧数据不用于正式结论，见 [timing_issue.md](environment/timing_issue.md)。若最后仍有缺项，必须保留未完成状态并在交接中说明。
