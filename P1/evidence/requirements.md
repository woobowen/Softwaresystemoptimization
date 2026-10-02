# P1 要求与阶段状态

Goal1 原矩阵保留在受审提交 `3ac0c4688b964c873379d012cbcf09afb7ed0937`。本表区分已实现、先前实际成果和本阶段受阻工作，不代替外部 Engineering 最终验收。

| 要求 | 对应产物/证据 | 本阶段状态 |
| --- | --- | --- |
| 老师1 三明确接口、框架图、优缺点 | src/autotuner.py / report第1题 / images/framework.svg | 已实现；最终代码及图审核待记录 |
| 老师2 指定Matrix目标 | original.c原件188d011…、当前C cece4f…、kernel4005ab… | 原初始化/double/n4096/六循环/尾块保留；240小全元素、5san及四个大矩阵各24点实际通过 |
| 老师3 五s×四O共20 | ConfigSpace及所有协议，8/16/24/64/128×O0—O3 | 未扩大；24保留，末块16 |
| 老师4 完整Grid及分析 | reference_v1原60有效样本 / grid_summary.csv / report4(1) | 旧20配置实测保留；新20配置0有效，时钟BLOCKED |
| 老师4 另外两算法自实现与比较 | Random/Greedy及旧九真实搜索 / report4(2) | 旧结果按统一身份参照重评，未伪称新六块已执行 |
| 正式Markdown report.md、重点代码、图片 | report.md / src链接 / images六图 | 文稿已精简，最终图与连续全文审查待记录 |
| OS/CPU/compiler，用户memory；学生身份 | report顶部、environment实际记录 | 实际Ubuntu24.04.2/185H/GCC13.3/15.42GiB；学号姓名无班级日期字段 |
| project01需自建，截止2026-10-28 24:00 | 老师PDF、本提示要求 | 本阶段不操作水杉；后续提交要求保留 |
| 历史保护/固定版本可复现 | history_goal2 / reproduction/goal2 / README版本入口 | 已有三旧版本重算一致；新增RAW停止5c78049已冻结 |
| 真多代理/测量独占 | agents_goal2 / performance.lock / primary ledger / review记录 | 主控+三原生代理；正式窗口仅一个高负载目标 |
| 时钟、多区间A/A、M0/M1 | measurement/clocks、clock_followup、RAW stopped原ns | 原41矩阵诊断完成；新RAW八A/A首项冲突止，0有效，不授正式准入 |
| 新协议、全部目标预算与成本 | protocol_v2、protocol_raw_aa、resource_plan、resource_ledger | 520/16h硬限、原2%门；每真实失败/暖机/数值/复现计费 |
| 新完整20表、六主seed、共同确认 | reference_v2 plan、预定seed/面板规则 | BLOCKED / NOT_EXECUTED；不能以旧结果补齐 |
| Greedy四结构起点 | protocol/显式start参数与测试 | 接口正确性已测；真实起点面板NOT_EXECUTED |
| S3有限重复单因素闭环 | recheck6+2、optimization_goal2、literature_goal2 | 实现及回归已测；真实配对/选择/留出NOT_EXECUTED，无KEEP/REJECT |
| 问题修复及两类终审 | goal2_review_closure / reviews两个最终路径 | 常规软件问题已修并回归；钟域核心依赖受阻，最终终审待记录 |
| 干净复现/安全截图/完整图片视觉 | reproduction/goal2 / screenshots_goal2 / images_goal2 | 有限非依赖闭环进行中；fresh仅一次，仍受原live保护 |
| GitHub main阶段发布及实际SHA | 最终publication证据 | 内部终审后正常发布，不宣称最终Engineering PASS |
| 清理/依赖/范围 | environment/goal2_dependencies.json / A1A2 tree / protected hashes | 新系统/语言包/工具链/全局配置均0；仅精确删除旧下载包，用户输入保留 |

Goal2：PARTIAL（性能可比性依赖阻塞）。Engineering：IN_PROGRESS，等待实际GitHub外部FINAL_REVIEW。Submission：NOT_READY，未提交水杉。
