# Goal 2R 方法修订

方法设计：`/root/method`；独立挑战：`/root/reviewer`；主控独占正式运行。本文与新协议只作用于新批次。旧协议、RAW停止记录、原始读数与3713.432874365秒费用保持原样。原2%辅助域比值门及不同身份先行否决是待修的方法问题，不再作为新批次执行门。

## 1. 主域及区间

RAW是本次候选主域，经预定核查支持后用于C六层循环的内核耗时、完整目标进程区间、完整搜索driver成本和新增受控费用。四者分别读取自身边界，不能将QPC完整进程区间当作C内核时间。旧`wall`字段继续表示MONOTONIC，新RAW字段保存实际整数ns边界或由它们相减所得秒数；在线横轴使用实际RAW事件，不对旧时间乘比例。

常驻PowerShell桥在测量前握手五次，核对频率、高分辨标识、顺序、实际PID和创建时间。启动/清理计入项目开销，不计入C内核。QPC通过Stopwatch在同一串行桥中读取；频率实际查询。RAW/QPC可能使用相关硬件来源，符合仅支持观察区间的一致性，并非独立物理标准或UTC绝对校准。

设起止宿主读取事件为A、B，Linux同域整数ns分别为before/after，频率为F：

```text
D_low  = (B.before_RAW - A.after_RAW)/1e9
D_high = (B.after_RAW  - A.before_RAW)/1e9
H_low  = (B.tick - A.tick - 2)/F
H_high = (B.tick - A.tick + 2)/F
RAW/QPC = [D_low/H_high, D_high/H_low]
```

必须有正的有序边界。±2 tick是保守量化敏感性处理，不称为同线程的官方排序歧义。工程筛查要求每个RAW端点括界≤20ms、RAW区间宽/QPC区间≤0.2%，整个RAW/QPC比例界包含于[0.995,1.005]。不用中点或半RTT假定单程误差；阈值不因结果放宽。MONOTONIC、REALTIME与CPU是辅助读数，倒退、跳变或比值变化单列保存，不能单凭它们否定RAW，也不能丢弃RAW原始读数。

六个预定区间与八个独立A/A进程见[诊断安排](goal2r_timing_plan.json)。两个不同长度idle、两个固定次数CPU负载、快128/O2和慢8/O0真实n4096分布两小块；idle请求值只控制等待，不是准确度证据。A/A选128/O2、8/O2，各两对AB/BA，物理样本不合并为零。A/A的范围仅描述这八个样本，不能外推全局rho或未来噪声上界。

正式阶段每参照轮、每主/留出seed含共同面板、每个Greedy起点及追加面板前后各一个idle10核查。相邻边界可引用同一次真实检查，不遗漏覆盖。后端失败只影响预定块；数学运行仍正常完成并保留结果，时间不可评分。不按结果好坏重划边界或删除慢样本。桥宽超限是桥证据不足；最多一次有明确修改的修复复测。窄括界的可重复分歧才进入主域诊断。有限检查不证明未采样的每一时刻或宿主最终根因。

预定六区间已完成，实际查询频率均为10,000,000Hz，整数读数、桥线程/进程、生命周期与受控driver边界见[原记录](goal2r/timing_result.json)及[独立整数复算](../reviews/goal2r_timing_review.json)：

| 区间 | 实际QPC秒 | RAW/QPC完整比例界 |
| --- | ---: | --- |
| early idle10 | 10.3523881 | [0.999965727, 1.000025330] |
| early CPU 4e9 | 11.6835443 | [0.999972879, 1.000022819] |
| early 128/O2完整CLI | 38.8194298 | [0.999991520, 1.000006971] |
| late idle40 | 42.4402569 | [0.999987742, 1.000008324] |
| late CPU 8e9 | 22.1342294 | [0.999983155, 1.000014525] |
| late 8/O0完整CLI | 335.1599250 | [0.999999113, 1.000000969] |

最大RAW端点宽0.660899ms，最大相对括界宽0.00595649%，均满足原固定工程筛查。MONOTONIC/QPC约0.941–0.966，REALTIME/QPC约0.963–1.135；主辅域分歧原样保存。只读adjtimex的`freq/65536`和`tick`快照不能确定这些变化的根因。

八个A/A样本对应八个独立新进程；F=128/O2两对的有符号差为+2.8075%、+4.1029%，M=8/O2为−1.0611%、−15.8600%。这里用`100*(A-B)/median(A,B)`描述实测波动，不把大差异自动归为时钟失效。初始诊断共10次n4096、948.666897230秒受控RAW费用，未耗满2700秒上限；这些证据支持本阶段选择RAW，正式块仍执行预定前后检查。

## 2. 三层判断及停止表

