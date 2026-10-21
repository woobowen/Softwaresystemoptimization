# P2 独立技术审查

审查者：原生子代理 `/root/code_review`。未参与主要实现，与 root 为不同代理。技术检查只读；仅在 root 明确授权后写入本文件。结论只用于本地交付，不代表外部阶段验收、GitHub 工程验收或教师提交验收。

## 实际检查对象与方法

- 首个命令为 `ls -la`：目录包含根 AGENTS.md、P2 老师 DOCX、已有 A1/A2/P1，以及本次刚建立的 P2。本代理没有改动其他作业。
- 阅读根 AGENTS.md、当前用户范围、MIT 原题全文 `.cache/P2/materials/hw2.txt`，以及官方 starter 的 homework 和 recitation 相关源码、Makefile。老师 DOCX 由 root 负责实际提取，本代理未独立提取 DOCX。
- 在实现过程中分阶段读取统一驱动和各版本，随后完整阅读最终六版、头文件、插入排序、Makefile、三个辅助脚本及两个内部小 harness。用 `diff` 确认 sort_a.c 和 util.c 与下载的官方原件逐字相同。
- 阅读正常计时协议、逐次日志、全部 samples.csv/summary.csv、阈值选择、W1/W3 和六版本 Cachegrind、Perf report/annotate、汇编、inline remarks、内存检查与失败传播证据。
- 连续阅读完整 README，逐项核对技术表述、数字、单位、统计量、输入类型以及修改前后的关系；复核其中所有性能表格和主要结论。文风、截图可读性与全包文件检查另由 root 和文档审查者负责。
- 用 Python 标准库仅解析已有 CSV/JSON，独立复算均值、中位数、最小值、最大值、加速比、阈值指标以及 Checkoff 2 汇总；没有执行被测排序或分析工具。
- 最终再次连续阅读全文，确认内存为“WSL2 显示总内存”、qsort 为“六个版本合计”。另实际查看重拍后的 correctness-memory.png，终端内容与 ASan/UBSan、极值和 Memcheck 日志一致，未混入内部故意失败诊断。
- 读取最终 artifact-index.json 与 build-index.json，独立逐项比较最终 16 份源码快照、索引 SHA 和实际 homework 文件，全部一致；all-versions 的二进制 SHA 与保留的 final-release-sort 一致。

## 发现、提醒与 root 的处理

| 项目 | 严重度与实际位置 | root 处理与复核 |
|---|---|---|
| starter 驱动缺口 | 影响测量与失败识别：tests.c 的跨输入累加、未连通的随机状态、仅打印失败、错误的零元素测试及 `&&` 守卫判断；main.c 的重复 sort_a | 最终 tests.c:63 接种子，186 按输入清零，47 的失败宏计数，main.c:138 返回失败；空区间、单元素和逐元素参考用例均不依赖 assert。已读正常、sanitizer、Memcheck 证据。 |
| 原版哨兵的数据域 | sort_a.c、sort_i.c、sort_p.c、sort_c.c 均可能把真实 UINT_MAX 与哨兵混淆，不能把它们当作完整 uint32_t 域实现 | 保留原版，正式比较固定共同的 `[0,2^31)` 域；README 明确区分。m/f 去除哨兵，另测包含 UINT_MAX 的 78 例，没有把此结果泛化到其他版本。 |
| 插入排序边界 | 原始 recitation/isort.c 可形成 left-1 指针，不能直接带入粗化版本 | 保留原始 profiling 对象；homework/isort.c:38 在访问 pos[-1] 前检查 pos > begin，不形成起点前指针。 |
| 热点行号与采样含义 | Checkoff 1 annotate 的源码正文显示编号容易与真实行号混淆；软件样本不能写成硬件 cycles 或精确语句耗时 | README 使用真实第 20 行、63.00% 局部样本与 0x11ea 指令；注明 cpu-clock:u、227 样本、无丢失和采样位置偏移，不归因为未经测得的 cache/branch miss。 |
| Cachegrind 分母 | Checkoff 2 全进程 D refs 含 rand_r/初始化，与随机读取行的访问次数不同 | README 分开报告全局率与第 32 行的 99.88%/37.23%；固定 U 改 N 只减少总工作，不误称命中效率改善。数字与逐行 annotate 相符。 |
| 实际内联与递归 | 关键字不证明内联；本机 Clang 明确拒绝递归内联 | copy/merge 的 remarks 与汇编匹配；递归 call 保留、函数 841 B。noinline 对照 .text 相同，README 不把独立时间样本差异解释为递归内联收益，也不编造代码膨胀。共享 util 未改。 |
| 内存与指令权衡 | m 相对 c 的 D1 miss 降低，但 I refs 和总分支数升高；模拟误预测总数没有升高 | README 只陈述省复制/分配与边界控制的权衡，不把 random 退化无依据地归因为 branch miss。f 的小收益和部分规模退化保留。 |
| 内部实验来源 | 仅有输出而无小 harness 或最终采样来源，会妨碍审核包复现 | root 收入 check-extremes.c、count-allocations.c、sum_controls.py，并扩充 provenance.md 的最终版本、noinline、计数来源。sum_controls.py 增加 --local/--output，可在新目录复跑而保留旧证据。最终索引已生成并完成上述交叉检查。 |
| qsort 用例数表述 | 低：初稿 README:168 的“各版本……1656”可能被理解为每版 1656 | root 已改为“六个版本合计……1656”；再次读取确认。仅文字澄清，无需重跑。 |

