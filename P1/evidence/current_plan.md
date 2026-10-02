# P1 Goal 2 滚动记录

开始：2026-10-02 13:29:47 UTC（北京时间21:29:47）。一次性任务，本文件是用户要求的实验进度记录。

## 当前状态（RAW A/A 停止后）

Goal 2 性能核心受阻，阶段结果为 PARTIAL；Engineering 尚待外部最终验收，Submission 为 NOT_READY。21:06 首个 RAW A/A 完整目标与 driver 的 RAW/REALTIME 比值相对前一有效区间变化 2.261197% / 2.245563%，实际触发原 2% 停止规则。1 项启动、0 个有效 A/A、7 项未启动；未计算 D/P、排序或新 rho，没有新正式准入。回退后的唯一 fresh 也触发原保护。最新实际 n4096=48，受控成本3713.432874365秒（含全部失败及五次安全拍摄，逐任务三域max）。47/3613.087682189是RAW停止快照，不是最终总账。

匹配 RAW 停止版本为 `5c78049a22fa3422f2b23dddd634f2e7a3d73f9d`，含原始数据、407行闭合快照与七派生文件。随后只还原目标两处 timer literal 到 Goal1 源 SHA cece4fd…；框架支持双钟、严格 known 计费及 S3 实验入口保留，CLI 缺省 Grid 不改。回退不是时钟修复。剩余依赖阻塞包括新20配置参照、六组比较、S3配对、三个新种子确认与起点面板；不以未执行替换为 REJECT 或 NOT_REQUIRED。

回退后的必要 fixture 回归、匹配版本重算、干净221测试/19语法/四冷构建、唯一 fresh correctness-only n4096 尝试、报告及六图真实查看均已执行。fresh 因原保护中断，保留PARTIAL、不追加尝试或解除保护。两类独立阶段终审完成后仅继续 GitHub 如实阶段发布和实际远端核对；不再安排性能诊断。

## 硬边界与历史

- 受审起点和启动时真实远端为 `3ac0c4688b964c873379d012cbcf09afb7ed0937`。A1/A2 tree与431受保护P1文件登记在 `history_goal2.json`。旧raw、协议、派生数值和判定不改写；用户未跟踪提示词/原C保留。
- 正式n4096/double/原初始化/六循环/尾块，20配置8/16/24/64/128 × O0—O3，公共编译参数不变。历史目标SHA cece4fd…已由固定提交保留；新RAW候选仅改两处计时literal。
- 主控加三个实际原生代理，责任见 `agents_goal2.md`。性能只有主控，非阻塞 `.cache/performance.lock`；他人仅读写文本，短测试窗口单独安排。
- 所有实际n4096含失败/预热/复现上限520；受控时间逐任务max(MONO/RAW/REALTIME)累计上限16小时。项目总账是 `measurement/resource_ledger.jsonl`，不能重复加批次副本。
- 不改其他作业、全局服务、配置空间或计算内核；不混合增强、不操作水杉、不授予最终Engineering PASS。

## 可靠代码与已完成关口

- 诊断代码检查点 `41ba9b745175c7f938c26e3c97f38fc489537df3`。core SHA32f4dd…，runner22a839…，clock12e220…。此本地commit尚未发布。
- 核心作者和独立审核各自实际72 tests通过。完整区间runner独立30 tests通过；分析独立59 tests通过。之后主控实际174非图形、4真实图形测试共178项通过，16个Python文件语法通过。测试身份和后续两行fixture修补分别记录，不追改旧测试输出。
- 同源小矩阵240个全元素用例及5个ASan/UBSan尾块用例实际通过。它们不是n4096成绩。
- 诊断协议已于2026-10-02T14:25:38.808158Z冻结，SHA8c0d51…；有限设计和代码关放行30矩阵调用，正式关仍未放行。
- 七个短多钟探针实际完成，40s idle及两次固定8e9工作均留原始ns值；比率变化不能作校正系数或根因证明。两次诊断内核多时钟运行已完成，F=54.087463s、M=82.817986s（MONO），单列。

