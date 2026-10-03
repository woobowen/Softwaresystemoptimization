# Goal3 独立源码、文稿与交付审核

审核者为独立 reviewer，与 README/交付文档 owner、报告 owner、图片/运行/发布 owner 分离。本记录是本次完整交付审核；没有把作者自检、旧审核或测试数量当作源码审核。本阶段 reviewer 只读源码、文档、日志和图片，未编译、运行测试、启动矩阵或操作 Git/水杉。

受审源码基点为 `c22d856b8fa2f0b37aff4f436a856cf3a74bb37a`，终稿文件由 [candidate-files.json](candidate-files.json) 的逐文件哈希固定；发布回执绑定其与最终提交。数据/方法完整独立审核见 [data-review.md](data-review.md)，不是本记录重跑历史实验。

## 1. 直接源码阅读

直接读完整 `src/autotuner.py`（853 行）、运行 C（67 行）、原始 C（47 行），以及 `goal2r_analysis.py`、`identity_quality.py` 与 `experiment_v2.py` 的身份、受控执行、恢复、块前后检查、共享确认和 Goal2R 路由。三个 src 的 SHA-256 与基点完全一致，不需要生产行为修复：

| 文件 | SHA-256 |
| --- | --- |
| src/autotuner.py | e3a563264994f4875da955ad87ff4ce1dd0c6c180aad3da750e1ae7d5beb02ec |
| src/matrix_multiplication.c | aad89170e8d0ca80c1dbc8dc1d8d5e69bab354af86128021be163c91e5a72b50 |
| src/matrix_multiplication.original.c | 188d011109c4470e1f41829216e8677a5c2d8f2b7c8a44215652320dbdf6de15 |

- 原初始化、n=4096、double、六层乘加及 s=24 尾块保持；计时先作整数纳秒差再换秒，checksum 和端点输出在计时后。未引入转置、并行、BLAS 或新计算方案。
- 目标、配置空间、搜索策略三个接口明确；主循环是 suggest → evaluate → observe。Grid 枚举、Random 无放回、Greedy 的邻居和严格改善规则均可从直接控制流解释，单次在线观测更快不等于真实性能改善。recheck 的六项探索与两次复测边界清楚，失败复测不能成为返回候选。
- 失败/中断仍占尝试预算，非 benchmark 不评分。构建缓存核对源码、编译器、实际 flags 及二进制；60 与 60.0 等非代码生成设置不进入构建键，完整恢复元数据仍核对。日志未闭合恢复不会免费重跑或擅自终止身份不明进程。
- Goal2R 没有重新启用辅助时钟 2% 全局否决、不同配置先作不确定判定或固定 rho 外扩。正确性、主计时有效性和比较质量分开；共享确认先锁定返回，不能反向反馈搜索。

源码仍含完整恢复与研究功能，规模超过最小算法示例，但职责可解释，没有为本次交付新增通用抽象或大范围拆分。普通运行只需包内源代码、Python 标准库及 Linux/GCC；通用目标需遵守参数/输出约定，不能宣称自动理解任意程序。

## 2. 教师要求与终稿连续阅读

已直接读老师本轮一页 PDF，并从头连续阅读最终 `P1/report.md`，同时读取终稿 README 与运行依赖说明。报告按题目 1—4 顺序回答：三个接口/框架优劣、给定矩阵、五个分块和四级优化、Grid 与另外两种自行实现算法；顶部身份为规定学号/姓名，无额外班级日期字段。

报告的 20 配置表、基础六组比较、四起点、三个新种子及六组候选复核值与本次独立 raw 算术吻合。g_ref 定义、G 的逐轮参考配置分母和百分点单位均解释清楚；min/max 未称置信区间，128/O1/O2/O3 的重叠未写成唯一稳定第一，八次固定 Grid 前缀未冒称完整穷举。搜索总耗时与内核耗时分开，25.708% 指调优成本节省。

正式正文用“候选复核策略”说明负结果，没有内部 Goal/S3/审核状态叙述；保留了必要的时钟有限区间、小矩阵全量与大矩阵抽查边界。第四/六组漏第八项、独立搜索同配置时段差及复测改选均来自保存轨迹，未用离线回放改判，不把全部损失强行归因于少探索。

README 在 P1 目录可独立解释 list/build/run/search 与恢复约定，直接命令不依赖 evidence、Git 历史、QPC 或截图环境。文稿链接的 CSV journal 字段是全工程出处索引，候选目录不因此承诺完整历史复算；两条依赖链的具体说明留在 [delivery-dependencies.md](delivery-dependencies.md)。文献边界仍为项目有限简化，不称论文复现；此次未新增文献清单或算法。

