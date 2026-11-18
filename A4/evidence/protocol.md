# 正式测试前冻结

- 上游 https://gitlab.com/chriscox/CppPerformanceBenchmarks，提交 f146846aebbd087ec58b23a3cdb3c5fbd26b5e34；选择 loop_fusion：比较独立、覆盖、替换和偏移循环，具有多种类型及循环形式。
- loop_fusion.cpp 未改；benchmark_results.h 只将秒数显示从两位改为六位，见 precision.patch。时钟仍为 C `clock()` 进程 CPU 秒，不包含编译；每行计时区间包含程序自身安排的循环及部分校验。
- GCC/G++ 13.3.0，Clang/Clang++ 18.1.3；均为 /usr/bin 命令，详细链接见 environment.txt。编译 `CXX -std=c++14 -I. -O{0,1,2,3} -o loop_fusion loop_fusion.cpp -lm`，没有 LTO、架构特化或 fast-math；CC 与 CXX 配对。
- 固定命令行 iterations=10、init_value 默认 3.0；前 27 组使用 10，最后 3 组源码固定乘 10，即 100；数组 SIZE=8000000，offset 为 400000。每组 3 次独立进程，无单独预热，无绑核；串行运行，每组先 clean 重编译，记录磁盘字节和二进制哈希。原始结果独立保存；异常退出、错误文字、缺行或非正数则停止。
- 预跑 8 配置每组一次、iterations=3，144 行及 30 组均通过，最快行约 0.000431 秒；提高至 10 以改善短行可读性，O0 成本可控。正式汇总按同名行对齐；每次运行 144 行之和，再取 3 次中位数，保留逐行数据，不能把各行最优拼成一次运行。单行极短及优化消除仍限制解释。
- 不预热：各次均为完整新进程，各配置相同；WSL 调度和主机负载不可完全控制，解释较小差异需参考波动。

## 关口顺序修正
首次 24 次采集前绘图脚本只完成语法检查，没有从保存数据生成图，未满足题目对测试前关口的顺序要求。首次采集保留在 evidence/pre-gate-runs，不作为最终正式数据。已使用该批原始数据生成图表、检查图像及独立重算全部汇总，并确认错误报告被拒绝；在此之后按相同冻结配置重新执行全部 24 次，输出到 results/formal。该修正不改变源码或工作量。