## 当前闭环与下一步

- 初始精确28jobs结束于前缀时钟保护：26完整、1中断、1未启动，另2次多时钟，真实共29次。原partial和实际失败成本保持原样；唯一有限十二次补诊断现已执行完毕，诊断合计41次。
- 作者37分析fixtures及实现代理独立37 fixtures通过，成本、历史raw写保护、真实恢复和重复seed缺口已修；S3未执行时不得生成性能效果图。初始raw/analysis以匹配检查点保护，不能改其计划中的旧runner哈希。
- 仅一次精确12次补诊断已通过方法关：两次补标签、两次多时钟、八次全新平衡A/A。区分前缀与完整区间；仅该诊断scope对比率变化记flag取得完整区间，硬资源/倒退/unknown/超时仍停止。
- 初始结果检查点为 `2fc0c334039bb6696c4d83acbe029ce65ca66ab9`。有限补诊断源码/协议初次冻结于 `a640671`；实际CLI在任何矩阵启动前因缺runtime protocol_path失败，旧协议/计划保留。另一外套受控wrapper被真实双锁拒绝，也单独保留0-call成本，不混称KeyError。
- 已最小修复runtime字段、增加check模式和真实parser/freeze_check fixture；独立13项回归和实际CLI check通过。修复检查点09afaea、协议r1 SHA7e8e6b…、计划1a2413…；十二次已真实执行结束，全为0退出，没有新增诊断额度或追认旧失败。累计41次n4096；实时成本以总账为准。
- 补诊断联合原始重算已完成：填补标签后的M0 D=3.61954%、P=46.97652%；M1 D=1.84430%、P=13.78460%，按预定规则选M1/rho14。延迟补标签不支持因果方差降低结论。新平衡A/A最大配对24.35165%超过rho14；rho仅描述所选安排的样本，不能当误差上界或证明5%可分辨。
- 所有补诊断完整同来源时钟未触发2%冲突，原前缀停机的反事实仍未知。正式计时器保持MONOTONIC；完整保护已实现并独立通过：逐目标process及完整driver分别检查同boot的first/previous，原2%门、资源、倒退、未知和超时约束不变。G1—G4字段、原始ns、身份及恢复问题已修复复核。分析不借runtime实时账本，按指定快照纯读重建共同面板；无效或冲突样本不计近优或KEEP。
- 固定版本历史重生成已完成：3ac提交九个数据文件和两张图、2fc初始诊断七个派生文件、c247补诊断十一派生文件全部逐SHA一致，证据在reproduction/goal2。README已修正为匹配提交重算入口，末尾仍须在干净checkout实际再核。
- 同源n129适配两项全元素检查和n4096 s24/O0、s128/O3各24个独立long-double抽查实际通过；正式目标内核和初始化不变，数学库参数仅用于验证，成绩不混入正式表。累计43个n4096真实启动且均已退出，时间以实时账本为准。
- 新A/A不支持不同配置的2pp风险判断，正式结果前固定different_identity_risk_supported=false：不同返回身份不授予非劣或KEEP；5%目标、2pp风险限及10%最低成本收益不放宽。相同配置的选择质量差严格为零，仍实际检查搜索成本和三个新种子。
- 正式协议SHA8ff127…及70项参照plan SHA62db9…于18:12冻结，经两类审核18:22放行，代码提交 `6463e2a3ab507debf02204d555c1f2083257235e`。精确jobs和资源场景保留于 `measurement/resource_plan_v2.json`，不反向更新冻结计划。
- 18:25唯一正式预热完整退出0，但process与driver的RAW/MONO相对first分别变化2.150234%和2.103464%，真实触发完整2%停止。预热1调用、已知保守成本34.217699605秒，正式参照0有效、69未启动；不能恢复这份协议绕过guard。累计44次n4096。原始ns、源码/构建、同域边界经独立重算，未发现软件guard误判。
- 有限后诊断两项已执行：原40秒idle和固定8e9 work探针各一次，总受控成本60.589249190秒、0矩阵调用。新RAW/MONO约1.0214；旧、新短work的RAW/REAL也曾变化，不能直接把RAW当真值。实际timesyncd/tsc/timex及日志只读记录已保存，日志不能证明预热漂移或宿主根因。三条区分路径及阻塞影响见 `reviews/goal2_formal_clock_review.*`。
- 有限Windows QPC相对核对已通过作者及独立13项实际测试（含五种原生清理），于19:22完成唯一idle40和work8e9。QPC为10MHz计数单位；RAW/QPC整个括界分别为[0.9999918633,1.0000067128]、[0.9999824611,1.0000167905]，端点/宽度门和原生PID退出均通过，受控成本61.298441010秒、0矩阵。这是当前两区间的相对证据，不是绝对准确、长期稳定或宿主根因证明；独立原数重算和新的有限RAW A/A准入仍待，正式C和旧first/2%未改。
- 原分析CLI已真实重算这次停止，44调用/已知完整成本/时钟不健康/参照不完整。未执行主实验却将候选确认标NOT_REQUIRED的标签问题已修：无搜索的两阶段NOT_EXECUTED，只有完整有效但未获选才NOT_REQUIRED；Random单独确认不代表S3确认。作者65项、独立65项及真实closed CLI通过，旧失败输出和raw/protocol/snapshot哈希不变，不把未执行策略当REJECT。
- 新只读桥执行前后使用实际flock、原probe身份及750秒限制。QPC源7fe379…、测试bccb33…、方法ac920…保存于本次旧C/runner检查点；新的RAW有限设计另文件编写，旧QPC冻结输入不追加更改。若另获准并完成八次A/A及两次必要数值抽查，累计将为54调用，后续全任务上界516或483；这些调用尚未执行，精确计划和两类审核待做。
- 未新增任何系统/语言包、工具链或全局配置；精确删除无人使用且来源已存的883484字节旧xterm下载包，保留已解压截图工具及其他缓存，详情 `environment/goal2_dependencies.json`。
- 停止版本已保存为 `a39f348e6cf0c7466900ec739a797753f4d93f0b`，其账本前296行完整闭合且SHA b8fda62…；新时钟迁移仅借用这些原始边界。原旧warmup失败不改成有效baseline。独立QPC结果审核及新有限设计10a4…条件审核已完成，均不直接授予正式准入。
- 新RAW C为a752f644…，原计算内核仍4005ab7…；core最小双钟识别55b880…，作者及独立各76 tests通过。新driver schema2使用完整target/driver RAW/REALTIME、同boot原first/previous和原2%门；schema1仍RAW/MONO。40旧journal SHA/header与全部296行canonical prefix精确绑定在 `measurement/raw_timing/clock_history.json`，SHA8ced08…，仅供时钟，不供成绩。
- 新driver作者首轮34 tests有三处fixture失败，完整输出保留；定位为旧冻结source identity、未按整数ns构造float和stdout舍入，修复后34项与4语法检查全部通过。独立driver检查尚在进行；生产guard和阈值未因fixture失败放宽。
- 新RAW同源240小矩阵全元素、5 sanitizer尾块及四级冷构建实际通过，0次n4096。新四级二进制单列于 `measurement/raw_timing/raw-build-four.stdout.txt`，不把旧二进制身份覆盖为新值。
- 有限机器协议 `protocol_raw_diagnostic.json` SHA03218fe…及检查点75a0154…已由独立gate放行两项数值检查；s24/O0和s128/O3各24预定点实际通过，最大相对误差2.814528e-15，两项完整RAW/REALTIME保护通过。绑定文件51dc3dc…保留原执行driver a6daf…；实际累计46调用/3544.605865782秒。旧八AA计划dff23c…仍未执行。
- RAW分析独立77项测试后发现新nonowned numeric缺known字段会被默认true；实际两项producer均true，不改其原始结果。方法owner先用合成反例复现，再作exact296历史兼容范围内的严格修补。driver同类缺口由主控修补，新36项实际通过（driver483a5c…）；修复后另冻结仅八AA的新协议，不改03218/75或未执行计划身份。剩余完整任务上界516/483、520调用/16h硬上限不变。
- 严格known修复已由代码49项和分析79项实际独立回归关闭；主控全221项与18语法通过，431受保护文件/A1A2 tree不变。新8AA协议84dc270…、plan4c514b…及资源3b7226…已冻结，代码/方法/分析gate分别6501a2…/cfa126…/d99a48…，尚0次AA，仅准原八项、不准正式。新RAW O2/O3实际二进制两timer间113指令相同；证据在raw-kernel-assembly输出。
- 最终报告/截图、完整正式批次、干净复现、终审、GitHub发布和真实SHA核对待后续关口。历史匹配版本的重算已完成，结束时仍需再次核对受保护清单。

