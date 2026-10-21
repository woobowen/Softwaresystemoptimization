# README 与材料独立审查

审查者：原生独立代理 `/root/report_review`，未参与主要实现。仅阅读材料、源码、日志、图片及复算保存的数据；未编译、运行排序、执行 Perf/Cachegrind 或改动 README/源码。本文件是本次唯一写入文件。

结论：本地 README、结果呈现和截图审查通过，未遗留必须修复的问题。这是本地内部审查，不代表 ChatGPT 阶段验收、GitHub 最终验收或教师提交验收。

## 依据与连续阅读

- 首条命令为 `ls -la`，确认当前根目录存在老师 DOCX、AGENTS.md、P2/ 与材料缓存。
- 阅读根 `AGENTS.md`、老师 DOCX 的正文及关系文件、官方原题全文 `.cache/P2/materials/hw2.txt`；按用户批准范围把 Write-up 2、3、7 一并作为必须完成项。
- 初次连续阅读 README 第 1—181 行；主执行者修复截图并调整两处表述后，再次从头到尾连续阅读最终 181 行，逐段检查其回答的问题、解释边界和中文表达，而非仅搜索禁词。
- 原题顺序、两个 Checkoff 和七个 Write-up 均有对应回答；身份信息正确，系统概况只列操作系统、CPU、内存。未见内部代理或外部验收结论混入正式报告。

## 发现、处理与复核

| 严重度 | 位置 | 发现 | 处理与复核 |
|---|---|---|---|
| 中等 | README 第 166 行引用的 correctness-memory.png | 初稿截图底部包含故意破坏 sort_a 后的 FAIL 与 expected_failure_exit=1；正文没有说明这是负向诊断，可能被误读为最终实现仍错误。 | 已向主执行者报告。主执行者从正式截图脚本移除负向诊断显示，重新在真实 xterm 中截图；原图移至本地缓存，负向日志仍保留在 evidence。已重新打开最终 PNG，确认只呈现成功的正确性/内存检查。截图记录中旧图标为 superseded。 |
| 低 | README 第 168 行 | 初稿“各版本……1656 个”容易被理解为每个版本各有 1656 个。 | 主执行者改为“六个版本合计……1656 个”。已结合 tests.c 的 23 个长度 × 2 个偏移 × 6 种模式 × 6 个版本复核。 |
| 低 | README 第 8 行 | 初稿“可用总内存”容易混淆 total 与 available。 | 主执行者改为“WSL2 显示总内存”。保存的 total 为 16,561,393,664 B，约 15.42 GiB，与最终文字一致。 |

## 结果核对

- 独立读取全部 10 个有效计时批次的 samples.csv、summary.csv 和对应原始运行日志，共 490 个进程/输入均值、2450 次已记录排序耗时。逐一重算均值、中位数、最小/最大值、加速比，核对每组 5 个独立进程和所有单次样本：未发现不一致。未把预热或分析工具耗时混入正常时间。
- 重算粗化来源选择：中大规模两种输入的几何平均加速比 i=0.9901477、p=0.9269556；a 作为来源与报告一致。阈值 8/16/32/64 的综合耗时比分别为 1、0.9771240、0.9650916、1.0327305，报告保留不同批次的阈值与最终对照结果，没有混称同一批。
- 重算最终 m/f 综合加速比为 1.6771689/1.6764759，符合报告 1.6772/1.6765；报告同时保留 p 的退化、m 随机输入相对 c 的退化及 f 对 m 收益不稳定的结论。
- Checkoff 1 的 227 个软件事件样本、Self 100%、源码第 20 行 63.00%、11ea 指令 14.54% 均与 report/annotate/opcodes 一致。原始源码行、指令字节和汇编对应；未把软件采样或采样偏移解释成硬件 miss 计数或精确源码独占耗时。
- Checkoff 2 的全部五组 U/N 表格与 Cachegrind 原始计数一致；全进程百分比使用 D refs 为分母，源码第 32 行的随机读取计数另列。核对五份逐行输出，4 MiB 配置该行 LL miss 为 0，16 KiB 配置该行 D1/LL miss 为 0，原配置读行 miss 与报告一致。减少 N 没有被写成提高缓存效率。
- W1 的 flags、Cachegrind I/D refs 和 misses、Debug/release 正常时间与对应日志一致；报告区分 O0/O3、assert 与两者均有调试信息。
- W2/W3 的 inline remarks、实际调用、841 B 递归函数和 2 B 入口跳转与保存的汇编/符号一致。实际读取 inline.text/noinline.text，二者 SHA-256 相同；没有把未发生的递归展开或缓存恶化写成观测结果。
- W4 的 677 B 指针版本、I refs 与模拟条件分支误预测和记录一致。W6 的覆盖安全等式、空间元素数与当前源码一致；W7 malloc/free 计数 32767/1 与独立包装记录和递归节点推导相符。
- 正确性、ASan/UBSan、Memcheck 与极值日志支持报告的合计 1656 个逐元素对照、78 个 m/f 极值用例及内存检查结果；原始哨兵数据域限制在报告中明确区分。本审查没有重新执行这些程序。

