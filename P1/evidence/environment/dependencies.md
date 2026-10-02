# 本次依赖和局部工具记录

未执行 apt install、pip/npm 安装或全局配置变更。

复用：GCC 13.3、Python 3.12、matplotlib、Xvfb、ffmpeg、字体及所有系统库。

唯一新增临时工具：`apt download xterm`，在 `P1/.cache/screenshot-tools/` 用 `dpkg-deb -x` 项目局部提取；版本包 `xterm_390-1ubuntu3_amd64.deb`，SHA256 `3541b6956d6c4be71db7b66ec91985bd5eb128fb130e806f1c879f9d94a97c72`。ldd 显示所需库全部已安装。用途是原生真实终端截图；不改系统默认 terminal 或其他全局配置。下载输出：

```text

WARNING: apt does not have a stable CLI interface. Use with caution in scripts.

Get:1 http://archive.ubuntu.com/ubuntu noble/universe amd64 xterm amd64 390-1ubuntu3 [883 kB]
Fetched 883 kB in 2s (446 kB/s)
```

截图能力诊断：Xvfb 自动选择 UNIX socket 在 WSLg 管理的目录失败；本地独立 TCP 显示可启动，但现有 Zutty/GL 显示黑屏。第三条路径使用非GL xterm，仅读取自己的虚拟窗口，不捕获用户桌面。未改 /tmp/.X11-unix 权限；所有测试显示进程已关闭。