前述 starter 问题已由用户要求提前指出，本审查者确认其存在和最终修正，不将其全部归为本代理首次发现。未发现仍需修改的阻塞级或重要级技术问题。

## 算法与验证结论

- 六个外部入口的函数类型保持一致，内部复制、归并和递归助手保留 static；主体仍为单线程递归归并排序。
- m 的不变量为 `k = p + i + (j-q-1)`，因此 `j-k = n1-i`。左侧未耗尽时 k<j，写入不覆盖未读的右侧；左侧耗尽时 k=j，右侧剩余元素已就位；右侧耗尽则复制左侧余量。
- f 为任意非零起点的 n 元素区间分配 ceil(n/2) 元素；任一后代的左半长度不超过该容量。子递归返回后再写入当前层左副本，复用不依赖尚需保留的其他层缓冲内容。分配和释放都在一次外部调用内部，没有全局跨调用缓存。
- release 的 1656 例为 23 个长度 × 2 个偏移 × 6 个模式 × 6 个版本，qsort 对独立副本排序后比较全数组，包括区间外守卫。空区间未通过 N=0 的完整驱动调用。
- 阅读 root 的 ASan/UBSan 与 Memcheck 日志：前者在 NDEBUG 下执行全部 1656 例，未报告错误；Memcheck 为 0 errors，退出时 0 bytes，196835 次分配与释放相等。
- 78 例为 13 个长度 × 3 个极值模式 × m/f 两版，p=3，完整数组比较。检查了实际 harness，容量和边界合理。
- failure-propagation.txt 使用能保持有序却破坏元素的诊断替身，qsort 用例捕获差异，实际预期失败退出为 1。不能仅凭“Arrays are sorted”或退出 0 接受排序，最终驱动已弥补该缺口。

## 独立数值复算

10 个正常计时批次共 245 次正式进程运行，保留 490 条按输入类型区分的进程平均值和 2450 条单次排序时间。每组 run 均为 0..4；所有均值、中位数、min/max、加速比复算无不一致。all-versions 为 90 次正式进程、180 条均值、900 条排序时间，预热单独保存且未混入。

| 复算对象 | 结果 |
|---|---:|
| 粗化前 i 的中/大规模两输入几何平均加速比 | 0.9901477095866678 |
| 粗化前 p 的同一指标 | 0.926955553436415 |
| 阈值 8 / 16 / 32 / 64 相对 8 的几何平均耗时比 | 1 / 0.9771240364366658 / 0.9650916431615669 / 1.0327304972124816 |
| 最终 m 的中/大规模两输入几何平均加速比 | 1.6771688781103111 |
| 最终 f 的同一指标 | 1.676475937312622 |

Checkoff 2 五组 D refs、D1/LLd misses 及百分比也与 provenance.json 中 Dr/Dw/D1mr/D1mw/DLmr/DLmw 的原计数逐项一致。README 的 W1、W2/W3、指针版、阈值及 m/f 数值按显示精度与这些证据一致。32 只作为本次有限候选的选择，不声称通用最优；m/f 也不被宣称有稳定显著差异。

## 归档来源补充复核

root 归档检查最初按 metadata 的历史执行路径读取二进制，因源码目录已清理而遇到 FileNotFoundError。该路径并不保证在后续重建、清理后仍有效。本代理读取新增 fixes.md、inline-binary-reconstruction.txt、binary-resolution.json 与更新后的两个索引，按文件内容而非历史同名路径复核。