另直接打开两项原来源核对实际借鉴段落：[2021 arXiv v2](https://arxiv.org/pdf/2103.08716v2) §III-C 描述重复测量与带分布假设的停止，并说明最低两次可能不足；[2024 大学仓储出版正文](https://pure.uva.nl/ws/files/182730825/A_methodology_for_comparing_optimization_algorithms_for_auto-tuning.pdf) §3.3、§3.4.3—3.4.4 讨论预算/噪声、时间及成本拆分。它们支持报告的有限动机引用，不提供本项目6+2规则或两样本置信保证。阅读这些段落没有下载论文入Git或扩展策略。

## 3. 六图实际打开与源数据

独立 reviewer 逐张实际打开五张 PNG，并打开当前 `framework.svg` 的新渲染 `P1/.cache/goal3/framework-preview.png`，也直接读 SVG。最终字节/哈希独立计算吻合 [images.json](images.json) 和候选清单。

| 正式图 | 阅读与来源核对 |
| --- | --- |
| framework.svg | 三输入、统一评估与反馈路径清楚，无外部资源依赖；SVG 字节与基点一致。 |
| interfaces-kernel.png | 最终 suggest/evaluate/observe 和实际六层循环，行号对应稳定源码；不是恢复重放截图。 |
| grid_median.png | 20 个已保存中位数、样本 min/max 与表相符，单位秒；快配置细差没有放大成稳定唯一第一。 |
| online_search.png | 三基础算法共同参照位置/搜索成本与保存表一致；读过展示脚本，时间图按完成反馈作 post 阶梯，未插入未来值。 |
| saved-search-results.png | 六组 18 G 与六个成本节省吻合，左为参考耗时分母的百分点，右为搜索成本百分比；标题明确不保留。 |
| build-run.png | 真终端显示 O0—O3 四个 cached=false/编译退出 0，n4096 完整输出、整数端点、target exit=0、calls=1；与最小目录同一次运行复用。 |

三张统计图只改展示层，旧 CSV、评分函数和协议不变。终端图裁去下方无关空白，保留命令、目标结果与退出；截图记录使用私有 Unix socket/授权，禁止 TCP，未把 viewer 退出冒称目标成功。

## 4. 全工程干净复现：直接读执行记录

主控从固定基点干净导出，再覆盖记录的候选文稿/展示文件，原构建缓存不存在；源码未变化。该导出是准确描述的候选导出，不冒称已存在的最终发布提交。下述命令均来自主控实际闭合 [control.jsonl](control.jsonl)，reviewer 未另运行它们。

在 `P1/.cache/goal3/full-clean` 仓库根目录执行：

```bash
python3 -B -m unittest discover -s P1/tests -v
python3 -B P1/src/autotuner.py build \
  --cache-dir P1/.cache/goal3-cold-build \
  --output P1/.cache/goal3-cold-build.jsonl
taskset -c 0 python3 -B P1/src/autotuner.py run --s 128 --opt O3 \
  --mode correctness --repeats 1 --timeout 1200 \
  --cache-dir P1/.cache/goal3-cold-build \
  --output P1/.cache/goal3-fresh-n4096.jsonl
```

直接读取完整回归 stderr，254 条具体测试行全部 `... ok`，结尾 `Ran 254 tests in 12.943s / OK`；0 skip、0 failure。四项原生截图与五项原生 Windows 清理确已执行，失败/超时/信号测试中的预期非零子进程仍保留，不能当作实验成功退出。清理记录五个宿主状态均 absent，四项截图均无清理错误、授权/套接字移除、无遗留监听。

[四级冷构建](full-cold-build.jsonl) 各有实际编译、`cached=false`、退出 0；没有以版本号代替构建。新鲜目标仅一次，n4096/s128/O3、唯一 start/end、退出 0、checksum=17180040496.458935；[整数内核差](full-fresh-n4096.jsonl) 为 45.362831808 秒，进程 RAW 为 46.039513505 秒，correctness 模式不评分。它检查可运行性，checksum 仍不是新增全矩阵数值证明。

使用匹配稳定分析代码从保存 raw 重生成，直接打开两侧文件检查：九个数据文件字节完全一致，`summary.json` 仅缺未请求绘图的 images 元数据，删去这一字段后其余 JSON 相等。既有五批历史重生成链未改变，故没有重新运行那些历史矩阵批次。详见 [regeneration-comparison.json](regeneration-comparison.json)。

## 5. 最小目录隔离与问题修复

`P1/.cache/goal3/minimal` 按候选白名单装配，包含两份 Markdown、三份 src、六图及两个正式 CSV，共 13 文件；不带 .git、evidence、AGENTS、提示词、输入 PDF/ZIP、历史缓存或其他作业。演练后构建/日志/同源小矩阵夹具只在该目录自己生成的 .cache 内，未进入候选清单。

最小目录四级冷构建与完整工程的四个 ELF 逐级 SHA-256 相同。实际完整 n4096 通过普通包内入口与最终终端截图复用，仅一次目标：

```bash
python3 -B src/autotuner.py build --cache-dir .cache/classroom-build \
  --output .cache/cold-build.jsonl
taskset -c 0 python3 -B src/autotuner.py run --s 128 --opt O3 \
  --repeats 1 --timeout 1200 --cache-dir .cache/classroom-build \
  --output .cache/fresh-n4096.jsonl
```

[最小目录 raw](minimal-fresh-n4096.jsonl) 的真实目标退出 0、失败 0、calls=1，整数内核差 **33.338204624** 秒、首行六位小数 33.338205 秒、进程 RAW 33.952249174 秒。它采用 CLI benchmark 模式，但只用于课堂运行展示，未加入原参照 60 样本或新的性能比较。主控消息曾把整数差转述成 33.338205624；原始端点未改，复现 JSON 已以正确整数差记录。

同源 n=129 夹具逐字等于正式 C 仅替换 n 宏。三个算法分别使用 `search --target .cache/small.c --algorithm <grid|random|greedy> --budget 20 --seed 17 --repeats 1 --timeout 30 --cache-dir .cache/small-build --output .cache/control-<算法>.jsonl`。独立 reviewer 直接从三份 raw 另写只读临时计算，核对 48 个真实 start/end、argv、配置、成功退出、首行/整数端点及进程区间，不转调 tuner 的策略实现；重放 Grid 20 项完整顺序、Random seed=17 的20项无放回顺序，以及 Greedy 八项移动与终点全部邻居的无改善。三者分别20/20/8调用，0失败/中断，Greedy停于local_optimum。此项是控制流测试，不是n4096性能成绩。

审核发现最小目录一张统计图仍是改单位前字节；交给图片/装配 owner 同步最终13项，仅展示层修复，无需再跑矩阵。修复后独立计算每项字节数、SHA-256、Git blob 与 manifest，全部正确；当前工作树、minimal 与 full-clean/P1 三处 13 项逐字一致。report 的12个本地引用与README的1个引用均存在且在清单中；候选目录除自己生成的.cache外无额外文件。

只读检查的临时命令曾误把全工程根目录当P1根目录、或按错误层级读取嵌套compile/clock字段而退出；检查命令修正后才作上述判断，没有修改生产数据或把失败检查标通过。这些普通短读没有伪造计时端点。

## 6. 审核结论与外部边界

本次完整数据/方法审核和完整源码/文稿/交付审核均完成，具体展示同步问题已由 owner 修复并复核。未发现待修的生产行为、数值、正文或最小运行依赖问题；两次新增 n4096 的实际目的和结果闭合，总调用由429到431，未重跑20配置/六seed主比较，也未改候选REJECT结论。

截图与测试仅使用既有工具和单进程PATH，没有安装包或修改全局配置。新增受控费用以主控闭合回执为准，不能把内核、进程、测试和外层阶段重复收费；不计量的普通文件阅读/文稿工作不能写成测得时间。

此处审核的是发布前冻结文件及真实执行记录。GitHub commit/push/远端读回及最终 ZIP 绑定由主控随后实际完成；外部仍需从最终发布提交读取报告、源码、六图、必要 raw 和清单，以实际附件及远端内容作最终工程判断。本记录不授予外部 `Engineering PASS`，不把候选演练叫正式教师提交包，水杉未操作。

发布前新增检查只复核改动：检查器曾把外层 recorder 的自身 active start 误判为未完成（保留退出1、RAW 0.218196933秒）；仅忽略缓存内检查器改为允许唯一自身 `publication-preflight-corrected` 活跃标签，修正运行退出0、RAW 0.239348181秒，最终读回12个 start 均有唯一 completion、15个 end 的整数差与费用一致，两次检查均0矩阵且未改生产源码/旧raw。直接核对新ZIP的六成员字节哈希与正式图完全一致：615834字节，SHA-256 `db115f2b89694456539af736ebd339acf3141b725720dc544c0417441c0ab146`；两项实际CLI list分别20项、4项。该具体检查器问题已修复，不需要重复全审或矩阵运行。
