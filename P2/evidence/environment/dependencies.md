# 环境与依赖追踪

- 系统：Ubuntu 24.04.2 LTS / WSL2 6.18.33.2；CPU和缓存记录按实际可见结果，完整 lscpu 在 `../../lscpu.txt`。
- 复用 Clang18.1.3、GNU make、Valgrind3.22.0、cg_annotate、binutils、curl/unzip/pdftotext、Python3标准库。
- 系统 perf 包装器查找内核配套目录失败。已有 `/usr/lib/linux-tools-6.8.0-147/perf`（6.8.12）经软件采样、源码关联、DWARF调用栈和report/annotate实际使用可用。硬件cycles/instructions/branch-misses不支持，未放宽权限、未换内核、未sudo安装；实际测试输出独立保存。
- 截图复用 Xvfb、xvfb-run、xauth、ffmpeg 和已有 P1 缓存中的xterm。仅将已有可执行文件复制到 `.cache/P2/tools/xterm`；其依赖库均已存在。临时显示使用私有认证、关闭TCP，截图后由xvfb-run回收。
- **新增系统包：0；语言级包：0；工具链安装：0；全局配置改动：0。**
- 新增的本地内容仅P2源文件/证据/截图和 `.cache/P2/` 中材料、分析原件与构建。未安装Python2，未为无关verifier扩展任务。
- 老师根目录DOCX保留。官方PDF/ZIP只在 `.cache/P2/materials/`，不进入审核ZIP；下载URL和输入SHA在同目录记录及 `input-sha256.txt`。
