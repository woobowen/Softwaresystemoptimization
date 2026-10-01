# 最终正式脚本检查

完整连续阅读了 [run-spec.py](../../scripts/run-spec.py)、[summarize-spec.py](../../scripts/summarize-spec.py)和 [run-formal.sh](../../scripts/run-formal.sh)。源码 SHA256、逐文件说明及读取时间见 [script-review.json](../formal-campaign/script-review.json)。

- runner 直接调用 JVM，stdout/stderr 写入独立文件，保留退出码、信号转发、互斥与防覆盖；新增 campaign、boot ID、服务状态等观测字段，实际进程 cmdline 与 argv 一致。六个假进程场景通过，见 [runner-tests-final.json](../formal-campaign/runner-tests-final.json)。
- parser 未引入任何最终成绩常量，从 raw 的 operations 和 elapsed 计算 workload/group/composite，并核对原生 TXT。最终新 raw 的十五个用例及直接 XML 数学复算通过，覆盖 38 workload、group/child/startup 区分、统计和异常输入；见 [parser-tests-final.json](../formal-campaign/parser-tests-final.json)。
- shell launcher 仅设置 JDK、SPEC、locale、FreeType，清除 Java option 环境变量后 exec runner；没有额外 JVM 调优。
- Host wrapper、监视器、截图和内部检查均在 evidence/tools。计时检查十个合成异常场景通过，见 [timing-fault-tests.json](../formal-campaign/tool-self-check/timing-fault-tests.json)；新运行的实际检查见 [final-data-audit.json](../formal-campaign/final-data-audit.json)。
- 26 个 Python 文件的 AST、正式 launcher 与五个截图命令的 bash -n 通过；远端浏览器工具通过 node --check，见 [syntax-final.json](../formal-campaign/syntax-final.json)。Gate 的 Java 源在正式探针中编译并运行通过，四个既有探针文件保持原样。

正式 scripts/ 保持三个文件。以上是本地源码和执行检查记录，最终代码质量与工程验收仍由独立审阅决定。