| 事件 | 数值结果 | 性能测量/比较 | 动作 |
| --- | --- | --- | --- |
| 参数、计算、输出、退出错误 | 不合格 | 不评分 | 保留失败、实际调用和成本，定位最小修复 |
| 超时、资源上限、中断、归属无法安全核对 | 依实际输出 | 依实际输出/主域 | 仅清理有确切身份的本任务进程，记录未完成 |
| RAW倒退、单位/边界错误、QPC主域核查失败 | 独立保留 | 受影响块不评分 | 停依赖该测量的批次，继续不依赖工作 |
| REALTIME/MONO变化，RAW证据正常 | 不受其否决 | 原样有效，辅助异常注明 | 不杀正确性进程、不撤销全部课程实验 |
| 同二进制耗时波动，主域正常 | 独立保留 | 样本不删除，限制细小差异结论 | 仅使用事前重复和平衡次序 |
| 5%/2pp判断不足 | 不受影响 | 有限/不确定 | 不阻止有效的其余配置/算法 |
| 新旧身份不匹配 | 不能混用 | 不能混用 | 新目录/新协议，不续跑旧停批 |

`correctness`保留参数、解析、退出、超时、资源及生命周期保护，辅助比值不杀进程；其耗时不会自动进入性能表。`diagnostic`保留全部域读数；`benchmark`要求同域边界与块核查。没有忽略所有错误的开关。核查成立与数学正确仍不能代替比较证据。

## 3. 正式参照、搜索与计费

20配置采用三轮完整随机遍历，`Random(505063+r-1).shuffle`，每项至少三有效样本。额外一次预热和每轮一个固定128/O2观测合计四次，单列不补正式重复。有限预算Grid仍按s外层/O内层固定顺序。六seed及平衡算法位置沿用旧协议的未执行列表；每项R=8、repeat=1，四种搜索独立只读自身反馈。Greedy四个结构起点单列。

共同参照质量为`g_ref(c)=100*(median_ref(c)/min_median_ref-1)`。这是所测表的位置，5%成员不称为总体近优保证。所有返回同一配置者取得相同g_ref。S3保持同seed Random前六项、两候选各一次新复核；两个样本中位数等于平均，可能上升，不锁定首测偶然低值。

所有seed搜索先锁定，再对{Random返回、S3返回、参照最优}身份并集作三轮外部共同测量。每轮按`Random(505071+100*block+round).shuffle`，同身份只测一次，全部引用共享原值。Grid/Greedy为锁定依赖，但不额外加入面板；其返回恰好在面板内才可引用。面板不反馈、不替换搜索返回。主计费是每项完整搜索RAW driver，含发生过的框架与构建开销；共享面板、QPC、一次构建、数值/截图另列项目成本，只入总账一次。内核/进程/编译分解不能二次累加。

旧48次/3713.432874365秒不折算。新增RAW正差计费，辅助日期时钟不替代成本；未知时长不填零。520次及57600秒累计硬上限不重置。诊断默认≤2700秒、≤12矩阵调用（默认10），一次新原因补诊断≤1800秒用储备。三次数值/最终复现独立预留；失败仍计费。受控程序/等待费用与人工会话跨度区分。

独立轻量检查另见`goal2r_method_control.jsonl`与`goal2r_review_control.jsonl`。方法角色此前未测RAW的只读/纯函数检查如实标为未知；安全预算单列120秒保守上界，不能称实际费用。另预留60秒给已测代理补账及后续轻量开销，正式driver合计提前扣除180秒安全余量；已测值和未用reserve分别报告，不重复累加主控已经受控计费的回归。

## 4. 有执行顺序的有限样本接受表

对不同身份的每轮共同面板计算`G_r=100*(t_R,r-t_S,r)/t_anchor,r`，同轮正anchor；保存全部三值（追加后五值）、中位数、min/max。相同选择身份G=0，但仍需完整真实面板、两搜索8次、正确性/身份/计时/成本，不以零差跳过缺数据。A/A波动另存，G=0不证明两个独立分布等价。基准/面板差异具体描述，不用历史rho14外扩、不用全局false否决不同身份。

`L_b=min G_b,r`、`U_b=max G_b,r`；`saving_b=1-C_S3,b/C_R,b`。只有主域、正确性、身份、成本、所有必要seed的等调用搜索、至少三真实完整面板齐全才称该阶段数据完整。以下依次判断；浮点边界仅有1e-12绝对舍入容差：

1. 数据缺层：未启动为NOT_EXECUTED，启动但不足为INCONCLUSIVE。
2. 任一不同身份`U_b<-2pp`：REJECT；若`U_b<-10pp`同时标记严重观察退化。
3. 任一`L_b<-2<=U_b`：INCONCLUSIVE（风险跨界）。
4. 所有`L_b>=-2`且median(saving)≥10%：效率KEEP。
5. 所有风险满足、median(L)≥2pp、至少两组L≥5pp、median(saving)≥−10%：质量KEEP。
6. 效率未达，质量低界条件未达而高界满足相同2pp/两组5pp条件、成本允许：INCONCLUSIVE（收益跨界）。
7. 风险全部支持，但高界也不支持质量路径，或质量成本增加超过10%，且效率未达：REJECT，未见有意义改进。