不确定：时钟跨时段关系、两种安排的实际价值、5%目标的可分辨程度、S3收益。timesyncd实际active、chrony不存在；不把服务存在当根因，不调整任何服务。

Goal1旧滚动记录留在受审提交的Git历史，不复制成多份最终文件。

## 最终非依赖闭环

- RAW停止匹配5c78049的7个CSV/JSON全部逐SHA重生相同。MONO停止a39匹配版10个CSV及JSON全部非身份值相同，原after_fix由中间未提交8111分析器产生，a39是eded；summary仅analysis_sha256不同，不伪称11文件字节全等。
- 默认回退后主控完整221测试及19语法通过。首轮两处timer假定fixture错误、clean clone首轮两处旧绝对路径fixture错误均保存现场后最小测试修补，生产严格身份/2%门不改。作者14/79及独立clean新检查点5e6719c完整221/0skip/19语法回归通过。
- 干净副本四级cold真实cachedFalse，生产源码Ccece/core55未变。唯一fresh correctness-only n4096仍原live guard，于>=10秒触发比值变化保护：CLI130、C−9/interrupted、kernel/checksum空，真实1调用与11.231500658秒计入，不重试、不填成绩。总n4096=48。
- 三个最终安全原生终端截图已捕获，private Unix/auth0600/nolisten tcp、空授权拒绝、全部本任务PID/display/auth清理实际核对。框架SVG渲染后及5PNG逐张实际打开，独立两类review也实际看图。两张历史数据图保持原SHA，正式图片ZIP仅6图在忽略缓存。
- 431历史保护文件及A1/A2 tree终检不变，raw停止10个绑定输入不变；正式report/README/evidence索引相对链接全部有效，未新增依赖或全局配置。唯一成本账已闭合，48调用/3711.066297609受控秒（逐任务三域max，非宿主绝对校准）；搜索/内部复核/共同外确认/新有效参照/正式锚点均0。
- 两类独立阶段终审完成后，将如实PARTIAL版本正常提交/推GitHub main，再真实核对remote SHA和关键blob/图片。不操作水杉、不以软件交付审核代替最终Engineering验收。

- ER9来源修补：两viewer已从实际字段派生并重拍，保留旧全文/新SHA/输入SHA。额外0目标调用/2.366576756秒，末账48调用/3713.432874365秒，五次安全capture均清理；原3711.066297609是修补前checkpoint。最后交接事实见goal2_stage_result.md。

## 实际GitHub阶段发布

两类独立终审已经冻结允许如实PARTIAL发布。于2026-10-02T22:26:27.829815+00:00核对已正常push到main，提交95298a0d407dde693d1c362bed544ae41946ccae；随后actual ls-remote前后均同SHA，fetch后的24关键blob和24个public raw HTTP内容与本地逐SHA相同，P1远端树1048路径，记录在commands/goal2_publication_checkpoint.json。此是已发生的发布checkpoint；核对记录随后另commit/push并再次actual查询最终SHA。源/数据/报告和已冻结审核不再改动，累计48/3713.432874365不变。
