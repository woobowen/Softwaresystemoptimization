# 固定两项QPC相对核对：独立结果审核

审核者 `/root/review`；已直接读取原始输出、启动身份和primary起止，以整数差及Fraction重算，未导入作者的区间函数。两项满足事前相对筛查门，只支持提出另审、另冻结的有限RAW A/A设计。原MONOTONIC协议继续停止；尚未批准RAW A/A执行或新正式实验。

[原始输出](../measurement/formal_clock_drift/host-qpc-two-intervals.stdout.txt) SHA-256 `3e13770e3e3b3cb927de2760c7f21f00c4c43dbf709be7dc0f5e3bbd306213d3`，实际attempt `2740d26f0aca4b12aea965b60903b08f`，开始UTC 2026-10-02 19:22:19.974053，结束19:23:21.271531。与[执行前代码关](goal2_host_clock_review.json) SHA `4a46cc745d3b52476b2878d90fa2bb5ba72365c7c5707851cb5321d06ad12a17`及方法 `ac920bb167e07760d841c430491df6edcdad45fe3be25af33e2acfe8f3924ea6`完全对应。原probe源、binary、GCC、桥源码和测试身份已对实际文件复核，原代码关文件未修改。

| 固定工作负载 | QPC区间（秒） | RAW/QPC完整括界 | MONOTONIC/QPC完整括界 | REALTIME/QPC完整括界 |
| --- | ---: | --- | --- | --- |
| idle40 | 40.9477802 | [0.9999918633, 1.0000067128] | [0.9769466197, 0.9769611286] | [0.9958412970, 0.9958557835] |
| work8e9 | 19.3217319 | [0.9999824611, 1.0000167905] | [0.9781816023, 0.9782152813] | [1.0163065949, 1.0163402905] |

九次响应seq0—8、实际Frequency=10000000、PID=70576、高分辨true和四域原始整数ns全部核对，五次握手完整保留且不替代固定seq5/6、7/8端点。两项分别用整数tick差409477802、193217319，再加减2tick；四个测量端点括界为0.169061、0.438595、0.243866、0.419037毫秒，全部小于20毫秒。两个RAW区间的相对宽度为0.0014839779%、0.0034308674%，另外两wall域也满足0.2%门；两项RAW/QPC整个括界均落入[0.995,1.005]，没有删除慢端点或再挑窗口。

两项C工作进程退出0，其stdout四域时间也从start/end整数独立重算一致；C的CPU和桥parent CPU保持不同区间。桥退出0，Linux主控PID369384、bridge PID369385已消失；实际宿主PID70576/创建ticks639265657398411510由限定PID查询确认absent，stderr为空。完整受控三域为MONOTONIC59.788104834、RAW61.169250493、REALTIME61.298441010秒，最大值61.298441010秒计入primary，新增n4096=0。全部primary起止独立汇总后为44次、3228.911797217秒，成本已知。

RAW与QPC在这两个区间相对一致；MONOTONIC和REALTIME与QPC的相对差异并未消失。QPC与RAW可能共享TSC/Hyper-V计时基础，Frequency不是硬件频率，不能据此指定绝对真值。[Microsoft QPC说明](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps)。这两个短区间不能证明数小时稳定、5%/2pp性能分辨力或总体误判率。旧完整预热冲突、first/2%门、原RAW/REALTIME约2.93%反例和未执行的正式参照/算法/S3状态均保持。

[机器可检查复算](goal2_host_clock_result_review.json)保存九端点、所有域区间与比例、实际primary记录和来源哈希。后续只能提出一个另审的有限RAW A/A闭环；通过该闭环、正确性及新身份/协议/资源关之前，不启动完整参照或授予性能KEEP。
