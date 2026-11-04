# Perfetto GUI 操作与截图记录

执行角色：`/root/perfetto_browser`。仅在本地处理真实 trace；没有连接学校服务器、启动 benchmark 或修改测量数据。

## 实际工具

- Node.js 22.22.0。
- 实际截图脚本自动选中的已有 npm 缓存为 Playwright `1.61.0-alpha-1781023400000`；Chromium `149.0.7827.22`。另有稳定版缓存，但没有为本次截图替换依赖。
- 官方 `https://ui.perfetto.dev/`，界面版本 `v59.1-79997ada9`。
- 使用独立临时浏览器上下文及 Playwright pipe；没有打开监听调试端口，没有读取日常浏览器 Cookie、登录信息或认证配置。
- 复用 `.cache/a3-perfetto/http/` 中原有官方 UI 资源。缓存按完整 URL 的 SHA-256 命名，响应 body 原样交给浏览器。未命中时访问原 URL；没有替换界面代码或事件内容。准备过程中重新读取过一份 8,259 字节的官方 service worker，与原缓存内容相同。没有安装系统包、语言包或修改工具链配置。

## 已实际生成并逐张查看的正式截图

| 图片 | 真实输入与展示内容 | 操作记录 |
|---|---|---|
| `images/03-cpu-perfetto.png` | 正式 CPU `cpu_naive.trace.json`；Python `naive_softmax` 与 max/sub/exp/sum/div | [perfetto_cpu.json](perfetto_cpu.json) |
| `images/04a-cpu-sql-average.png` | 同一 CPU trace；老师指定 AVG SQL，结果 `0.00024946536` 秒 | 同上 |
| `images/04b-cpu-sql-total.png` | 同一 CPU trace；200 次 exp，总计 49.893072 ms，平均 249.46536 µs，非重叠分母 264.485312 ms，占比 18.864213091858225% | 同上 |
| `images/06-gpu-timeline.png` | 正式 GPU naive；完整五步调用、CUDA launch、五个计算 kernel；选中第 11 次完整调用的 exp kernel，显示 flow 与 1.984 µs 详情 | [perfetto_gpu_naive.json](perfetto_gpu_naive.json) |
| `images/08-triton-timeline.png` | 正式 Triton；teacher wrapper、cuLaunchKernel 和单个 softmax_kernel；选中第 6 次调用，3.903 µs | [perfetto_triton.json](perfetto_triton.json) |
| `images/09-online-timeline.png` | 完整 100×5000 Online trace；按时间排序第 17501 个 kernel 附近的 180 µs 窗口，可读 maximum/sub/exp/mul/add 与连续小 launch/kernel | [perfetto_online.json](perfetto_online.json) |
| `images/11-attention-timeline.png` | L=512 正式 Attention；完整四阶段调用，第二次 mm 的两次 launch；选中第 3 次调用的 splitKreduce kernel，1.471 µs | [perfetto_attention.json](perfetto_attention.json) |

共 **7 张正式 Perfetto UI 截图**，覆盖五类正式 trace。截图使用浏览器原生 screenshot，不是绘制的时间线或表格图片。原 trace 未被裁剪、改写；缩放仅改变 UI 可见区间。操作记录保留原 JSON SHA-256、选中 slice、关联 launch、函数祖先、可见时间范围、SQL 文字和实际界面输出、图片 SHA-256。

以上五个正式 trace 的 GUI `stats` 中 `severity IN ('error','data_loss') AND value>0` 均为空。预检查 trace 的探测图只留在 `.cache/a3-formal-browser/`，没有用作正式图片。

## 可复用入口

源码：[capture_perfetto.py](../../scripts/capture_perfetto.py)。脚本通过真实 UI 暴露的 `app.trace` 查询已有 slice、选择实际事件、展开轨道并设置时间窗口，然后调用浏览器截图；没有改写 DOM 标签、数值或 trace。

实际执行形式（仓库根目录）：

```bash
python3 -B A3/scripts/capture_perfetto.py \
  A3/evidence/cpu/cpu_naive.trace.json A3/images/03-cpu-perfetto.png \
  --log A3/evidence/review/perfetto_cpu.json

python3 -B A3/scripts/capture_perfetto.py \
  A3/evidence/gpu/gpu_naive.trace.json A3/images/06-gpu-timeline.png \
  --gpu --focus '' --context naive_softmax --index 52 \
  --log A3/evidence/review/perfetto_gpu_naive.json

python3 -B A3/scripts/capture_perfetto.py \
  A3/evidence/gpu/gpu_triton.trace.json A3/images/08-triton-timeline.png \
  --gpu --focus softmax_kernel --context softmax --index 5 \
  --log A3/evidence/review/perfetto_triton.json

python3 -B A3/scripts/capture_perfetto.py \
  A3/evidence/online/online.trace.json A3/images/09-online-timeline.png \
  --gpu --focus '' --context online_softmax --index 17500 --window-us 180 \
  --log A3/evidence/review/perfetto_online.json

python3 -B A3/scripts/capture_perfetto.py \
  A3/evidence/attention/attention_l512.trace.json A3/images/11-attention-timeline.png \
  --gpu --focus splitKreduce --context attention --index 2 \
  --log A3/evidence/review/perfetto_attention.json
```

SQL 截图通过同次 CPU UI 会话，依次提交 [perfetto_queries.sql](../../scripts/perfetto_queries.sql) 的第一个查询和最后一个 CTE 查询，分别保存 04a/04b。实际送入 UI 的 SQL 文字与输出完整保存在 `perfetto_cpu.json`；临时拆分文件在 `.cache`，不是另一套 SQL 算法。复现时可用成对的 `--sql FILE --sql-image PNG`，每个查询对应一张图。

发布的 `*.trace.json.gz` 是原 JSON 的无损压缩；先解压，再使用上述入口。截图时读的是原 JSON，记录中的 SHA-256 对应解压后的原始内容。

## 调试与界限

初次探测遇到缓存响应的 JS MIME 类型未按 URL pathname 识别，以及包含图标的菜单文本不能用 exact-match 定位的问题；修正辅助脚本后已真实加载与截图。尝试 pin 同一轨道会在 UI 中重复显示，最后采用正常展开 CPU/GPU 轨道的方式。

正式截图没有 GUI 阻塞，也不需要用户补做浏览器操作。时间线中选中的单个 kernel 时间仅用于展示事件详情，不能替代主代理从完整 200 次 trace 统计的单次完整 Softmax 时间。截图选取后续调用只用于便于阅读，不改变任何正式统计范围。Attention 图中第二次矩阵乘确实包含 GEMM 与 split-K 归约两个 kernel，不能把四阶段实现直接计为四个 kernel。
