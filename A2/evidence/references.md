# 官方资料阅读记录

访问日期：2026-09-30T10:36:15+08:00。原网页缓存只保留于已忽略的 `materials/A2/official-docs/`，不作为成果重复发布。

读取方式：web 工具及 Python urllib 直接读取官方 HTTPS；D6 和 JDK 页面在 web 工具返回错误后，urllib 成功返回 HTTP 200。

| 资料 | 实际 URL | 页面 SHA256 |
|---|---|---|
| home | https://www.spec.org/jvm2008/ | `8e34a86517c10f5c74171484a4c1fc546ba7a25feae600f79965959c63ea81ba` |
| UserGuide | https://www.spec.org/jvm2008/docs/UserGuide.html | `1f6d1038d353a713562c872eba337c0c929f67134659330172b0f4e0d9c21757` |
| RunRules | https://www.spec.org/jvm2008/docs/RunRules.html | `5fcaaf25ea1843bb257c5b50eb562687031526f085f74926037afd1e7e6cf7e4` |
| KnownIssues | https://www.spec.org/jvm2008/docs/KnownIssues.html | `475de0b12e287d624639023123fdafd17bafc38ea3cea7d20257b57aecceca39` |
| FAQ | https://www.spec.org/jvm2008/docs/FAQ.html | `8d5359eb3b99412f4c6375bb57d492aeb434f639d11e52956f7495e0903defa4` |
| results | https://www.spec.org/jvm2008/results/jvm2008.html | `a18b060c30b2909a85b8799f6e3e9dd957a31269c0ff0ee8d0312c2f804559d2` |
| jdk8-MR3 | https://jdk.java.net/java-se-ri/8-MR3 | `78a0bebd0d283b3a40bdd6c6b690055631f8c4c0618991db43dfb7d582c1e075` |
| compiler | https://www.spec.org/jvm2008/docs/benchmarks/compiler.html | `705790283d3b8627cccfb32a63a82b7a12d7eaf78e01a6665a798990d5b73958` |
| compress | https://www.spec.org/jvm2008/docs/benchmarks/compress.html | `25bec3bd6d94adc393e46e49c674f14915f823b55b016bdd8b2597e190929372` |
| crypto | https://www.spec.org/jvm2008/docs/benchmarks/crypto.html | `62e4d76bc71be071f061a364665fc65d8c392c84eae68e4c1e8b324f92263e14` |
| derby | https://www.spec.org/jvm2008/docs/benchmarks/derby.html | `c0c5d50c0788fe0aff6c1a8200bd6740e8dfb45ff468de1ced800be1326e9152` |
| mpegaudio | https://www.spec.org/jvm2008/docs/benchmarks/mpegaudio.html | `2960e65580ad46aab51cf0c335c09ac0ba01aeb73743e15d459dfeeaee5d91a7` |
| scimark | https://www.spec.org/jvm2008/docs/benchmarks/scimark.html | `280047685bd61d3d50f92460bf94b8e9f8462045f37e77e1a8495663c463c6e5` |
| serial | https://www.spec.org/jvm2008/docs/benchmarks/serial.html | `6def191d03a11a46b6c47ef8e06f55b89fad1efd18d8eb0cdf046c28ffe44bbb` |
| startup | https://www.spec.org/jvm2008/docs/benchmarks/startup.html | `eec8a056b06805fc0ebdec3c1b2468651dcca242744ccbe4b48682b320b59193` |
| sunflow | https://www.spec.org/jvm2008/docs/benchmarks/sunflow.html | `9d6b47d0e977d902cc7f65ce8b84b04430a6401ed787b088e90cc705d28761d5` |
| xml | https://www.spec.org/jvm2008/docs/benchmarks/xml.html | `b1f19866d7eab6ea7f3a647e163b7ad1df743e00f8730c85aeeaa35258f00225` |
| official-summary | https://www.spec.org/jvm2008/results/res2015q1/jvm2008-20150120-00018.html | `81d53945c97e5082c7b75b2b39c0a8ea99400592341073d9b497dd60e9701a98` |
| official-base | https://www.spec.org/jvm2008/results/res2015q1/jvm2008-20150120-00018.base/SPECjvm2008.base.html | `8472daef33df919535faf0b21b02b7ecc3a8c72b92bd8f49002e56d4faf016b3` |

## 版本与适用判断

- User Guide：Version 1.0，页首 2008-04-16；在线文档同时包含 Lagom 和现行命令附录。安装后核对本地帮助和文档差异。
- Run Rules：Version 1.1，页首 2014-07-30；Java 规范支持至 SE 7。第 5 节允许清楚披露偏离的学术研究，但不替代运行正确性和完整性。
- Known Issues：Version 1.0，页首仍为 2008-04-12，但正文已包含第 8 条 Java SE 8 问题。采用具体条目，不把旧页首日期当作内容没有更新。
- FAQ：Version 1.3，2018-03-22；Q4.8 列明 compiler / startup.compiler 以及 Java 9+ XML 风险。
- Java 8 MR3：Reference Implementation，build 1.8.0_41-b04；Linux x64 包为 openjdk-8u41-b04-linux-x64-14_jan_2020.tar.gz，GPLv2，约 167 MB。是否需要安装由现有 JDK 的实际预检决定。
- Base 不带 JVM 调优参数，不缩短 120 s 预热 / 240 s 测量，不改 properties。发生真实 OOM 时才考虑 Known Issues 的 Base 线程适配。
- Valid 表示计算正确；Compliant 还要求完整套件、顺序和规则。单项运行的非整套警告不等同于计算失败。
- User Guide §6 将 SciMark 写成单个组；所选 2015 原生报告分为 scimark.large / scimark.small。最终总分以实际套件 Reporter 为准，不能直接平均所有子项。

