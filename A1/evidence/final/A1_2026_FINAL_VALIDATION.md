# A1 2026 Final Validation

Engineering self-review: PASS_WITH_NONBLOCKING_ENV_LIMITATION.

本记录覆盖本地最终验证及发布前检查；独立 reviewer 仍须审查 GitHub 实际文件，不能以本记录代替最终验收。GitHub 提交号与远端验证在发布后的 RESULT 中给出。水杉未提交。

## 来源与范围

主任务：A1 初试环境和工具.docx 全部题目。MIT 正式仅 Getting Started PDF 的 W2–8，代码来自老师 ZIP。三份输入的 [SHA256](../environment_2026/source_hashes.txt) 保留，原文提取件和 handout 不进入发布文件。

[Requirement matrix](../A1_REQUIREMENT_MATRIX.md)：57 PASS，0 PARTIAL，0 BLOCKED，0 NOT_REQUIRED，0 UNVERIFIED。计数描述 requirement completion；DMI、CPU 频率、Windows 物理拓扑等具体事实仍 UNVERIFIED due WSL，已在题目答案中明确说明。

## OpenCilk

官方 OpenCilk 3.0 Ubuntu 24.04 x86_64 tarball，安装到 `/home/addaswsw/.local/opt/opencilk-3.0`。编译器显示 clang 19.1.7，来源为 OpenCilk/opencilk-project；分发版本 3.0 来自官方 release 资产，不能把 LLVM 19.1.7 当作 OpenCilk 版本。

HTTP/1.1 curl 下载成功；以前的 /tmp 片段已不存在，本轮无法续传旧片段。归档实际 1,406,208,994 bytes，与官方 API 记录一致；gzip -t exit 0。本地 SHA256 为 `38e16208a0d086f72858c2024474a0a69c519830d3d3268a80e1ef50d6116838`。官方资产未提供 checksum，digest=null；独立官方 checksum 比对不可用，不伪称已比对。

`-O2` 首次编译成功但提示小循环并行化收益不足，改用 `-O0 -fopencilk` 做最终 smoke test。编译 exit 0，运行 exit 0，输出 `sum = 85344`；ldd 确认 libopencilk.so.1 和 personality 库来自独立安装目录。未修改系统 Clang、alternatives、shell rc 或持久 PATH。

[下载](../environment_2026/opencilk_download.txt)、[发布资产](../environment_2026/opencilk_release_asset.json)、[版本/编译/运行](../environment_2026/opencilk_validation.txt)、[源码](../environment_2026/opencilk_smoke.c)。

## 最终构建与测试

- C primer clean build exit 0，verifier exit 0 / LGTM；pointer 保留 starter 的 unused-variable warnings。
- Matrix clean build exit 0，release `-O3 -DNDEBUG`；normal、-p、-pz 均 exit 0。
- check_matrix.py 独立重算普通矩阵并检查 zero matrix，6/6 PASS，不以舍入为零的计时证明性能。
- Valgrind 普通和 zero：exit 0、ERROR SUMMARY: 0、in use at exit: 0 bytes。
- W6 系统 Clang 18 ASan 阶段性错误记录仍完整，runtime 文件由系统 libclang-rt-18-dev 提供。没有重新插入最终 release 构建。
- Git 第 (18) 项的隔离仓库实验记录存在；旧 /tmp demo 已消失，未重新制造提交。
- 最后执行 make clean，工作树不保留程序 binary、object 和 .buildmode。

[命令索引](test_commands.json)、[verifier](verifier.txt)、[matrix build](matrix_build.txt)、[6 次核对](matrix_correctness.txt)、[Valgrind normal](valgrind_normal.txt)、[Valgrind zero](valgrind_zero.txt)、[系统版本](environment_versions.txt)、[工具可用性](environment_commands.txt)。

## 代码逐文件审查

pointer.c、sizes.c、swap.c、verifier.py、matrix Makefile、matrix_multiply.c、testbed.c 和 check_matrix.py 均逐文件读取。本轮没有更改这些已验证源码：

