# 本轮资料使用记录

主依据仅为本轮 DOCX、PDF、ZIP；哈希见 source_hashes.txt。

| 来源 | 用途 | 为什么三份材料不足 | 是否改变任务 |
|---|---|---|---|
| https://www.conventionalcommits.org/en/v1.0.0/#summary | 阅读语义化提交结构、feat/fix、breaking change | DOCX 明确指定阅读此链接 | 否，题目要求 |
| https://www.opencilk.org/doc/users-guide/install/ | 确认 Ubuntu 24.04 / WSL2 支持及官方 OpenCilk 3.0 包 | DOCX 只给 >=1.0，没有安装步骤 | 否 |
| https://www.opencilk.org/doc/users-guide/getting-started/ | 确认 -fopencilk 编译/链接与 runtime 验证方式 | 当前材料未提供 OpenCilk 示例 | 否，仅最低环境验证 |
| https://github.com/OpenCilk/opencilk-project/releases/download/opencilk/v3.0/opencilk-3.0.0-x86_64-linux-gnu-ubuntu-24.04.tar.gz | 尝试下载官方包 | 当前工具链缺失 | 否；传输失败，未安装 |
| 当前已配置的 Ubuntu noble / noble-updates 软件源（mirrors.tuna.tsinghua.edu.cn/ubuntu） | 获取 htop、hwloc、libhwloc15、Clang runtime、llvm-cov | 工具缺失，ASan 链接失败 | 否，使用 Ubuntu 官方发行包 |
| 本机 man（含 Ubuntu 包中的 htop/lstopo 手册） | 核实命令选项、列头、perf 参数、采样口径 | 题面要求查手册，未解释全部字段 | 否 |

没有使用网上学生答案，未查找或执行后续作业。
安装源来自现有 apt 配置；记录 apt 输出与 SHA256，不修改 apt 源。