- 对 artifact-index.json 的 **94 个唯一路径**实际逐文件检查：文件全部存在，字节数与 SHA-256 全部一致。
- 10 个正常计时批次均有 **1 个完整 SHA 精确匹配**的保留程序，且 resolution、build-index 与原 metadata 的 SHA、历史路径对应一致。粗化前批次复用相同 SHA 的 W1 release 程序；最早 inline 批次使用明确标记的恢复件。
- 最早 inline 原件被阶段重建覆盖。root 以 W1 快照恢复当时 15 份 C/h 文件，逐文件对照仅 main.c 的 sort_p 注册行和 sort_p.c 不同；sort_p.c 逐字等于官方未实现 stub，其余 13 份代码相同。W1 快照另有一个 sort 二进制，未放入恢复源码目录，不属于源码差异。
- 恢复日志使用原 O3/NDEBUG/g/gdwarf-3 等 flags，另以 `-fdebug-compilation-dir` 保持原调试信息中的目录。实际读取恢复件计算出的**完整二进制 SHA**为 `7b6eaca3379fe858b36738ce2a8393cf46852a21f3137a62024ab01cf89f4371`，与最早 metadata 完全一致。因此恢复件没有被当作“相近版本”替代原构建。
- 阅读 root 对恢复程序运行 sort_i、N=129、R=1 后的 276 例 qsort 复现日志；本代理没有重新编译或执行程序。该复现不参与正常性能统计，也没有替换旧计时。
- 对先前 58 项绑定重新计算，只有两个来源索引改变；全部已绑定代码、README、截图和原始计时 samples.csv 都保持原 SHA。来源修复未改变实验结果或正式结论。

补充复核结论：历史路径失效与最早构建覆盖问题已有可追踪修复，10 批二进制和 94 个本地原始材料的对应关系成立，没有新增未解决技术问题。下方索引绑定已经更新，并增加此次实际检查的文件。

## 没有做的操作与结论边界

本代理没有执行 make/clang、排序程序、Perf、Cachegrind、Memcheck 或 Sanitizer，没有调度性能负载，没有安装软件、改配置、改主要源码、提交或推送 Git。实际执行由 root 唯一调度；本代理阅读其原始输出，并独立检查代码和数据算术。没有把查看日志表述为重新运行实验。

本地技术结论：所审查实现、测试结构、保留结果与 README 技术解释可用于本地完整审核包；没有未解决的阻塞级技术发现。硬件事件不可用、原基线哨兵限制及小差异不确定性均已保留。此结论不代替独立文档审查、最终包校验或后续外部验收。

## 审查快照

下表由本代理读取实际文件计算，绑定本次审查的源码、README 和关键数据。文件改变后应复核相应部分并更新绑定。完整原始采样与匹配二进制索引由 root 另行维护。

