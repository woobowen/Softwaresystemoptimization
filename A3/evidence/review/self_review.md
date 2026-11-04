# A3 主代理完整自审

本记录针对学校服务器正式成果，不代替ChatGPT对GitHub实际文件的最终审核。Engineering只能进入FINAL_REVIEW，Submission仍NOT_READY。

## 实际分工与边界

- 主代理：原题六页通读、唯一远端作业调度、全部正式CPU/GPU测量、本地统一源码、传输/数值复算、终端截图、逐题报告、自审和Git发布。
- review_math_code：只读独立代码/公式、统计和报告审查，输出三个review文件；未连接服务器或运行benchmark。
- perfetto_browser：只在本地加载正式trace，实际操作官方UI并截图/保留provenance；未连接服务器或运行benchmark。
- 正式测量串行；所有GPU性能对照使用相同UUID。没有并行A3 benchmark、无关GPU负载或其他研究进程干预。

## 代码完整阅读

已连续阅读3个最终src文件、当前采样入口、正确性脚本、执行脚本、传输和结果复算脚本。naive保留五步；Online为按列同时处理N行的m/d递推，d计算使用旧m；Attention显式四阶段；Triton保留教师persistent/warp/stages/warmup/occupancy/grid。只对CPU可导入和输入约束做必要处理，没有新算法/调优框架。

核心源码与正式运行metadata的SHA完全一致。输入/搬运/首次编译/正确性检查/预热均在正式采样外；递推中无.item/NumPy/隐含搬运。CPU、CUDA、Triton/Attention实际执行均成功，5个作业退出0。保留原始统计，不修改scores或失败信息。

## 已发现并修正的问题

1. 复用预检查定位的Profiler lazy-import初始化修复：正式with_stack前空跑with_stack=False；原始诊断保留remote_preflight的patch/trace/log。
2. 将profile.py重命名profile_workload.py，避免标准库profile遮蔽；实际正式执行新入口。
3. 补最大相对误差（参考绝对值下界1e-6）、行和、UUID和输入SHA元数据，不放宽原定容差。
4. Attention两个mm不能直接混用聚合行回答四阶段：用External id/correlation分开QK与PV，splitKreduce归入发起它的mm；与独立复算完全一致。
5. 文档复读修正Softmax占比末位为17.291%、将100元素限定为递推kernel，并删除未经测量的实际计算密度断言；完整重读最终README。
6. 截图元数据标签改为真实“读取已保存结果”，未把展示cat/JSON的终端画面说成新benchmark；全部图片来自实际xterm/官方UI，非绘图模拟。
7. 安全Git快进前保留P2原有文件，逐字节恢复本地差异；本次仅提交A3，P2已有manifest差异和其他未跟踪文件不提交。
8. 截图工具的xterm路径改为PATH/显式参数，复用已有二进制而不硬编码其他作业目录；实际重新采集环境图，哈希未变。
9. 一次本地解包检查早于异步下载结束，因文件尚不存在退出；等待下载正常完成后按整体/逐文件SHA核对解包，没有启动重复远端作业或改动实验数据。

## 正确性与数据复核

5份正确性JSON共58项通过固定rtol=1e-4、atol=1e-6。Softmax包括随机、非二次幂、同行相等、大正负有限值和边界；Attention包括非方形、dk≠dv、Q=0、长度1、三档正式规模。性能输入还在各自metadata额外检查，不能把正确性脚本不同随机输入的误差混成同一个测试。

完整解析8份正式trace：CPU/GPU/Triton主实验各200次；Online对照各1次；Attention各10次。5组Softmax同输入SHA，所有GPU同UUID。所有计算kernel均有关联launch；按原始kernel事件求和，不叠加父子Device total；CPU SQL分母用非重叠cpu_op根区间且与Profiler Self总和一致。

7.811倍是完整Softmax的GPU kernel时间比；独立同步调用133.998/131.088us接近，不声称端到端同倍加速。1024.163GB/s是逻辑有效带宽，缓存可能参与，不是实测DRAM超规格。Online真实更慢并保留全部35,005kernel trace。Attention短规模同步延迟不单调，报告没有把理论L²增长伪称为实测拟合。一般形状、O空间与逻辑FLOP/Byte已经独立算术复核。

## 报告、图片与文件

README按教师原顺序覆盖Step1、2.1–2.6及Attention四问。主代理与独立代理均从头至尾连续读完，不只检查关键词；保持必要答案、技术解释和限制，去除内部流程叙述，无模板总结。

13张正式图片逐张打开检查，命令/界面/关键数值清晰，链接和哈希均核对。Perfetto5类trace实际加载，无error/data_loss；选中单个事件只用于时间线展示，统计仍使用完整采样。8份正式JSON完整无损gzip，解压SHA与原件一致。历史本地/预检查记录单独标明，未冒充正式结果。

必要脚本的AST/shell语法、数值复算、输入/源码身份、所有作业退出码、58项正确性结果、完整trace压缩哈希、13图来源、README相对链接、发布文件/凭据标记扫描通过，输出见final_validation.json。未安装新依赖、无系统配置改动，详见installation_log.json。

## 已知限制与外部重点

- 用户选学校替代魔搭：计算任务全部完成，但没有魔搭Notebook创建记录，不能声称原平台操作完成；老师是否接受替代需外部确认。
- 不具有DRAM硬件计数器证据，瓶颈不能仅用逻辑带宽比例强行二分；五次同步样本不支持端到端显著性结论。
- 请最终审核者重点检查README逐题内容、真实图片、完整trace/SQL复算、Online真实递推、Attention splitK归属与报告措辞。
- 本地P2/evidence/final/manifest.sha256仍保留用户原差异，其他已有未跟踪文件未动；它们不进入A3提交。
- 不提交水杉、不猜A3水杉分支，不自行宣布Engineering PASS。

内容提交edba39528f6f3b3fe91c6d57ff53d228a675e610已推送GitHub main。通过连接的GitHub REST ref/Contents/tree API核对372文件全部blob SHA一致；直接fetch_file回读17份文件（README、全部核心源码、执行/正确性/SQL、关键数据、一张PNG、一份gzip）字节完全一致，13图及17个README相对链接存在。回读记录保存github_verification.json，并随仅证据的后续提交发布；最终HEAD/main与完整树会在后续提交后再次核对，最终SHA见最终回复。

完整git diff --check因原始Profiler表/终端日志的行尾填充，以及README学号行的Markdown硬换行返回2，未将其伪称通过，也未改写原始证据。对src/scripts/.gitignore的源码空白检查返回0，完整分类见git_whitespace_assessment.json。这是原始输出格式的检查范围差异，无编译/数值/运行失败。

此文件的自审完成不等于外部最终审核完成。
