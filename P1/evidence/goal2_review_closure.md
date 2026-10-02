# Goal 1 交接问题的 Goal 2 闭环

本阶段性能核心受阻，不能写成全部关闭。旧 raw、协议、派生结果和判定保持不变；报告中的旧结果按同一配置参照重新解释。

| 问题 | 影响、定位与处理 | 证据及实际审核者 | 状态 |
| --- | --- | --- | --- |
| C1 同配置跨时段误判 | 实现共同 T_ref(c) 身份映射，在线、外部确认、成本分账；同 seed130363 返回 s128/O2 的选择差严格为0，不以3.015102秒确认差判策略退化。正文旧三算法统一 g_ref，独立 A/A 原样保留 | identity_quality.py / results/identity_quality_v2；measurement 分析 fixtures、implementation 原60样本与九身份分数独立重算；最终 report review | 评价逻辑与正文已修；新共同面板实测受阻 |
| C2 时钟及成组变化 | 41次初始/追加矩阵诊断、Linux多钟/WindowsQPC两区间后，MONO正式预热及RAW首A/A先后触发完整first/previous 2%保护。RAW相对REALTIME目标/driver前值变化2.261197%/2.245563%；数值/单位/身份/计费复核正确，未确定宿主根因、未改服务 | raw_aa_result_review：review与implementation原ns独算；raw_aa_summary_v3；只读服务日志、QPC正文范围 | BLOCKED：正式可比性未建立，不扩门/删慢样本/校正旧成绩 |
| C3 旧门不可达 | 不复用5.6秒门；5%目标、2pp质量风险、10%最低成本节约及严重回归界限先固定。相同身份可检验效率，不同身份风险不支持则不能KEEP；合成同身份/退化/成本/不足/边界反例实测 | protocol_v2、raw_formal_design、optimization_goal2；method设计及review关口、实际规则测试 | 设计和代码关闭；候选收益/非劣实测受阻 |
| C4 种子/起点不足 | 六个预定新主seed、三个新确认seed、四结构起点与平衡算法次序已设计；保留原Grid次序，默认Greedy随机起点不变。不把旧三种起点推广为普遍优势 | protocol_v2 / resource_plan_v2 / current_plan；implementation接口及review设计实查 | BLOCKED：六组在线、新确认、起点面板未执行 |
| C5 报告冗长 | 按老师1—4顺序重写，去恢复/审核叙述与旧跨时段gap误判；只保留必要结果和限制，README明确版本入口。须连续全文终审，不能用词表代替 | report.md、README.md；implementation独立实验/报告最终review | 已精简；implementation连续全文及report/README实际重读完成，最终阶段审核见两类review（整体性能仍受阻） |
| C6 截图安全/视觉 | 旧TCP/-ac事实保留，不声称已遭访问。改为私有Unix/auth0600/-nolisten tcp，原生成功/失败/超时/SIGTERM清理测试真实通过；最终三截图使用同安全工具、六图逐张打开。ER9把查看脚本的准确常量改为实际字段派生后只重拍两图 | safe_screenshots.py、screenshot_cleanup_tests、screenshots_goal2 / images_goal2及viewer全文/输入SHA；review代码与implementation视觉两路径 | 已关闭：3张最终终端图、5次安全拍摄全部清理，6图实际打开；ER9新两图已由两审核角色重新打开，见最终终审与visual_addendum |
| C7 历史版本依赖 | 431受保护文件清单；固定3ac九数据两图、2fc七数据、c247十一数据精确重算。RAW停止保存匹配5c78049及407行快照，回退后只在该版本重算，不删hash检查/改旧header | history_goal2、reproduction/goal2各comparison；review独立407行成本及10输入/7派生SHA重算 | 已关闭：3ac/2fc/c247逐SHA重算；fixed5c RAW7派生全等；431保护终检不变。a39十CSV及非身份JSON全等，仅中间分析器SHA差明确记录 |

C1/C3修复机制不等于真实对照完成，C2/C4仍是核心BLOCKED。干净221/19与四冷通过，唯一fresh n4096被原live guard止为PARTIAL；代码交付审核不授予性能准入或最终Engineering PASS。
