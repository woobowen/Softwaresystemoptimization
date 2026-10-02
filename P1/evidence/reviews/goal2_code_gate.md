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
