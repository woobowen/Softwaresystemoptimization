# 原生 JVM 命令行字段

参数 smoke 的 checksum、correctness、报告和图片检查均成功。随后附加检查误以为 raw 的 `spec.jvm2008.report.jvm.command.line` 会自动包含 `-XX:+UseSerialGC`，因此触发了一次 AssertionError。启动三次正式参数实验的代码在该断言处停止，未启动任何额外正式运行。

实际读取字段为 `n/a`；`smoke/run.json` 中完整命令明确含有该参数。未修改的 SPEC 源码说明：`Util.java:331–362` 仅在 `Launch.parseDefaultArgs` 为 true 时通过 RuntimeMXBean 读取参数，`CommandLineParser.java:134–136` 由 `-pja` / `--parseJvmArgs` 开启这一行为。此次所有正式单项的 SPEC 参数都是 `-jar SPECjvm2008.jar compress`，没有加入 `-pja`，也没有修改 reporter properties。

修正的是附加检查的依据：使用 runner 记录的实际 argv、参数前后的 PrintFlagsFinal、运行中 `/proc/PID/cmdline` 和完成情况检查参数。`default-flags.json` / `modified-flags.json` 显示 UseSerialGC false→true，UseParallelGC true→false，初始堆和最大堆数值相同。保留原生报告的 n/a 字段和分类，不补写或修改 raw、HTML、TXT、summary、sub，也不为了补充元数据重跑或改变既定的六次实验条件。

原生报告的类别和合规提示不代替实际 JVM 参数检查。参数实验是 compress 单项的调优配置比较，不能当成默认 JVM 配置下的完整 Base 成绩。
