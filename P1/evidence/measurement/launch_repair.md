# 有限补诊断的启动修复

初次精确协议与计划冻结后，真实 `clock_followup.py execute` 在 `freeze_check -> plan` 中因缺内存运行时字段 `protocol_path` 抛出 KeyError。发生在第一个矩阵 task_start 前，矩阵调用仍为29。此前纯fixtures和手动传入完整字典的校验没有覆盖这条CLI入口，旧可执行放行已经撤销。

失败复现的完整 stderr 保存在 [launch-runtime-field-reproduction.stderr.txt](clock_followup/launch-runtime-field-reproduction.stderr.txt)。外层预留0-call资源、子CLI取得真实性能锁；0.119734568s MONOTONIC、0.120990698s RAW、0.119735178s REALTIME 已计全局账，不当作零耗时。此前尝试用通用受控wrapper再套同一锁，首先被锁拒绝；[launch-preflight-failure.stderr.txt](clock_followup/launch-preflight-failure.stderr.txt) 保留该不同错误，不能把它叫作KeyError复现。

修复只补入运行时 `protocol_path` 并增加不构建、不运行矩阵的 `check` 模式。新增测试实际调用parser和原freeze_check，仅隔离缓存可用性及fixture锁，随后还需实际CLI对本机缓存校验。13项独立fixtures通过；实际代码关和身份详见 [goal2_followup_code_review](../reviews/goal2_followup_code_review.md)。

原已冻结协议和计划不改写；修复版新协议/目录使用r1并引用旧身份。十二次调用数、顺序、2%关系门、520/16小时硬上限、计算内核和所有正式选择规则不变。它是同一次有限诊断的启动修复，不能再增加另一轮诊断来追逐稳定结果。
