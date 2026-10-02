# Windows QPC有限相对核对的独立审核

审核者 /root/review。有限两项QPC相对诊断的方法与代码关通过；原MONOTONIC协议仍停止。没有恢复正式实验、批准RAW A/A、修改旧first/2%或删除RAW/REALTIME反例。

Linux每次请求前后括住host counter实际读取事件；两事件Linux域差范围为last.before−first.after至last.after−first.before，整数tick先相减再除freq正确。startup不进入比较但全部记实际成本，固定原idle40和work8e9不改变目标输入。

Microsoft官方说明支持以QPC测时间间隔及使用固定boot frequency转换，但它不与UTC同步，精度/准确度仍受counter基础影响，不能据此认定本机QPC或RAW为绝对真值或二者是独立硬件振荡器。见[QPC官方说明](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps)和[Stopwatch高分辨标志](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.stopwatch.ishighresolution?view=netframework-4.8.1)。实际IsHighResolution必须true，tick先差再转换，量化边界应保留。

初稿发现H1 selector后readline可在partialline上无限阻塞，H2缺少SIGTERM清理和Windows实际PID退出证据，H3阈值未进入代码，H4未区分parent与C的CPU。作者现在将partialline改为deadline下os.read，落实整数差、20ms/.2%和两项整个RAW/QPC边界门，并明确CPU范围。H1/H3/H4已静态看到修复，尚未由本审核者执行相关fixture。

方法方案[新增QPC诊断节](../measurement/formal_clock_drift_design.md)（SHA-256 `ac920bb167e07760d841c430491df6edcdad45fe3be25af33e2acfe8f3924ea6`）已完整静读，有限方法范围通过。固定五次握手不替换四个测量端点；两个原工作负载各一次；所有wall域的端点宽度≤20ms、区间宽度≤0.2%，两项RAW/QPC整个区间都须落入[0.995,1.005]。±2tick只是保守量化敏感性处理；REALTIME括界附带无未观察跳变条件；宿主和WSL可能共享计时基础，不能据此证明绝对准确或数小时稳定。

H5清理命令多余`+`已去除；H6将原响应和已取得的工作负载输出在异常校验前保存；H7要求正tick、跨端点Linux有序，清理前固定Process.Handle、核对创建时间并停止同一Process对象，复用PID不停止。新发现H8处理清理阶段收到SIGTERM：有界finally暂忽略SIGTERM/INT，保证清理和JSON不被二次信号打断。未扩大终止范围。[Microsoft process handles](https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers)、[Stop-Process](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/stop-process?view=powershell-7.5)。

本审核者在真实非阻塞performance.lock下独立执行13项回归，13/13通过，unittest报告3.738秒；另一次语法检查退出0。两项均由controlled写入primary，n4096新增0，max三域成本4.370467999秒。完整命令、时间边界、资源attempt见[独立回归记录](goal2_host_clock_regression.json)，原始测试输出见[stderr](../commands/host-clock-independent-tests.stderr.txt)。前后源码SHA `7fe379a843ebd360c31ec4e7ecd23c669138ee5c80bba85065d18e21ddeb24a7`、测试SHA `bccb33e16220df5606703c31468f9c33bdeca6df84be0d94d29144917648f023`不变。

五个真实Windows清理用例分别覆盖正常、失败工作负载、timeout、工作阶段SIGTERM和清理阶段SIGTERM；宿主PID77472、73496、68200、47752、43724均由独立查询确认absent，Linux自己的bridge/workload PID也已消失。完整PID、创建时间、查询命令、原回复及异常见[原生独立日志](../commands/host_cleanup_independent.jsonl)。这些用例每个五次实际QPC握手，只是生命周期检查，零工作负载比较区间，未用于时钟质量评价。

准入限于一次固定五次暖握手、idle40和work8e9各一次的QPC诊断。执行前复核原probe源/binary/GCC身份，真实flock、primary成本和750秒上限保持；所有原始端点保留，不重新挑窗口。只有两项完整、生命周期与成本明确、全部括界合格且RAW/QPC整个比例范围都落入[0.995,1.005]，才能提出另行审核、另冻结的有限RAW A/A方案。此处没有批准该后续试验或任何正式参照、算法比较、候选KEEP；原MONOTONIC预热冲突和三条已执行诊断路径的事实不变。