效率优先，质量跨界不会否决已经符合效率路径的候选。每seed成本只有一个实际driver观测，其配对saving中位数是描述值，不伪造成本总体区间。主实验六seed、留出三seed用同样定义和阈值；主实验KEEP只是阶段选择，最终保留需主/留出均完整KEEP。缺留出不最终KEEP。CLI缺省仍Grid；Random仅是增强比较基线。

主实验INCONCLUSIVE且数据完整时，只选不同身份的跨界对追加：风险跨界优先，其次质量2/5pp跨界；类内`U-L`降序、seed升序。最多两个seed，每项完整并集追加第4、5轮，最坏12次，仅一次。只在主实验进行；留出仍按冻结三轮，不追加搜索或换seed。原新样本全部纳入。**min/max全样本包络只能扩展，不能靠追加保证把既有跨界变为KEEP/明确退化REJECT**；补测用于有限复现和扩展该对观察，不称提升置信度、缩窄区间或保证消除不确定。预算不足时记缺追加，不能冒称已执行。

追加请求始终由原第1–3轮与六组已闭合搜索成本重算，后来的缺第5轮、追加块核查失败或项目总费用缺口不能改写原请求。新增无效样本保留、费用照计，完整阶段据实际缺口为INCONCLUSIVE；不能用清空原判定或抹掉失败费用恢复身份。

主实验完整且未KEEP时，候选留出才为NOT_REQUIRED；三个新Random seed及其返回/参照去重面板仍执行（最坏42次）。主实验缺数据则候选留出PENDING/NOT_EXECUTED，不套用NOT_REQUIRED。

可达性例：不同身份六组低界6/6/3/3/0/0pp、成本增加5%→质量KEEP；每组[-1,0,1]pp且saving10%→效率KEEP；整组上界−3pp→REJECT；[-3,−1,0]跨风险→INCONCLUSIVE；[0,3,6]六组且无节省→收益INCONCLUSIVE；完整零收益且无节省→REJECT。夹具仅在测试中，不能画成实测。具体测试为`tests/test_goal2r_method.py`，正式结论必须另外读取真实日志。

## 5. 原资料实际读取

访问日期均为2026-10-03（Asia/Shanghai），仅限本次问题。DOI入口读取报错后使用原大学仓储正文；Canonical网页的browser读取报错后以只读HTTP获取同一官方页面正文。未安装软件或改全局配置。

| 标题与原链接 | 实际阅读段落 | 本地适用与限制 |
| --- | --- | --- |
| [Linux clock_gettime](https://man7.org/linux/man-pages/man3/clock_gettime.3.html) | DESCRIPTION的REALTIME/MONOTONIC/RAW/CPU/BOOTTIME；timespec单位 | MONO受渐进校正、RAW不受NTP渐进调整；CPU不是等待成本。语义支持分域，不能据手册证明本机RAW绝对正确。 |
| [Linux adjtimex](https://man7.org/linux/man-pages/man2/adjtimex.2.html) | struct timex、modes权限及NOTES | modes=0只读；freq为16位小数ppm，除65536得到ppm；tick为每内核tick的µs。getconf CLK_TCK不能替代clocksource频率。瞬时参数不能确定本机漂移因果。 |
| [Microsoft Acquiring high-resolution time stamps](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps) | Guidance、Virtualization、FAQ frequency/UTC/quantization | QPC是差分计数、频率查询，与UTC调整独立；虚拟化支持依hypervisor。相同桥线程不继承跨线程±1tick排序问题；±2tick仅保守敏感性。 |
| [Canonical Time synchronization for Ubuntu on WSL](https://ubuntu.com/wsl/docs/stable/explanation/time-sync/) | Hyper-V隐式同步、Ubuntu24.04与较新chrony行为 | 用户态NTP与宿主同步可能冲突，提供只读调查线索；文档不证明本机根因，也不授权停服务、重启或改.wslconfig。 |
| [2021 Autotuning Benchmarking Techniques: A Roofline Model Case Study](https://arxiv.org/pdf/2103.08716v2) | §III-C Evaluation Budget及normality讨论（PDF pp.4–5） | 有限重复分配动机；原方法的CI依分布假设，正文指出常非正态且默认两次可过早淘汰。本题6+2未实现其CI/BLAS/并行机制，不继承置信保证。 |
| [2024 A methodology for comparing optimization algorithms for auto-tuning](https://pure.uva.nl/ws/files/182730825/A_methodology_for_comparing_optimization_algorithms_for_auto-tuning.pdf) | §3.2–3.4，预算、测量噪声/算法随机性及真实时间（PDF pp.7–9） | 用共同预算、真实seed搜索与分账；不把函数计数替代时间，不将六seed/三重复当大量iid请求。原计算Random基线不替代本题实测。 |
| [2023 Just-in-Time autotuning](https://arxiv.org/pdf/2309.06414v1) | §3.3及§4.3（PDF pp.4–5） | 编译、试探慢变体有成本，需要后续调用摊销。本题没有未来调用量，不宣称应用总收益或盈亏平衡；不是6+2规则来源。 |
