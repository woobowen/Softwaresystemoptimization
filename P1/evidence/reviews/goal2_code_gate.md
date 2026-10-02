# Goal 2 核心实现独立审核

审核者：`/root/review`；实现作者：`/root/implementation`。完整读取 `src/autotuner.py` 及 `tests/test_goal2_search.py`，并与受审基准的核心路径比较。审核冻结源码 SHA-256：`32f4dd734a15b7d295ee011b566bf113b722e8128fd147525e8c77856dfdf964`。

## 实际验证

主控分配独占短测试窗口后，审核者持有 `flock -n P1/.cache/performance.lock` 执行 `cd P1 && python3 -m unittest discover -s tests -v`。**72 个测试、exit 0、无 skip**；unittest 10.753 秒，外层实际 MONOTONIC 10.823904780 秒、RAW 10.791651942 秒、REALTIME 10.823905241 秒。源码/测试前后哈希相同；本窗口 n4096 调用为 0。完整命令、起止、三个钟域原值、源码身份和 stdout/stderr 在 [goal2_code_gate.json](goal2_code_gate.json)。锁已释放。

既有 54 个测试和新增 18 个测试覆盖实际短 C 进程、四级构建、异常/超时、断点恢复、S3 候选及预算等路径。此次测试不是正式 n4096 数值抽查，也未运行任何正式性能比较。

## 代码结论

核心/旧算法路径与 S3 的低成本正确性关通过，**整体 runner/分析与正式实验关仍待审**。Grid 的 s-major 枚举、无放回 Random、基础 Greedy 随机起点/邻居规则保留；显式起点只用于 Greedy 诊断，不改变默认随机规则。目标 C 的六层循环、double、n4096 与初始化没有修改。

S3 用同 seed Random 顺序的六项前缀，探索结束冻结最多两个首测 finalist，再各一次真实复核。失败占试探和已启动调用；复核失败失去返回资格；候选不足不补免费探索。最终只比较成功复核候选的两样本中位数，平局保留初测访问顺序。恢复回放 `fresh_score`，避免把聚合分数误当新样本。

独立检查了 `1→100`、`2→2` 的反例：原首测赢家的聚合分数会上升为 50.5，最终返回第二候选 2；没有沿用历史首测最小值。`best_so_far` 在探索时为临时候选，第一次复核之后只比较当时已复核成功集合。正式曲线必须说明该资格变化，不能把后续面板结果回填。

## 发现与关闭

| 项目 | 影响及严重性 | 修正/回归 | 结论 |
| --- | --- | --- | --- |
| CPU 原始起止与读序缺少 | 中：只有差值不足以检查诊断边界 | 增加 `child_cpu_start_s/end_s`（user/system 秒）和 `boundary_read_order`；clock fixture 检查整数 ns、各域独立及 CPU 原始值差 | 关闭；CPU 时间仍不能替代进程/driver 等待时间 |
| aggregate evaluator 误用时校验过晚 | 中：错误 strategy/repeats/proposal 可能先发生 build/measure | 校验移到 `evaluate` 入口；误用 fixture 断言没有 build/measure | 关闭；已包含在独立 72 测试 |
| 永久历史最小值会掩盖候选复核变慢 | 高风险线索，未出现在最终实现 | S3 聚合 best 可上升，最终成功 finalist-only；极端反例和失败/恢复用例 | 关闭；旧三基础算法仍保留原单测语义 |

## 后续依赖

主控编排和派生分析必须严格核对计划、实际步骤、`measurement_start/completion`、源码/编译器/协议、试探聚合和 summary，防止改 metadata 或 summary 伪造恢复/配置选择。共同面板去重、外部样本隔离、真实累计资源锁/计费、截图安全和接受表的 fixtures 不在本核心关的完成范围，须随后补审。正式构建若计时/输入/内核变化，应重新开身份和受影响批次。

该记录是内部核心关，未授予最终 Engineering PASS。

## 新数值原始产物的只读复核

主控实际执行后的 `measurement/correctness/goal2-small.jsonl` 与 `goal2-sanitizer.jsonl` 已由审核者逐条读取，重新检查退出码、stdout 的 `CHECK` 元素数/失败数、源身份和重复覆盖；审核者没有在性能窗口重跑它们。

| 产物 | 实际构建 | 实际检查 | 检查范围 | 最大绝对误差 | 失败/排除 |
| --- | ---: | ---: | --- | ---: | --- |
| 小矩阵 | 8 | 240 | n128/129、五分块、四优化、六输入；每例16384/16641全元素 | `5.174333e-14` | 0/0 |
| ASan/UBSan | 1 | 5 | n129/O1、五分块尾块；每例16641全元素 | `4.110601e-14` | 0/0 |

两份 raw SHA-256 分别为 `95157345865bb314f9793178b3f16d86973eb17c4949ab5da4c2e202c0d3bbec`、`9d45c9f9383365f3e313bf025120cd711df3f8d8cd4191ff3e258d863f654c7d`；目标源仍为上述冻结 C，kernel 文本 SHA 为 `4005ab7de11a2336c300420cdf354b3ec2f05aa995be988b5008abdf21e382ab`。独立未分块 long double 点积是数值参考，checksum 不是全元素正确性证明。正式 n4096 两构建24点抽查与干净复现仍待执行，不能由这些小矩阵结果替代。

新大矩阵数值adapter已按真实临时源文件独立提取循环和SHA，n129/n4096六层内核与原附件及正式源逐字规范化一致（kernel4005ab7…）。argc仅恢复2参数接口，显式默认seed1/mode0；原checker的24个预定元素long-double逐项点积保持，数学链接flags仅给验证构建。大目标当前实际运行中，尚未记数值通过；此审核没有编译或启动目标，完整结果后再审。

大目标原始结果复核：O0/s24与O3/s128都真实检查24个预定元素，failures0，max_abs2.937539e-12、max_rel2.814528e-15；绝不称n4096全元素验证。四个诊断构建身份、真实输出、源码/二进制SHA、两个成功process及driver的first/previous ns派生保护均按独立stdlib重算一致；两个n129全元素smoke各16641点也通过。两次大目标控制资源271.091947967s，两个smoke另0.527333388s；大目标累计调用2，成本及clock-only绑定保留，不进入正式成绩。
