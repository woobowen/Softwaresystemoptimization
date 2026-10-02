# Goal 2 实际角色与资源边界

开始时间：2026-10-02 13:29:47 UTC（北京时间21:29:47）。实际可用主控加三个原生子代理，未安装代理平台或启动嵌套执行器。

| 角色 | 原生任务名 | 文件责任 | 独立检查任务 |
| --- | --- | --- | --- |
| 主控、集成与测量 owner | `/root` | `experiment_v2.py`、`clock_diagnostics.py`、`clock_followup.py`、`host_clock_probe.py`、`safe_screenshots.py`及各自tests、C最小timer适配、`validate_target.py`、有限诊断job协议、当前计划、历史保护、报告/README、截图、复现和发布 | 接收并修复独立审核问题，不单独授予结论 |
| 方法、文献和分析 owner | `/root/measurement` | `measurement/design.md`、新协议、`literature_goal2.md`、`summarize_v2.py`及分析fixtures | 交叉审查非本人实现的核心与编排 |
| 搜索实现 owner | `/root/implementation` | `src/autotuner.py`、`test_goal2_search.py`、搜索测试日志；审核仅`goal2_method_analysis_review.*`及`goal2_experiment_report_review.*` | 检查非本人编写的实验、完整报告与图片 |
| 独立审核 | `/root/review` | 已创建的起点/核心/设计/runner审核；新增独有`goal2_analysis_review.*`、`goal2_followup_code_review.*`、`goal2_protocol_review.*`、`goal2_formal_clock_review.*`、`goal2_host_clock*_review.*`、`goal2_raw_timing_review.*`、`goal2_final_code_review.*` | 读真实代码、原始结果、协议、完整报告和图片；实际执行回归 |

所有文件只有一个修改 owner。建议通过消息送给 owner，由其修复后交回审核。代理消息不作为证据聊天归档；审核文件记录角色、对象、具体问题和回归。

初期主控给两条分析审核路径分配了重叠名称，发现一次MD覆盖后立即拆为上述独有路径，JSON迁移并恢复各自问题记录，不把覆盖的内容当作两份独立证据。

性能窗口由主控独占 `P1/.cache/performance.lock`，使用非阻塞 `flock`，第二个 owner 会实际失败。正式窗口中其他代理只做阅读、轻量文本分析和编辑，不编译、不跑批量测试、绘图或基准。短测试窗口顺序授权，测试不计入正式n4096调用，但保留真实工程成本。全局 `resource_ledger.jsonl` 是目标调用和受控时间的唯一总账；批次driver是其任务记录，不重复加总。

独立终审分代码/正确性和实验/报告两条路径。内部通过表示本阶段关口已检查，不是最终 Engineering PASS；最终验收由外部完成。
