# 十二次补诊断执行器独立代码审核

审核者 `/root/review`；作者 `/root`。方法关另见 `goal2_design_review.md`，不重复占用其他角色文件。修复后代码与独立回归关通过；仅在精确新协议/身份冻结后允许本次十二次补诊断，不批准正式比较。下文保留初稿发现、修复及真实回归过程。

本次读取后记录的源码 SHA：followup `5694e73c6b61fcbf0d06eed72dde7bccaf9544ebe0e90426b4eede3e88ea7bfd`，runner `7fa4c97cac4b749ef249489d909cb79f7c8021f6bdfc1e5e1ea486c2ead5e439`。这仍是 owner 在编辑的初稿快照，不视为冻结版本。原诊断的匹配代码已保存在 `2fc0c334039bb6696c4d83acbe029ce65ca66ab9`，不修改原计划/header。

下表记录初稿发现与当时状态，最终修复/回归闭环在末节；它们不是当前未关闭问题。

| 问题 | 严重性、位置与证据 | 必要修正/回归 | 初稿状态 |
| --- | --- | --- | --- |
| F1 恢复只按任务标签和两个状态跳过 | 高，`main()` 的 `old` 分支未拒绝 `reason!=None`，未核对对应 task_start 的 command/journal/protocol 或既有 raw/clock trace。资源停止竞争中恰好 code=0 的任务可能在重启时被当作完整 | 对恢复核对唯一匹配 attempt 身份、无失败原因、原始有效 journal/多钟输出、完整 trace、时钟边界与实际成本，损坏/失败不跳过或免费重跑 | 已送作者，待修复/独立测试 |
| F2 多钟 elapsed_s 长度未核对 | 中，`matrix_interval()` 使用 zip 比较，空或短列表可能漏掉应比较的边界 | elapsed_s 严格四项，类型/有限/正值及每项原始 ns 差一致；加入空、短、多项损坏 fixture | 已送作者，待修复/独立测试 |
| F3 多 attempt journal 被整个重放 | 中，`complete_sources()` 对每个 task_end 都遍历整个 journal，若多 attempt 会重复计入早期/后续完整测量 | 按该 attempt 的 prior_measurement_starts 与实际新增数分段，或明确拒绝含多 attempt 的歧义输入；保留 first/previous 的真实先后且排除 interrupted | 已送作者，待修复/独立测试 |
| F4 新 timex 读取库身份未绑定冻结输入 | 高，`query_reader()` 只将本地 c/so 与可修改的本地 identity 比较；没有核对固定 QUERY/source、readonly_modes 或冻结 identity SHA | build 后把新 identity 路径与 SHA 绑定新协议，执行检查固定 QUERY SHA、modes=0、编译器及 binary 身份；元数据与源码一起改也须拒绝 | 已送作者，待修复/独立测试 |

方向上，该 observer 仅在精确 approved 十二次、formal_admission=false 下记录 q flag；默认正式路径仍执行原实时保护。三域整数 ns、约两秒局部与前缀、完整 driver/process/kernel 来源、只读 adjtimex、资源/倒退/非有限值/超时硬停和唯一 owned 清理皆有明确路径。仍须实际低成本 fixtures 验证这些路径，并检查恢复/身份/异常不旁路保护后才能放行有限补诊断。

完整 q 冲突须与成本已知分开：允许有限诊断采全样本不代表正式准入，也不代表该 summary 可支持 KEEP。后续正式源和协议必须另行审核。此初审没有编译、测试、GUI、矩阵运行或其他 owner 文件改动。

## 第一轮修复与独立回归

作者增加了 `completed_job()` 恢复检查、elapsed_s 严格四项、按 attempt 的 measurement_start 分段以及固定 QUERY/modes=0 和协议绑定新 query identity。2026-10-02 15:45:53.439–15:45:54.945 UTC，审核者按主控授权取得非阻塞独占 performance.lock，独立执行 12 项 `test_clock_followup.py` 与 19 项 `test_goal2_driver.py`：31 项全部实际通过、exit 0、无 skip。followup unittest 0.283 秒、外层 MONOTONIC 0.372650263 秒；driver unittest 1.053 秒、外层 1.132981526 秒。测试前后 followup `fca87ec…`、runner `7fa4c97…` 不变，n4096=0，锁已释放；全文与三域边界保存在本记录 JSON。

审核者还实际调用固定源码、固定 binary hash 匹配的只读查询：modes=0 返回正常，offset_unit=us、status=0、tick_us=9824；它只是本机状态观测，不证明服务根因。新 identity SHA `db9f230…`，固定 QUERY 源 `20ef2a6…`、so `3d176110…`；冻结协议须精确绑定该 identity。F2 与 F4 修复及相关独立回归已通过。

**F1 与 F3 仍需修复，31 项通过没有放行十二次**：

