# 实际使用的外部资料

首要输入仍是教师6页PDF（本地原件，未提交PDF副本）。下列只用于A3统计含义、官方规格和工具操作：

1. NVIDIA Ada GPU Architecture V2.02，Appendix A/Table 2，第30页：https://images.nvidia.com/aem-dam/Solutions/geforce/ada/nvidia-ada-gpu-architecture.pdf#page=30 。已再次核对RTX4090显存带宽1008GB/s；这是官方规格，不是本次测量。另参考128SM与缓存规格解释小输入的可能影响，不以规格冒充硬件计数器测量。
2. PyTorch 2.6 Profiler文档：https://docs.pytorch.org/docs/2.6/profiler.html ，以及官方Profiler recipe：https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe 。用于Self CPU、CPU total、活动/栈和事件聚合含义。实际字段以已安装2.6对象与原始输出为准。
3. Perfetto SQL文档：https://perfetto.dev/docs/analysis/perfetto-sql-getting-started ，CLI参考：https://perfetto.dev/docs/reference/trace-processor-cli 。用于slice/ancestor_slice、单位、查询与真实trace解析；所有正式SQL均已执行。
4. Milakov与Gimelshein，Online normalizer calculation for softmax：https://arxiv.org/abs/1805.02867 。用于在线归一化思想的论文入口；具体实现仍严格对照教师PDF中的Algorithm3图片，不沿用论文性能数值。
5. 官方Perfetto UI：https://ui.perfetto.dev/ ，实际加载正式trace并观察/截图；UI版本和浏览器操作见browser_setup.md。

不使用其他机器性能数值作为本次结果；没有引入A3以外课程或研究功能。
