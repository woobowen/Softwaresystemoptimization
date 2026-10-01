# Runner 检查与修改

第三阶段开始时的脚本保存在 `../environment/checkpoint-stage3.json`。它已经把 Java 的 stdout 写入 `console.log`，并用 `stderr=STDOUT` 合并输出，没有为 Java 创建两个未读取的 Python PIPE。因此，不能把上一阶段实际发生的阻塞归因于这份 Python runner。

真实阻塞位于未修改的 SPEC `src/spec/benchmarks/startup/Main.java`：`Runtime.exec()` 创建 startup 子 JVM，套件只读取其 stdout，未读取 stderr。JDK 8 的旧编译器版本警告超过管道容量。证据沿用 `../compatibility/jdk8-startup-sunflow-threads.txt` 与 `../compatibility/decision.md`。本阶段没有改动这段套件代码，而是按照已授权方案使用兼容的 Java 7。

Runner 的改动限定为：stdout/stderr 分别直接写文件；记录两份日志绝对路径、Java 路径、results 根目录、wall time 和 runner SHA256；为 Java 建立独立进程组；收到 SIGINT/SIGTERM 时转发给该组，等待真实 Java 退出并保存退出码。没有 tee、shell wrapper 或输出读取线程。

`test-runner.py` 直接执行正式 runner，以临时本地程序替代 Java。stdout/stderr 各输出 307212 bytes，测试在程序退出前不读取日志，随后逐字节比较全部内容与尾部标记。退出码 0、7，SIGINT、SIGTERM，并发拒绝及已有输出目录防覆盖全部符合预期。结果见 `test-results.json`。

随后运行真实 SPEC 短测：JDK 8，`-jar SPECjvm2008.jar -wt 1s -it 1s -bt 2 compress`。14.141 秒自然结束，Java exit 0，checksum 与 correctness 通过，TXT 为 valid but not compliant（单项且缩短时长）。全部原生文件复制到 `spec-smoke-jdk8/native-results/` 并逐文件核对；不计入任何正式统计。

Runner 不会修复 SPEC 内部自己创建的管道，也不会把退出码 0 当成 correctness 通过。每次正式运行仍需检查原生 raw、TXT 与完整 workload 覆盖。

冻结前增加记录 `LD_PRELOAD`、`LD_LIBRARY_PATH`、`DISPLAY`、`FONTCONFIG_PATH`，以披露报告字体库的兼容设置。随后再次执行全部 runner 测试，通过；冻结脚本 SHA256 为 `902363d62d17a109faefa3de3ba49d76203757e81c23b976e21b958b534b98f6`。

## 第四阶段

历史冻结源码保存在 [frozen-run-spec.py](frozen-run-spec.py)，哈希与旧七次测量元数据一致。正式 runner 增加 Popen/wait 两侧的 realtime/monotonic 成对时间与明确 elapsed 字段，保留旧字段供历史读取；启动失败时也保存错误、退出码 127 和结束元数据。stdout/stderr、锁、信号和结果发现方式保持简单。

更新后输出压力、退出 0/7、SIGINT/SIGTERM、并发拒绝、覆盖拒绝、缺失 Java 路径均通过；[test-results.json](test-results.json) 对应当前源码哈希。真实 `.014` compress 自然结束，日志与完整原生结果正常保全；双时钟仍发现环境异常，runner 的测试成功不能代替计时可信度判断。
