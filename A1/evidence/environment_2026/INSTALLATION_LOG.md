# 本轮安装与配置记录

User confirmed system installation completed.
Final system packages and dependencies:

htop	NOT_INSTALLED -> 3.3.0-4build1
hwloc	NOT_INSTALLED -> 2.10.0-1build1
icu-devtools	NOT_INSTALLED -> 74.2-1ubuntu3.1
lib32gcc-s1	NOT_INSTALLED -> 14.2.0-4ubuntu2~24.04.1
lib32stdc++6	NOT_INSTALLED -> 14.2.0-4ubuntu2~24.04.1
libc6-i386	NOT_INSTALLED -> 2.39-0ubuntu8.9
libclang-rt-18-dev:amd64	NOT_INSTALLED -> 1:18.1.3-1ubuntu1
libhwloc-plugins:amd64	NOT_INSTALLED -> 2.10.0-1build1
libhwloc15:amd64	NOT_INSTALLED -> 2.10.0-1build1
libicu-dev:amd64	NOT_INSTALLED -> 74.2-1ubuntu3.1
libncurses-dev:amd64	NOT_INSTALLED -> 6.4+20240113-1ubuntu2.2
libpfm4:amd64	NOT_INSTALLED -> 4.13.0+git32-g0d4ed0e-1ubuntu0.1
libxml2-dev:amd64	NOT_INSTALLED -> 2.9.14+dfsg-1.3ubuntu3.8
libxnvctrl0:amd64	NOT_INSTALLED -> 510.47.03-0ubuntu4.24.04.1
libz3-4:amd64	NOT_INSTALLED -> 4.8.12-3.1build1
libz3-dev:amd64	NOT_INSTALLED -> 4.8.12-3.1build1
llvm-18	NOT_INSTALLED -> 1:18.1.3-1ubuntu1
llvm-18-dev	NOT_INSTALLED -> 1:18.1.3-1ubuntu1
llvm-18-runtime	NOT_INSTALLED -> 1:18.1.3-1ubuntu1
llvm-18-tools	NOT_INSTALLED -> 1:18.1.3-1ubuntu1


No pip/npm/cargo packages installed.
No shell RC, global Git identity, apt sources, default Clang or WSL kernel changes.
Local reversible fallback: A1/.tools/ubuntu; Ubuntu packages htop, hwloc, libhwloc15, libclang-rt-18-dev, llvm-18 extracted while waiting for sudo authentication. No dpkg installation for this fallback.
The system LLVM/Clang runtime installed by the user is used for final ASan and coverage.
OpenCilk: NOT INSTALLED; incomplete downloads only in /tmp.
Local copies and downloaded .deb files retained; removable after review.
System package removals should consider other projects; do not remove automatically.

## Finalize / GitHub publish 阶段

OpenCilk 3.0 官方 Ubuntu 24.04 tarball，安装到 /home/addaswsw/.local/opt/opencilk-3.0。归档 gzip 检查通过；官方 release digest 为 null，没有独立官方 checksum。本地 SHA256 见 opencilk_download.txt。

未安装新的 apt/pip/npm/cargo 包。系统 /usr/bin/clang 保持 18.1.3，没有修改 alternatives、PATH 持久配置或 shell rc。使用完整路径调用 OpenCilk。

本轮将 A1/.tools、重复 assets/topo.svg、本地旧笔记/材料和过期截图辅助脚本移至 /tmp/a1-local-retained，未发布；先前的原始证据保留或归档。工具链与 1.4 GB 下载包均在课程仓库外。
