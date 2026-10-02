# 有限RAW计时分支：方法与代码关审核

审核者 `/root/review`。方法和最小core/driver正确性关已通过，许可仅为冻结身份与精确计划后执行两个新n4096数值抽查。八次A/A执行仍等待两抽查的实际数值/时钟结果及独立严格分析关；没有批准完整正式比较，原MONOTONIC停止、失败预热和未执行状态不变。

完整阅读[方法设计](../measurement/raw_timing_design.md)，冻结SHA `10a4db6ea5e0d370c0fedffdd7aae5ccbed7315729ebff55e3a47be1bfa4f42d`。QPC原整数和端点括界已由[单独结果审核](goal2_host_clock_result_review.md)核对，仅支持提出局部RAW候选，没有绝对时间真值或长期稳定性保证。

用原整数ns独立重算已有矩阵RAW/REALTIME，描述性39完整进程/43完整driver的范围及最大first/previous变化一致。剔除原时钟失败预热后，baseline仅38/42项，first仍原d30/a754，previous仍最后数值抽查5fa6。被中断和失败预热不转有效；旧kernel秒数不重标RAW。历史迁移逐字核对40个旧journal、三个binding文件及ledger前296行，与固定 `a39f348e6cf0c7466900ec739a797753f4d93f0b` 完全相同，bytes/SHA/header fingerprint全部一致，详见[本审核JSON](goal2_raw_timing_review.json)。

新C `a752f644337a96b6bceeadc24489c0d14bbf976850dcb0292b06d312ef93aed1` 与固定6463版本逐字比较，仅两个计时literal变RAW；默认初始化、n4096/double、原六层循环、尾块和checksum均未改，内核SHA仍4005。core `55b88052a5d33eec30b88a40a1800452365d0b2e0694f2d96f39caca3236266c`只识别唯一MONOTONIC/RAW域并核对应process delta上界；已有MONOTONIC字段不换义，搜索/预算不变。已独立运行原与新76项回归及两文件语法检查，全部退出0，源/测试/C/设计SHA前后不变，真实n4096新增0、受控成本11.626588080秒。

新driver最终SHA `a6dafecd1f1abb00d9515829f5e1cf55d97bb2f024b8475d74f82a609fa94e4c` 将完整process和driver分别比较RAW/REALTIME，同boot同来源的first和previous各自2%，prefix仅观察。已有rawns/coverage/调用数/资源max三域/恢复身份保护保留；schema2和history8ced精确记录新语义。C内核与process RAW同域保护仍为+0.005秒，错域的两个timer literal在预检中拒绝。新成功matrix若缺journal或schema2 RAW mode/history/complete/error结构即拒绝进入新baseline，原四个固定direct诊断保持原身份。

独立联合回归初次47项中46通过、1项ERROR；driver34全部过，唯一失败是旧CLI fixture仍引用旧source/framework身份，生产freeze_check正确拒绝。原owner只更新临时fixture身份，旧冻结协议及哈希检查保留。第二个发现是未来无journal的matrix可进入driver baseline，owner用最小生产拒绝修复并加反例。最终独立相关19项回归和五文件语法检查均通过，真实成本1.562047554秒、n4096新增0，源码/测试前后SHA一致；初次失败成本2.748525882秒和输出仍保留，没有覆盖或记成通过。作者当前完整48项通过的记录也已读取，不能将它描述为本审核者重复执行全部48项。

四个新冷构建均为实际GCC同公共参数，仅O级别不同，cached=false/exit0；四个binary逐文件SHA和build key匹配冻结草案。240个小矩阵检查和五个sanitizer尾块检查的原始日志逐条为CHECK count=n²、failures0、退出0和stderr空。新数值adapter `f195ec9a183e9b12800661c6c401900c4f75537c833158fdf6153cb59522dcad` 同原内核，显式seed1/mode0，仅验证增加mathlib flags及计时后24个独立long-double点，不称大矩阵全元素验证，不作成绩。

**批准的两项数值步骤**：协议approved并冻结源码/编译器/方法/history/审核身份，生成精确八AA计划及十调用资源计划，正常提交源码/协议检查点之后，唯一scheduler持真实非阻塞performance.lock，分别controlled执行 `goal2-raw-n4096-O0-s24` 与 `goal2-raw-n4096-O3-s128`。每项一个真实C进程、call_upper=1、有frozen journal、完整RAW守卫/history8ced和primary账；不调用全量validation wrapper、不附加预热。原始CHECK/输出/身份/原整数时钟/失败与成本全部保留；任一失败停止，不自动追加。

**八AA依赖**：两项新数值raw须实际CHECK n4096/count24/failures0及完整clock/resource有效，由独立审核核对；另完成严格RAW分析代码关，保证schema2/history/来源/first/previous/2%/成本重算。届时仍只能执行预定F-A1,F-B1,M-B1,M-A1,M-A2,M-B2,F-B2,F-A2八个全新标签，F=s128/O2、M=s8/O2，同二进制，不按配置身份合并A/A，不额外预热或补到稳定。只有八项全有效和四组M/F最小正差大于max(P_F,P_M)时，才能另审新正式协议。

完整项目调用上界独立求和为516/483，含旧44、新8AA/2数值和后续全部必需阶段；520调用/16小时仍硬限制。此次独立关后账本为44调用、3268.031799947受控秒，剩余54331.968200053秒，十目标超时和为12000秒；最坏全部剩余超时不能保证完成。5%目标、2pp质量风险、10%最低收益及different_identity风险不支持门不变，没有搜索增强KEEP。保留0-call测试RAW/REALTIME≈0.93944和原短work约2.93%反例，不能因QPC筛查通过就宣布环境已稳定；这些0-call记录不更新matrixbaseline，实际费用按三域最大值计账。

本审核JSON保留全部actual command/primary/源身份、发现/修复/复核和限定许可。该gate在协议引用后保持字节不变，数值和AA实际结果另存独有结果审核文件；旧v2继续和完整formal准入均为false，Goal2没有宣告完成或最终Engineering PASS。
