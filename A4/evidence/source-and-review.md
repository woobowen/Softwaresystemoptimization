# 来源、改动和自审记录

- 课程材料 A4.pdf 全文经 `pdftotext -layout` 阅读；PDF 哈希见 material-sha256.txt。原题的教师提交要求为 homework04，本任务明确不执行水杉提交。
- 上游官方 GitLab HEAD f146846aebbd087ec58b23a3cdb3c5fbd26b5e34，初始浅克隆于本机临时目录；只复制测试、依赖及许可证，不含嵌套 Git。`loop_fusion.cpp` 与原始文件逐字节一致。完整上游 makefile 保存于 upstream-makefile.txt，改动后的文件在 source/Makefile；固定 `-O3` 被可配置等级取代，构建和报告仅保留一个测试。
- benchmark_results.h 秒数输出精度变更见 precision.patch；计时器仍为标准 C `clock()`。30 组共 144 个同名子测试，最后 3 组迭代数在源代码中乘 10。正确性失败输出 `failed`，可能不改变退出码，脚本对输出另作检查。部分超短结果可能被编译器化简，不以单行推断具体优化机制。
- 首次编写检查器将行数误设为 124；对真实预跑计数核对后修正为 144，然后进行了八组合预跑。正式关口前遗漏绘图实测，发现后保留首次全矩阵为 pre-gate-runs，生成并检查图表和独立重算后重采全矩阵，详见 protocol.md。
- 截图使用 Xvfb 和真实 zutty 终端：第一次显示尚未就绪，第二次默认字体缺失；等待显示就绪并使用已安装的 DejaVuSansMono 后成功，所拍为实际命令与最终保存数据，不重新排版伪造终端。
- 原生多 agent 曾安排材料及环境独立复核，但两位代理均明确报告无法使用本地文件/终端工具；因此不存在非作者审核通过的结论。主执行者自审，另用独立代码从原始结果复算，见 validation.txt。
- 已知限制：WSL 和主机负载影响稳定性，未绑核；部分子测试较短，编译器可能化简循环；硬件 Perf 不支持，不能计算 IPC。请重点复核原题覆盖、子测试汇总含义、报告及图表与最终提交的一致性。
- 初始工作树：main，HEAD 与 origin/main 均为 cb710711ba4dcb8fc1cd4e7b2c867917ec4261a5；P2/evidence/final/manifest.sha256 已有修改，另有若干 P1 提示词和 matrix_multiplication.c 未跟踪。本次仅定向处理 A4。start-status.txt 是建立 A4 后的再次记录。
- 绘图脚本第一次语法检查发生在首次采集开始后，完整生成和独立复算在第二次采集前完成；不将首次采集称为通过该关口后的正式数据。
- 发布前 `git diff --cached --check` 报告上游原样源码的行尾空白、benchmark/perf 原始输出的行尾空格及报告 Markdown 的双空格换行；保留原始源码与日志字节，不为了消除提示改写证据。代码与 Markdown 的实质内容、相对链接及文件范围另行检查。