## 图片、链接与文字

12 张最终 PNG 均逐张打开查看：lscpu、Checkoff 1 热点、Checkoff 1 源码/汇编、Checkoff 2、W1、W2/W3、W4、W5、W6、W7、全部版本性能、正确性/内存检查。文字可读，关键结果和代码上下文完整，未见虚假终端拼接；capture_terminal.py 使用真实 xterm/Xvfb，ffmpeg 捕获窗口。保存的命令与实际显示内容相符。

最终 12 条有效截图记录的图片哈希、命令文件哈希与命令文本全部匹配；1 条 superseded 记录不作为最终图片。README 的 21 个相对文件/图片链接全部指向现有文件。未见截图与最终代码或数值冲突。

最终文本逐题直接给出结果，必要解释围绕题目展开。环境限制、模拟与硬件数据、正常时间与分析工具开销均有清楚区分；没有据小幅波动声称确定加速，也未为文风删去必要技术限制。

## 本次审查绑定的文件

| 文件（相对 P2/） | SHA-256 |
|---|---|
| README.md | 2f128df051dfad89a5f31577af37c7d75998abc2e07ddd83180a15e2551aef91 |
| images/01-lscpu.png | 75b325fa7f190f8e5f20414786a3a91297d12f2ab6238acd219b98babce58bea |
| images/checkoff1-perf-report.png | 9ee53f88c702b7b1ed9f86aec6e73464ee19545abfd713323a10c7b2b4b8f956 |
| images/checkoff1-perf-annotate.png | 3e90e640d7c64444da930a70868b4a995b0c26fdcfdcc9bc64caa6c14f812770 |
| images/checkoff2-cachegrind.png | 5a8c5d8b5afeb5d4d7a314b5b119f323e6854482c0179f31b00b0729af5927ce |
| images/writeup1-build-comparison.png | dfd5530fc14494b62d6c556ebba9a252d94fce4c39dd8e4191bc51274804eb33 |
| images/writeup2-inline-assembly.png | 5ce6087d245e5c36781d8af3c699d1213e7ca112374081b5a9603f9c94a3ff2f |
| images/writeup4-pointer-merge.png | 1c0a4fc42ec988c457b176007f0e27475426b0b4f690cc4cd3aedbe550c871a7 |
| images/writeup5-threshold-results.png | 898d116470dd6de213e95e7112220bde501fda5982b0d6983eae72541e3387ab |
| images/writeup6-single-buffer.png | 960a66c4bf2265f81a18bd749040d4f80a578888fdc69fe20a73d05fac034b73 |
| images/writeup7-profiling.png | ca246b48777c6ba4071dc0dd7551b07a3fcac06778fe4d4e89c0e1c885b8f1e4 |
| images/all-versions-performance.png | fd295ef9b551239ab203a5250e826429902b5b0efb2133858092e0f947873676 |
| images/correctness-memory.png | c8e34ac13ef38bc41bb476aceb7cd777d2d426fef2b75809a42d817bac6003a6 |

审查限制：仅审本地已保存内容，没有重新测量；完整代码正确性另由代码审查者负责。未检查尚未发布的 GitHub/水杉最终树，也未对最终压缩包作超出本文件范围的验收。
