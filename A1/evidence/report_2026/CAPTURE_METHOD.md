# 当前截图来源与核验

2026-09-16 本轮最终代码稳定后，在 Xvfb 的真实 X11 显示中启动 Zutty 终端，实际执行命令，使用 PIL ImageGrab 捕获终端窗口。没有将编造的终端文字绘制成图片，也没有使用图像生成模型。

截图源文件位于 A1/images/，各张对应的完整 terminal.txt 保存在本目录。screenshot_manifest.json 记录图像及对应文本的 SHA256；final_source_sha256.txt 记录拍摄时最终源码。

- 普通命令截图直接执行；top / htop 实际交互运行后按 q 退出。
- GDB、ASan、IRQ 图显示本轮阶段性记录的 cat/tail 输出，终端首行与正式报告均明确说明。它们分别用于证明初始错误、尚未释放时的内存错误、特定时间窗口中断计数，不能误作最终程序仍报错。
- ASan 最终证据使用系统 libclang-rt-18-dev；旧临时 runtime 记录仅作历史保留。
- vmstat/mpstat 画面重新捕获，mpstat 仅显示前 27 行，保证命令和逐 CPU 区间都可见。完整原命令的连续采样记录仍在 linux_commands_2026/。
- 不同时刻的系统负载、空闲内存和进程列表自然变化。原实验 PTY 与截图终端可见的 PID namespace 不同，均为实际执行输出。
- iostat 宽表在终端自动换行；完整原始文本可查。

21 张 PNG 已检查尺寸、解码、非空白像素和 README 引用；关键画面经人工视觉检查。topo.svg 校验 XML 根节点和内部引用，images/topo.svg 与 assets/topo.svg 字节一致。

## Finalize review

2026-09-16：逐张重读原 21 张截图；新拍 OpenCilk version/source/compile/run，重拍 06b-pidstat-iostat（iostat 明示截取前 125 列）和 07-sar（保留命令及完整单次接口采样）。现有 22 张 PNG + 1 张 SVG。其他截图源代码未改变、数据仍与所回答的采样窗口对应，予以复用。旧 Git demo 的 /tmp 目录已不存在，保留其当时真实执行的文字和截图，不重造实验。

images/topo.svg 为唯一正式拓扑文件；原 assets 重复文件已移出仓库。早期 final_review.py 及截图辅助程序是临时执行工具，未作为本次交付脚本。当前检查见 ../final/A1_2026_FINAL_VALIDATION.md。
