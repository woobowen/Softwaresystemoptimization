# JDK 决策

Java 21 可以显示套件帮助，原版套件 checksum 通过，但初始功能检查发生 `IllegalAccessError`：`jdk.compiler` 未导出 `com.sun.tools.javac.main`，因此 check 失败，所选 compiler/XML 测试均没有进入测量。进程退出码仍为 0，原生报告的 Composite 1 不能作为 benchmark 分数。

这已满足 Java 21 止损条件：默认配置不能通过必需功能检测，且 SPEC FAQ Q4.8 还明确说明 Java 8+ compiler 和 Java 9+ XML 风险。不添加模块开放参数，不修改套件，不尝试通过跳过 check 获得正式分数。改用老师明确验证过的 OpenJDK 8u41 RI；用覆盖全套 workload 的短跑继续确认。短跑与正式 Base 分开。

记录：`installer-java21.log`、`java21-preflight/run.json`、`java21-preflight/console.log` 及其原生诊断报告。

## JDK 8u41 RI 的实际阻塞

2026-09-30 15:48:34+08:00 启动全套短跑。check 和 startup.compiler.compiler 通过；startup.compiler.sunflow 子进程停在 `FileOutputStream.writeBytes` → `javac.util.Log.warning`。该子进程 stderr 的管道容量为 65536 bytes。套件原始 `src/spec/benchmarks/startup/Main.java` 只启动 stdout 读取线程，没有消费 stderr。

15:50:30 左右仅为定位问题读取了子进程的 stderr，收到 151578 bytes，其中反复报告 Java 8 class major version 52 超过套件 javac 所支持的 51。读取后子进程立即退出，harness 继续。这是诊断干预；该短跑所有数值均不得用作正式 Base 或重复实验数据。没有修改任何套件文件。

证据：`jdk8-startup-sunflow-threads.txt`、`jdk8-startup-sunflow-stderr.txt`、`jdk8-preflight/`。不能在正式测量中用外部进程持续疏通管道掩盖兼容性问题。

官方 FAQ Q3.2 / Q4.8 及 Known Issues 8 把支持范围限定到 Java SE 7，并列出 Java 8 compiler 风险；建议跳过 compiler 的分析方法不满足本任务完整 Base 要求。已查到官方 GPL OpenJDK 7u75-b13 Linux x64 RI：https://jdk.java.net/java-se-ri/7 。当前提示词只明确授权 Java 21 → JDK 8 版本决策，因此已请求用户确认是否改用 JDK 7；尚未下载、安装或测量 JDK 7。

## 第三阶段：已授权 Java 7，完成全套预检并冻结

2026-10-01 的执行要求已明确授权官方 OpenJDK 7u75 RI，同时保留 Java 21、JDK 8、安装和缓存，不再存在 JDK 7 授权等待。官方 MD5 匹配；安装路径为 `~/.local/opt/java-se-7u75-ri/`，Java/Javac 1.7.0_75，VM 24.75-b04。

第一轮 JDK 7 全套短测自然结束，38 项计算、checksum 和初始 check 均通过，但报告绘图失败，79 个 JPEG 为空。原始失败报告保留在 `jdk7-preflight/`，不能作为正式结果。`font-probe/loader.log` 定位到系统 fontconfig 加载时缺少 `FT_Done_MM_Var`：JDK 自带旧 FreeType 与现代系统库不兼容。

处理方式是在实验进程设置 `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libfreetype.so.6`，使用已经安装的系统字体库。JDK 与 SPEC 文件均不修改，未添加 JVM 参数，未安装新字体或系统包，也不改全局环境。独立绘图程序和官方 reporter 均通过；后者完整生成 79 张可读图片，诊断 raw 的哈希不变。

第二轮全套预检为 `jdk7-preflight-fixed/`，命令仍为 `java -jar SPECjvm2008.jar -wt 5s -it 5s`，默认线程配置。2026-10-01 00:22:53 至 00:33:16（本地壁钟）自然完成，exit 0；38 项及其顺序完整，raw 无 correctness error，checksum 通过，TXT/HTML/summary/sub 与 raw 计算一致，79 张 JPEG 均可读，77 个本地 HTML 资源链接可访问。stderr 201117 bytes 均为 compiler.sunflow 的 unchecked 编译提示，无异常。唯一原生 violation 是缩短的测量时间。此结果仅用于诊断。

正式环境已冻结在 `../environment/formal-environment.txt` 与同名 JSON。完整 Base、三次原配置和三次参数实验使用同一 JDK、同一 runner 及同一 FreeType 兼容设置。原始 Java 21/JDK 8 诊断、两轮 JDK 7 预检全部保留。
