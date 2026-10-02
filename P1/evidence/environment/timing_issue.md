# 正式实验前计时诊断与最小适配

旧预测试为 pretest-v1（results/pretest），并非正式参照或在线初评。四个已完成的真实进程中，C 的 gettimeofday 内核时间都超过 Python monotonic 进程时间；差异达秒级，float 量化不能解释。原 stdout、timestamps、kernel、process wall、停止的第五项全部原样保存，逐项对照见 timing_anomaly.json。旧源码可从 Git d545d53 取出，不用新源码冒称旧数据。

两条诊断路径：Python 对 REALTIME/MONOTONIC/RAW 的五个短间隔实际对比（clock_probe.json）；独立小C MONOTONIC 与 Python 同进程时基对比，包括 CPU0 affinity 与无pin（clock_compare.json）。RAW/MONOTONIC约1.091只描述可见差异，未确认WSL/时钟服务的具体根因，不据此换算成绩或改变全局时钟。

独立审核比较了两种方案：保留 gettimeofday 标失败/重试，或只换单调时基。前者已系统性出现异常，会浪费慢运行且混合时基；采用后者。先向自己的已核验cmdline的autotuner发SIGTERM，其正常中断处理清理目标进程组；没有停止任何用户无关进程。停止记录 pretest_stop.json，driver已退出。

C仅将timeval/us/gettimeofday换成timespec/ns/CLOCK_MONOTONIC，两个位置不变并检查返回码；float tdiff和六位输出保留。初始化、double、n4096、六循环和计算量不变；checksum仍在结束时间之后。差异文件说明CRLF/行尾空白规范化，原件字节一致保留。验证生成器明确识别原版与新timer边界，替换前后比较内核。

新 small240 和 ASan/UBSan 五项、新 full/n4096 两构建各24点抽查通过。独立代码复核再次通过数值与汇编检查；pretest_monotonic 九次和一次有界三次连续快配置诊断已经结束。新的formal protocol只接受新目标哈希，clock_guard拒绝kernel大于同clock process wall加0.005s，原输出不改写。尚未开始正式结果，不混入旧批次。

参考：[Python time.monotonic](https://docs.python.org/3.12/library/time.html#time.monotonic)、[Linux clock_gettime文档](https://man7.org/linux/man-pages/man2/clock_gettime.2.html)。它们说明单调性与调整特征，并不证明本机时钟绝对准确。


## 新时域一致性与仍存波动

新预测试每个 stdout 首行、finite checksum、rc=0、affinity0 和代码/协议哈希由另一上下文重新核对；九次 MONOTONIC kernel 均小于同域进程 wall，原 gettimeofday 与进程时域不一致的问题通过统一计时解决。这不表示绝对时钟已校准或性能噪声消失。

O0/s8 三次为 304.606781、310.770050、312.302917 秒；O3/s128 三次为 42.548756、46.046341、49.066238 秒。快配置随次序上升，因此只做一次三次连续快配置诊断，得到 41.610653、47.216225、49.724476 秒，之后停止追加预测试。六个快样本中位数46.631283秒、MAD2.764074秒、相对MAD5.927510%、相对范围17.399957%；这些是描述性样本，不是置信界。

诊断中 CPU0 的 jiffy 忙比例约99.98%，waited children 的 CPU计数与 RAW 跨度接近，RAW/MONOTONIC 跨度比约1.089至1.098。测后短快照 CPU pressure 均0、CPU0闲时忙约2%；温度、cpufreq/governor和PMU不暴露或不可用。这些证据未定位物理宿主机根因，不能据此指定某频率/温度值，也没有停止别人进程或改全局设置。

原始 UTC timestamps 仍保留为日期/顺序信息，不能相减作调优成本；正式成本采用 MONOTONIC。正式协议以固定收益门、严格风险约束、样本端点敏感性与有限冲突复核限制结论；不能通过大幅放宽质量退化容差制造 KEEP。相同目标、配置与编译产物的计分从未以 RAW 比率改写。