- F3 的切片使用 run_id 集合；真实同次搜索及恢复中的多次 trial/repeat 会共享 header run_id，因而仍会选中整个 journal，重复前后 attempt。当前 fixture 使用不同 run_id 没有复现真实契约。需用实际 start/completion 的 trial_id、repeat、PID/出现次序身份选择，并增加共享 run_id 反例。
- F1 的新恢复只互相比 task_end 和 clock_complete 派生字段，未从原始 driver/process/kernel 边界与当时前序 baselines 重算 complete_checks、q、conflict；若同时修改两份派生字段会被接受。须独立重算这些值并核对 resource_wall_s 等于原始三个域差最大值。新的 fixture 必须同时改两份 q/flag 并证明拒绝。

已交同一 owner 修正；后续只重跑这些新增/受影响测试与必要 driver 回归，不启动矩阵后再修身份漏洞。

## 最终有限补诊断代码关

F3 改为实际 `(run_id,trial_id,repeat,pid)` start/completion 身份，真实共享 run_id 与未来未完成第三项的 fixture 通过。F1 用 `complete_sources(before_attempt)` 取得当时前序完整参照，从严格验证后的原始 driver/process/kernel 区间重算 complete checks/q/flags、逐前缀/局部比率及资源最大值；同时修改 end/trace 派生值仍被拒绝。两项修复已读取和独立复核。

implementation 角色另提出 CF1：独立 timex/phase 字段损坏原先未必阻止恢复。owner 在 clock_complete 追加后计算全 trace SHA 写入 global end，恢复先校规范路径与 SHA 再重算；SHA 不写回同一被 hash 的 trace。单改 timex/phase，以及改两份派生值并更新 trace hash 的 fixtures 均实际拒绝。原中断/未知/其他 boot 排除、默认正式保护、硬 cap/timeout/倒退及 owned 清理未改变。

2026-10-02 15:52:30.448–15:52:30.824 UTC，最后版本在非阻塞独占 performance.lock 下独立运行 12 项 followup fixtures，全通过、exit 0、无 skip；unittest 0.302 秒，外层 MONOTONIC/RAW/REALTIME 为 0.375661655/0.379501476/0.375661923 秒。执行前后 source 不变，锁已释放，n4096=0。全部前一轮 31 项和后续受影响 12 项真实输出分别保留同名 JSON，未覆盖历史失败/修复证据。runner 19 项刚独立通过，runner 未再改动，没有无理由重复。

最终代码准入身份：

- executor `6c0283cbba357ff7027091ad1ed2f157d2b7ad17443da150694654a576c00221`。
- runner `7fa4c97cac4b749ef249489d909cb79f7c8021f6bdfc1e5e1ea486c2ead5e439`。
- followup tests `d2c2f1f21dc41d882c4f7772467f2aa31dbcef092892281d40d1277b9a80181d`。
- readonly query identity `db9f23021422f2b69ccbb3c216b942139e574d61a820671764e3b8b61d0e7552`，源 `20ef2a6…` 与 binary `3d176110…` 实核。

**代码关允许精确十二次有限补诊断，条件是 method 将上述 source、实际 query identity、最新设计 SHA 与方法/代码证据写入 approved/frozen 新协议并生成匹配新 plan**。现有 main 会拒绝未冻结或身份不匹配的输入。F1–F4/CF1 的代码问题及独立回归关闭；F4 的机器可读 protocol binding 尚需冻结后读取确认。只有 prefix q 超限记录并完成这一有限任务，2%完整检查仍保存；520/16h、1200s/编译60s、倒退/非有限/未知成本及锁保持硬边界。补诊断根因、完整 q 与 A/A/排序结果均待实际产物独立重算，不允许提前授予正式性能准入或 KEEP。未授予最终 Engineering PASS。

## 冻结协议及十二项 plan 实核

审核者随后实际读取 approved 协议 `02446a7f6d7047d5c4876665f0f0b991860c023b874ce53123bb9edf57fb62ed`（冻结时间 2026-10-02T15:55:01.963903+00:00）与 plan `a10f8bb4dd7a549ea06cae72a056f550beb8c506c90df8fcb91a4489a03e5de3`。目标/core/runner/executor/design/旧多钟 identity/新 readonly query identity 的全部 SHA 与真实文件字节一致，所有 approval evidence 路径存在。plan 的 12 jobs 与协议逐项完全相同，10 个普通 run、2 个 clock_matrix；2 replacement、2内核诊断、8新独立A/A，formal_admission=false，root/path/protocol/driver 身份正确。

F4 的 protocol binding 条件已实核关闭；**允许主控按该冻结 plan 执行且仅执行这十二次补诊断**。新的原始时钟/标签/成本和后续正式准入仍待结果审核。此次身份复核仅 stdlib 只读，无目标或编译调用；不修改旧协议/计划/raw。
