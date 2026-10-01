# 环境变更记录

截至许可确认前：没有新增系统包、pip/npm/cargo 包、JDK 或 SPEC 安装；没有修改 shell 配置、alternatives、WSL 资源限制或其他项目配置。

复用：OpenJDK 21.0.12.1、Python 3.12、BeautifulSoup、Pillow（XCB）、pdftotext、Zutty、Xvfb、Chromium 缓存。原始 JDK 和全部全局环境保持原样。

初始截图：Zutty 在临时 Xvfb display :91 中实际执行环境命令，再用 Pillow ImageGrab 直接截取 X11；对应终端记录为 `01-initial-java-environment.terminal.txt`。捕获后停止本次启动的终端与 Xvfb，没有停止用户程序。

Chromium 官方页截图尝试：在线页面等待 45 秒、原样保存的本地 HTML 等待 25 秒均未生成截图。日志分别为 `official-screenshot.log`、`official-screenshot-local.log`。没有制作替代的仿页面；需要页面截图时可复用真实终端展示已下载的官方文本。

## 第二阶段（2026-09-30）

用户已经接受 SPEC General License Agreement，许可等待已解除。官方下载 URL： https://www.spec.org/downloads/osg/java/SPECjvm2008_1_01_setup.jar 。下载缓存位于 `~/.cache/a2-downloads/`，拟安装于 `~/.local/opt/specjvm2008/`。第一次 HTTPS 连接提前关闭（curl exit 18，收到 6,679,889 / 67,054,942 bytes），对同一官方 URL 使用 HTTP Range 断点续传。SPEC 官方 MD5 索引未列出此包；下载后保留本地 SHA256 和套件内 checksum 验证。

Java 21 的 ZIP 读取器拒绝旧安装器 CEN extra field；使用 OpenJDK 的 `-Djdk.util.zip.disableZip64ExtraFieldValidation=true` 只用于安装器排查后，报 `NoClassDefFoundError: java/lang/Compiler`。停止修补该安装器，采用老师建议的官方 JDK 8u41 RI 安装；之后仍将用 Java 21 检查已安装 benchmark。没有改动安装器字节。

安装完成：SPECjvm2008 1.01 (20090519)，路径 `~/.local/opt/specjvm2008/`；OpenJDK 1.8.0_41-b04 RI（VM 25.40-b25），路径 `~/.local/opt/java-se-8u41-ri/`。JDK 官方 MD5 与本地匹配。套件的 777 个初始文件已记录 SHA256；未改动 benchmark、properties 或校验逻辑。Java 21 预检中套件 checksum 全部通过，随后 check 因模块访问 `com.sun.tools.javac.main.JavaCompiler` 被拒绝而失败。

新增系统包：无。新增 pip/npm/cargo 包：无。全局 shell 配置、alternatives、WSL 配置：无修改。下载包留在仓库外。

安装器另写入用户级注册文件 `~/.com.zerog.registry.xml`（1637 bytes，含 SPECjvm2008 安装/卸载位置）；它不在仓库中，不是 shell/系统 Java 配置。新增工具链仍为 SPECjvm2008 与 OpenJDK 8u41 RI。

第二阶段截图：复用现有 Node Playwright + Chromium 成功截取未经改动的官方 HTML；安装与兼容错误使用现有 Zutty/Xvfb/Pillow 直接截图。Xvfb 自动 display 选择未及时就绪，切到前阶段已使用的临时 :91 后成功。所有本任务临时 GUI 进程已退出，无新增依赖。

JDK 8 全套诊断在 15:55:35+08:00 结束；因 startup 子进程曾被外部读取 stderr，整次结果不用于正式成绩。正式 JDK 尚未冻结，JDK 7 仅核对了官方页面、下载 HEAD 与 checksum 文本，未下载或安装。

## 第三阶段（2026-10-01）

从官方 GPL OpenJDK 7u75 RI Linux x64 包安装到 `~/.local/opt/java-se-7u75-ri/`，沿用 archive 原始目录名。官方 MD5 核对匹配；本地 SHA256、URL、文件大小与日期见 `jdk7-download.json`。缓存保留于 `~/.cache/a2-downloads/`。Java 21、JDK 8 和 SPEC 安装保留；没有 apt/pip/npm/cargo 安装，也没有修改全局 Java alternatives、shell、Windows 或 WSL 配置。

JDK 7 报告字体兼容：系统 fontconfig 依赖 `FT_Done_MM_Var`，JDK 7 自带旧 FreeType 未导出该符号。使用已有系统库 `/usr/lib/x86_64-linux-gnu/libfreetype.so.6`，仅在实验进程设置 `LD_PRELOAD`；FontProbe 绘图通过。没有替换 JDK 文件、安装字体或系统包，也没有全局环境修改。库版本/哈希与诊断见 `../compatibility/font-probe/`。

截图资料整理补充：早期 `01-initial-java-environment.terminal.txt` 实际为空，不能作为有效的文字转录；保留该历史文件，初始环境事实见 `initial-environment.txt`。01、02、03 图片保留为历史资料，最终报告使用新 JDK 7 环境和正式实验截图。各图来源及哈希集中记录在 `screenshot-provenance.json`。

## 第四阶段（2026-10-01）

新增系统包、pip/npm/cargo 包、工具链：均无。复用现有 JDK 7、GCC、Python、PowerShell、Pillow 和 pdftotext。ClockProbe.java、read-adjtimex.c 的编译输出使用仓库外临时目录并自动清理。未修改 Windows、WSL 时钟源、时间同步、shell 或 Java 全局配置；仅提出临时时钟源诊断请求，尚待批准。

## 第五阶段（2026-10-01）

新增系统包、pip/npm/cargo 包和工具链：均无。复用现有 JDK 7、Python、Pillow、Xvfb、Zutty。`sudo -n true` 因无缓存凭据返回 1；随后通过现有 WSL `--user root --exec` 入口执行用户已授权的单次 sysfs runtime 写入，回读确认 clocksource 为 `hyperv_clocksource_tsc_page`。切换命令与时间见 `../timing/clocksource-after-switch.txt`。没有修改 sudoers、Windows 时间服务、`.wslconfig`、kernel boot、shell 配置或全局 Java 设置。实验结束时必须恢复原值 `tsc`；恢复状态以 `../timing/clocksource-restored.txt` 为准。

第五阶段收尾：两次 600 秒探针均未通过。2026-10-01T11:27:11+08:00 已通过同一 WSL root 入口恢复 `tsc`，退出码 0 并回读确认。没有新增任何包或工具链，没有持久化配置变更；本次 Java/C 临时编译目录由 TemporaryDirectory 清理。新环境截图仅执行版本/环境读取，没有恢复后性能测量。

## GitHub checkpoint 发布（2026-10-01）

没有新增系统包、语言级包、工具链或字体；没有修改 shell、环境变量持久化文件、Windows/WSL 全局配置或 clocksource。复用 Python 3、现有 JDK 7 `javac` 和 C 编译器，只做离线检查及编译；未执行 timing probe。Java 编译输出和 runner 假进程测试放在自动清理的临时目录。本次仓库配置仅补充 `.gitignore`；AGENTS.md 保留此前新增的长期规则。已有 JDK、SPEC 和仓库外下载缓存保持原位，不上传。
