# P1 要求与执行状态

本表记录Goal2R的实际产物。旧阶段要求表保留于受审提交efb6259e7c662a706a57297bb016116b7412d92c，旧raw、停止和判定不回写。最终Engineering由外部实际GitHub验收决定，本表不自授PASS。

| 要求 | 实际产物/证据 | 执行事实 |
| --- | --- | --- |
| 老师1：三个接口、框架与优缺点 | src/autotuner.py；report第1题；framework.svg | TargetProgram、ConfigSpace、SearchStrategy；真实suggest/evaluate/observe截图 |
| 老师2：指定矩阵目标与原核 | original.c；matrix_multiplication.c；数值日志 | n4096/double/原初始化/六层循环/24尾块16不变；仅边界计时及必要元数据适配 |
| 数学正确性 | measurement/goal2r；reproduction/goal2r | 240小矩阵全元素、5ASan/UBSan、两项4096独立24点；最终完整4096退出0；不称checksum全量证明 |
| 老师3：全部20组合 | ConfigSpace；protocol_goal2r | s8/16/24/64/128×O0/O1/O2/O3；共同C11/Wall/Wextra；未扩大配置或合并O2/O3 |
| 老师4：完整Grid参照 | results/goal2r_reference；goal2r_summary/grid_summary.csv | 三轮各20，60有效样本；预热1、锚点3单列；观测最佳128/O3，接近项重叠 |
| 另外两自行实现基础搜索 | results/goal2r_comparison；report4(2) | 六主seed×Grid/Random/Greedy；共同参照评分，真实driver成本；共141基础搜索调用 |
| 单因素S3及配对 | comparison原始轨迹、48新面板；paired.csv | 同seed前六Random＋两候选新复核；总8；真实三组观察退化，不保留；不混S1/S2 |
| 固定Greedy起点 | results/goal2r_starts | 8/8/5/7调用，28合计；独立面板，不变多起点策略 |
| 追加及新seed | summary/additional_request.json；confirmation | 主完整REJECT不触发追加；S3留出NOT_REQUIRED；三个Random新seed24搜索＋15面板完成 |
| T1主域有限依据 | 初始六区间、8A/A、32正式检查、2最终检查 | RAW/QPC整数完整括界符合冻结阈值；辅助变化保存，不据其单独否决RAW；非绝对校准 |
| T2三层分开与可达判断 | 三运行模式、纯判据、两类独立审核 | 正确性不受辅助比值杀进程；退出/输出/参数/超时/资源/主域/归属保护保留；KEEP/REJECT/INC具体夹具及真实负结果 |
| 预算与旧费用 | resource_ledger；goal2r_costs；supplement规则 | 原48及3713.432874365秒不重置；520调用/57600秒硬上限；共享面板只计一次 |
| 干净检出与旧版本重算 | reproduction/goal2r | 首次目录准备失败保留；一行修复后254测试0skip；四冷构建及1完整4096；五版本45派生逐字节等 |
| 正式report/OS/CPU/内存/编译器/学生身份 | report.md；README.md | 老师1—4顺序；10245102410吴博闻；Ubuntu24.04.2/185H/15.42GiB/GCC13.3；完整表图与有限结论 |
| 六张正式图 | images；reproduction/goal2r/images.json | 框架SVG保留；五新实测/源码/运行图；实际逐张查看，运行图只裁空白 |
| 原生多代理及两种审核 | reviews/goal2r_*.md/json；三个actor control | 主控独占测量，实施与独立审核分开；方法设计被独立反例挑战；以raw复算结论 |
| GitHub与外部验收 | main正常发布；实际远端核对见最终交接 | 发布授权已给；不force/reset/覆盖输入；最终SHA核对后交接；不自授Engineering PASS |
| 教师分支及截止 | 原PDF；当前提示 | project01需自建，截止2026-10-28 24:00；此次不操作水杉，Submission NOT_READY |
| 范围与依赖 | 起点A1/A2 tree；历史hash；实际命令 | 无其他作业/全局服务/时间/WSL/电源变更；无新系统包、语言包或工具链 |

预定性能任务和完整新鲜运行已完成；最终成品独立审核及远端检查见相应新记录和最终交接。Engineering等待外部最终验收，Submission NOT_READY。