## 已选官方对照

`jvm2008-20150120-00018`，Sugon I620-G20；首次发布 2015-02-23，测试时间 2014-12-25。已完整读取 Summary 和 Base Report，包括各 workload 明细及末尾套件版本 1.01 (20090519)。Base 853.15 ops/m，双路 Xeon E5-2660 v3，20 cores / 40 logical CPUs，256 GB，RHEL 6.5，Red Hat OpenJDK 1.7.0_45（24.45-b08）。

## 访问失败记录

SPEC 主页许可 PDF 链接使用相对路径；尝试官网标准路径 https://www.spec.org/spec/docs/sample_license_agreement.pdf 时 curl/urllib TLS EOF，web 工具也未成功获取。按主页相对链接解析出的 https://www.spec.org/jvm2008/spec/docs/sample_license_agreement.pdf 返回 HTTP 404。尚未声称读过许可正文，已按用户要求请求许可授权；未下载套件。

## 第二阶段复核

用户已明确接受许可，前一阶段的许可等待不再适用。2026-09-30 重新直接读取候选官方 Summary Report 和 Base Report（HTTP 200），内容哈希及访问时间见 `environment/official-recheck.json`；确认 Base 853.15 ops/m、2 chips / 20 cores / 40 logical CPUs、256 GB、RHEL 6.5、OpenJDK 1.7.0_45、测试日期 2014-12-25。保留该对照，不按本机分数挑选。

安装器兼容性参考： [OpenJDK ZipFile 源码](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/zip/ZipFile.java) 与 [OpenJDK CEN header 讨论](https://mail.openjdk.org/pipermail/nio-dev/2023-November/015321.html)。`jdk.util.zip.disableZip64ExtraFieldValidation` 仅用于诊断安装器；仍因 Java 21 缺少 `java.lang.Compiler` 失败。

再次核对 SPEC FAQ Q3.2 / Q4.8：Java SE 5、6、7 是列明的支持规范；Java 8+ 的 compiler 和 startup.compiler 是已知风险，排除 compiler 不能满足本任务要求。官方 JDK 7 RI 候选页 https://jdk.java.net/java-se-ri/7 已用 urllib 实际读取（HTTP 200）；其 GPL Linux x64 7u75-b13 下载链接 HEAD 返回 200、156554803 bytes，官方 MD5 为 `538acd35c6cf6977fa19d21ab2c17b0a`，见 `compatibility/jdk7-candidate.json`。这不表示已安装或已确认其兼容性。

## 第三阶段复核（2026-10-01）

已再次读取官方 JDK 7 RI 页面及 MD5，下载并核对官方 GPL Linux x64 包。信息见 `environment/jdk7-download.json`。官方 Summary/Base 页面与第二阶段字节完全一致，见 `environment/official-recheck-stage3.json`。

报告字体问题检查了 [OpenJDK 7 X11FontManager](https://github.com/openjdk/jdk7u/blob/master/jdk/src/solaris/classes/sun/awt/X11FontManager.java) 和 [Java 7 Font Configuration](https://docs.oracle.com/javase/7/docs/technotes/guides/intl/fontconfig.html)。`LD_DEBUG=libs` 实际显示系统 fontconfig 找不到旧 FreeType 中的 `FT_Done_MM_Var`；进程级预加载系统 FreeType 的绘图测试通过。SPEC Run Rules §2.4 的环境披露要求用于记录这一功能兼容设置；未添加 JVM 性能参数，不声称取得官方发表审核。

JVM 参数参考 [Java 7 Garbage Collector Ergonomics](https://docs.oracle.com/javase/7/docs/technotes/guides/vm/gc-ergonomics.html)，访问记录和页面哈希见 `environment/jdk7-gc-reference.json`。该 Java 7 页面明确说明 Server VM 的默认 Parallel GC 与 `-XX:+UseSerialGC` 切换方式。实际 JDK 的默认值、修改值与版本输出见 `parameter/default-flags.*`、`parameter/modified-flags.*`；采用实际输出确定参数，没有用当前 JDK 文档代替 JDK 7 行为。

已阅读安装套件的 `src/spec/benchmarks/compress/Compress.java`：performAction 创建输入/输出包装和 Compressor/Decompressor，后者创建辅助表数组。这是选择回收器比较的源码依据，不代表采集过 GC 次数或暂停时间。

原生 JVM 命令行字段的 n/a 行为参考安装套件 `src/spec/harness/Util.java:331–362`、`CommandLineParser.java:134–136`。采集该字段需要显式 `-pja`；为保持已完成原配置与修改配置的 SPEC 参数相同，没有追加该参数，见 `parameter/metadata-note.md`。计时行为的源码位置与实际观察见 `environment/timekeeping-analysis.md`。