| 文件 | SHA-256 |
|---|---|
| `P2/README.md` | `2f128df051dfad89a5f31577af37c7d75998abc2e07ddd83180a15e2551aef91` |
| `P2/evidence/review/check-extremes.c` | `b5c8d898903a60e427df005d0cf24133fab5c0e773b7afd48ab77f55e38c9393` |
| `P2/evidence/review/count-allocations.c` | `9d54cea123fcd3b6619be5317504304f694af86533ef6eb55ae7ad7d4f2ee85e` |
| `P2/homework/Makefile` | `0695cb61587862f80e411fd76cd2bca3ab9a4bcb6a30ba6cb2f28e59d57d3bd9` |
| `P2/homework/coarsen.h` | `e922f18a49b58ead010b3a90b8dfb4ca13ec2fb9252b5cc239f5cb3a0d1a9455` |
| `P2/homework/fasttime.h` | `8f1233cbb6c78c102d3b0d9cc08593c11d8c843706de716220f140414ec7923c` |
| `P2/homework/isort.c` | `323bf382c05d5bfc45d8d1d0ef0d6859b286e3ef3997e3e8ec3e3d201ae9d64c` |
| `P2/homework/main.c` | `09ed59133fe30d080fd41d508af48646be0ac0abf3326fb8e28f52627eb13a8d` |
| `P2/homework/sort.h` | `93aa3b48914b69426d26b1f3e13ad808a5e2c7b624e92a38736ef86e05b78c43` |
| `P2/homework/sort_a.c` | `fc509ecb57d326cde6c0911e94fc17a255f76a240124511016f532bdff3dc15a` |
| `P2/homework/sort_c.c` | `72ec0e9f34577839fea6e31cd90e3ca74654c440f1ce6e4f8626a524a973cec9` |
| `P2/homework/sort_f.c` | `a1059f32fb016f9a7e27bc2a59941036e2360a2f30b5a163152d4c9f841b1650` |
| `P2/homework/sort_i.c` | `657aaae43b4aef69789d1e42de1220cde5a092a6e98c4fa5fd47a032596b3b34` |
| `P2/homework/sort_m.c` | `5a6bb1cc8a8b7dc3e61da727a8e95f67fdbbc1192ea855adb1b8b09d32322777` |
| `P2/homework/sort_p.c` | `8025ec2aeb63855fd9757d571ed98a8359187015884b670fb0b4706d57496f85` |
| `P2/homework/tests.c` | `40667998a470d2f97d94a8cc7208c748b0c85620fb745d9191552436bb92b0f0` |
| `P2/homework/tests.h` | `7661833655d057a87d3bbabde48d1e354931cdc6db9f2e5bf044cf94a79a1a21` |
| `P2/homework/util.c` | `373b15640c5fcabda6d9e700de4007b1ebd00aca1177727a1c0fad591e401bc5` |
| `P2/homework/util.h` | `00238d0b8e93937c4895e7628e9aa081bd23fd7f5613de2c733b8f270c46a93a` |
| `P2/recitation/Makefile` | `1acfb6fff1859fe5c3e86c1d0599a040e3e98042b0e4d703ca010e4c07683b9a` |
| `P2/recitation/isort.c` | `3fddf1ce89acfae4bf0cef92e95073bdf9273a4eef18310daeb1472e9db9ea1a` |
| `P2/recitation/sum.c` | `26898636aba35823fb423e1ba0b865b9174dd8503a3f95369c07bb19f9234ed4` |
| `P2/scripts/capture_terminal.py` | `e7dbdaa7b62c24c62ad668a54648a517c54455a13d2138a1dd6b05d2ac541cce` |
| `P2/scripts/measure.py` | `ed2f0542f2996d1794d61553734404bf97c56fa3f153a29768ce0051ad11701e` |
| `P2/scripts/sum_controls.py` | `c17e5da043cfde09e83d643d972a9a43ea42c714347e562a79ef837ba98f5144` |
| `P2/evidence/performance/all-versions/samples.csv` | `05233531414def729b563553b3a95fc11ad3efd74c804452babdabf656b02ad7` |
| `P2/evidence/performance/inline/samples.csv` | `76fdd8f7171f24224106970a2706209b7bd612030588760eacdd5165ecebb592` |
| `P2/evidence/performance/pre-coarsening/samples.csv` | `09f65f0fc76b3e7e7cdb24b324edaf7a3ee38b8ee5f058b9fad69e54a3bcba6c` |
| `P2/evidence/performance/recursive-noinline/samples.csv` | `5405a6f4353617c8004d959d6418b9a144f5cfe589e43ce4de66336a18065dca` |
| `P2/evidence/performance/thresholds/t16/samples.csv` | `9843d48a2ec4e445e90a8949b137a07d17a16cfe8e3147834580b39156a7bd62` |
| `P2/evidence/performance/thresholds/t32/samples.csv` | `7783a8bca924fc403a6fe4a426ce0abd3f9e8f7ed8135925f656f5b96147eeff` |
| `P2/evidence/performance/thresholds/t64/samples.csv` | `b464056a2f005e5e55262eb5fe39c411751b8ea613f80bc120fc85293f5aafc0` |
| `P2/evidence/performance/thresholds/t8/samples.csv` | `35e8d507dd75b36312a7722fdd19c5b87799be31e789397314e9278564caf4e2` |
| `P2/evidence/performance/writeup1-debug/samples.csv` | `f0489248446ad759b7357d1eb75fa8a74edd73f8140d2db62a66a8139684694a` |
| `P2/evidence/performance/writeup1-release/samples.csv` | `a4f858c8a8524f570c0b852eb7ae7225b0102ea1376d4893091b3b7085f83004` |
| `P2/evidence/performance/protocol.md` | `263b49d579ad2d7d544c720ebb5f34670b886697511c628b452edec7104acaa1` |
| `P2/evidence/performance/all-versions/summary.csv` | `f95b92d2ba694df2c202d7386281a058cb2743d478af6a6ab34743a46ace0553` |
| `P2/evidence/performance/pre-coarsening/summary.csv` | `79464d2a0fd0d291f2b4afcf46c17c9b0a5086a11fe39d2145911efb4a460ce0` |
| `P2/evidence/performance/thresholds/selection.json` | `17be7d24f89a0c2d7ce3b315db5fa5319e66304d77969e4c1bccdbc6b0bd3288` |
| `P2/evidence/profiling/checkoff1/report.txt` | `859cbd3cc65a387de501ee1c034de54ed983f17450020a2233cafe2bf2e80567` |
| `P2/evidence/profiling/checkoff1/annotate.txt` | `70244044d48887a3ca0bcff5cbd1d213ede00f43356703c1c1149193e465736d` |
| `P2/evidence/profiling/checkoff2/provenance.json` | `9837790db59314bc0f4a97b41661ac94128f70563fb5c2da90f4ef84b9cd565c` |
| `P2/evidence/profiling/checkoff2/summary.csv` | `21329e64127650d1c26821923fc9b3d96313c025fab290526d4ce12853ef13e5` |
| `P2/evidence/profiling/writeup1/debug.txt` | `93d37bcc80601614abeeb47698a0a9c8f4f3c63c7e78e5dfc4bcb6c5147f1e4d` |
| `P2/evidence/profiling/writeup1/release.txt` | `e97c61e724b3bced7c2a3a11b0cf250502cab8af4fefc0e4a14ba38102cfe0d5` |
| `P2/evidence/profiling/writeup3/text-sha256.txt` | `7522427f62a5562003e8c65a6be996d98b75fb341d9ce44a7c25122347405446` |
| `P2/evidence/profiling/writeup3/noinline.diff` | `d940307f52767affbb3bd4664b68d668020580e6f309203e72c1759bdedd1829` |
| `P2/evidence/profiling/versions/inline-remarks.txt` | `feab3d9a3b86d0bbeb8207311a5e86e461184cb0573e86e83324f09e22846df5` |
| `P2/evidence/profiling/versions/allocation-counts.txt` | `28393a4320ed9647d3a5e5f1efed28d5f94032b80944080599c32ae8ef0f1f31` |
| `P2/evidence/profiling/perf-versions/sort_m-report.txt` | `f482e03f1f0070572f1c89172565032e8b980f3cbe62d3f7441a1a2688548ff9` |
| `P2/evidence/profiling/perf-versions/sort_f-report.txt` | `8847f3f7354a32aa2ce31ec5811a69c3aed59b6ec2e0bc92a226065f32568a6e` |
| `P2/evidence/correctness/asan-ubsan.txt` | `d8a113d03474e892904b7771b881de690d6649aa5abf5f435124fa469ea33bc6` |
| `P2/evidence/correctness/memcheck.txt` | `cdb2dd806aa9cf4aa218a4077bd7713a1bf12db5ccd2045d491306642d5b14c8` |
| `P2/evidence/correctness/extremes-asan.txt` | `b1ac1386cd426f430b9f1cfe09e7d686090c0e9aca2e05af73006b39a918a537` |
| `P2/evidence/correctness/failure-propagation.txt` | `b61048161406a3e4167f66635e343834bc37f68988cd56ca83873a86b66d76cf` |
| `P2/evidence/profiling/artifact-index.json` | `ee7b000af195d0107a2423c7778ac88e9f7bc81d9daf90ac6d2bc59d23b1d36a` |
| `P2/evidence/performance/build-index.json` | `5c758747d8c695f3c18fbbe59f16042fa5af9d518f6672e63cde27531d5fc417` |
| `P2/images/correctness-memory.png` | `c8e34ac13ef38bc41bb476aceb7cd777d2d426fef2b75809a42d817bac6003a6` |
| `P2/evidence/debug/fixes.md` | `4253d550e95f31689a6f557d23c4e01be73bbcb38bf3ed866d79908d801c75d3` |
| `P2/evidence/commands/inline-binary-reconstruction.txt` | `18ed0c37df1afac1790d15c2a2ffecbaad014a6e12df619c27144215b3ee868c` |
| `P2/evidence/performance/binary-resolution.json` | `cf834af9c96017cbc2154fd66c36b4b608e08844ffad1a6eaab446b5a66ab79a` |
| `P2/evidence/correctness/inline-reconstruction.txt` | `b28c90c2e85e3e46858aacacbdf7f3a4faef2554b4fd1c7ac65e74fd3f4181ac` |
| `P2/evidence/performance/inline/metadata.json` | `6934a189bc2eb9d6f4e6496620fc45a551b5cf09d71307414843a575d51fe64a` |
| `.cache/P2/recovered-inline-source/main.c` | `0beb570201a36541ea1a44ea0a64c9588e95954869c089916372e417d4602665` |
| `.cache/P2/recovered-inline-source/sort_p.c` | `a04436a5e3ceb0bf8bb0b22c7cceec55d5b1c21e52a485352830a6f0923f3d44` |
| `.cache/P2/builds/inline-sort-recovered` | `7b6eaca3379fe858b36738ce2a8393cf46852a21f3137a62024ab01cf89f4371` |