- pointer 保留题目说明，仅注释六条非法赋值。
- sizes 使用一个简单宏，没有新增层级；数组和结构体指针通过 & 取得。
- swap 为三行指针交换，main 传地址。
- verifier 仅 Python 3 兼容，原检查表及规则保留。
- Makefile 保留 starter 的构建模式和正常 clean，无 coverage 编译选项；已有 coverage 文件清理项无需为风格改动。
- matrix 保留断言、结构体和三重循环，calloc 对应初始化缺陷。
- testbed 保持 4×4，结束前 free A/B/C。
- check_matrix 共两种输入各三次，直接解析和重算，不引入框架。

未发现需要新增抽象或重写的理由。辅助 check_environment.sh 删除了已失效的本地 .tools fallback，改为通过完整路径查 OpenCilk，并清理一条旧任务编号注释。

## 报告逐段审查

重新读取 DOCX 和整个 README，保留题目 (1)–(18) 及各子问题、MIT W2–8。实际修改：

- 移除报告中的完整日志导航、终端控制码/meta.json 说明、重复输出及逐题内部 evidence 链接。
- 删除“没有照搬 PDF frame”“不能强行改成相同结果”“不能仅以看起来正常”等面向验收的表述。
- 简化反复声明实验真实性的句子；保留关键数据、原理及 guest/host 边界。
- 删除 ASan 与 Valgrind 泄漏数量差异的未验证原因推测。
- 增加 OpenCilk 安装版本与 smoke 结果；身份为 10245102410 / 吴博闻。
- 系统表只包含 OS、CPU、Memory；未添加班级/日期等字段。

这是具体内容的自审记录，不宣称报告“AI-free”，也不替代独立 reviewer 对语言、代码及报告质量的判断。

## 截图与链接

全部 21 张原 PNG 已逐张查看；重拍 sar（命令此前滚屏丢失）、pidstat/iostat（宽表换行），新增 OpenCilk 版本/源码/编译/运行。当前 22 PNG + 1 SVG，全在 A1/images/。

iostat 截图的命令明确截取前 125 列；sar 明确显示单次接口采样。完整原命令的文本仍保留。GDB、ASan 和 IRQ 图显示的是本轮已保存的阶段记录，未冒充最终程序仍报错。源码与旧截图源哈希一致，其他截图继续复用。

topo.svg 是原始生成的 SVG，仅保留 images 下的一份，XML 根节点与内部引用检查。PNG 均可解码；屏幕内容未发现密码、token 或私钥。具体链接、文件和模式检查见 [publication_checks.json](publication_checks.json)。

## 文件组织与范围

旧 tracked linux_commands、mit6172 和 final evidence 归档到 archive/previous_a1，保留 baseline/debug/ASan/Valgrind。当前证据按 environment_2026、linux_commands_2026、git_exercise_2026、mit6172_2026、report_2026、final 分类，入口为 [evidence/README.md](../README.md)。

A1/.tools、重复 assets/topo.svg、本地笔记/旧材料和过期临时截图脚本移至 /tmp/a1-local-retained。根 handout 和原文提取件保持本地忽略；未删除老师原始输入。安装器和 OpenCilk binary 均在仓库外。

A2–A5、P1–P3、MIT Section 6、W9、W10 均 NOT_STARTED；MIT Git、AWSRUN NOT_EXECUTED。水杉 NOT_SUBMITTED，未接触 homework01。

## 发布前检查结果

publication_checks.json 的 45 项检查通过：正式报告/矩阵/导航链接有效、22 PNG 可解码并被引用、SVG 根与内部引用有效、源码哈希匹配、Valgrind 与矩阵检查通过、57 项 requirement 均完成、候选文件无 ELF/object/cache/handout/后续作业、无 >10 MiB 文件。

敏感词扫描匹配到 CPU 的 pat 标志、sysctl cookie 参数、软件包名、sudo 缺密码提示、手册和检查说明。已逐类核对，无 GitHub token、私钥或实际凭据；tcp_fastopen_key 的原始记录为 permission denied，没有泄露键值。扫描只记录位置，不输出或复制敏感值。

本地 main 与 fetch 后的 origin/main 在发布前一致（ahead=0、behind=0）。仅在最终 staged 内容复核后创建普通提交并推送，不改写历史。
