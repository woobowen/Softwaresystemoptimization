# 补诊断分析边界

本说明在十二次新增样本结束前固定分析过程，不包含未来结果或安排选择。执行要求来自已冻结 [启动修复协议](../protocol_clock_followup_r1.json) 和 [有限设计](clock_followup_design.md)。原 [补诊断协议](../protocol_clock_followup.json) 与 plan 保留原身份；其真实 CLI 在任何矩阵启动前因缺少 runtime `protocol_path` 失败。修复只补启动字段与只读 `check` 入口，同十二个 job、顺序、2%规则及调用上限不变，不增加第二批诊断额度。目标执行仍需真实 `check` 的零调用输出、成本和独立身份审核。

1. 初始 raw 必须在固定提交 `2fc0c334039bb6696c4d83acbe029ce65ca66ab9` 的匹配 runner22a839、summary963524 中重新分析，输出写入忽略缓存。当前 runner7fa4c97 不能通过删 SHA 检查读取旧批次。联合分析读取这个固定初始派生的实际样本，再读取新协议/新 plan 验证过的补充 raw；两批身份并存。
2. 新增十份正式 journal 按 frozen common_metadata、真实 stdout、PID、三域整数 ns、预算与步骤独立重放。两份直接内核诊断按原 multi-clock identity 和二进制、三行真实 stdout、原始四域 ns 验证；它们只参与诊断，不成为正式秒数样本。
3. 每任务 `clock_trace` 的全文件 SHA 与唯一实际 global end 对齐。start/interval/end 均从原始 ns 重算 prefix/local；完整 driver 从 global start/end 重算，formal process 从其 journal 起止重算，diagnostic kernel 从 stdout 原始起止重算。核对保存的 elapsed/q/first-previous changes/conflict；不能只相信布尔标志或图片。CPU 范围按相应原始字段单列。
4. 分来源、同 boot、正常结束、已知调用的完整区间分别重算首个及前一个 q，原 interrupted 不进入 completed baseline。所有实际 prefix、局部和完整区间都呈现，不能仅输出未触发的片段。`abs(q_i/q_j-1)>0.02` 原阈值不变；cost_complete 与 clock_healthy 是两个不同判断。
5. 两个 replacement 必须分别对应原 interrupted M0-M-B3 和未启动 M0-F-A3，且目标/二进制/配置完全一致。只为原缺失评分槽提供新有效样本；原失败行仍在全部 measurements 和成本中。禁止替换已有有效慢样本。重新计算原 D/P/rho 时另注明等待间隔和连续性被打断；后八次独立 A/A 另外给四对差、A/B 中位数和两档排序，不混成新增随机种子。
6. 任何完整同来源 q 也超限，或两档排序冲突，正式测量关保持未关闭。仅前缀超限、完整区间均符合原 2% 条件且排序可分时，才提交“完整区间对完整区间”最小正式规则修订的代码/方法审核。正式须逐目标进程和完整 driver 分别 hard-stop，不用八调用平均掩盖单次问题；summary 存在也不能让 clock_conflict 的数据 KEEP。
7. 安排按原 D/P/rho 表决定，不预设 M1。rho 仍取原全部有效样本的 ceil(max(D,P))，不删初始 +13.7846% 单对。5%近优目标、2pp风险和10%效率门均不随 rho 放宽；若大 rho 阻止不同身份风险判断，结果是 INCONCLUSIVE。同身份质量严格0，实际成本路径仍可检验。

来源明确、数字/时钟/资源检查通过后再冻结正式 protocol_v2；本十二次的通过仅说明这一个有限诊断可分析，不等于整个 Goal 或最终工程验收通过。
