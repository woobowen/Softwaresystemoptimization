# P1 project01 提交记录

- Engineering：外部 `PASS`，绑定源提交 S；依据见 [engineering-acceptance.md](engineering-acceptance.md)。
- 正式包：`READY`；13 文件，770631 字节；源与教师远端逐字一致。
- Submission：`SUBMITTED`；教师 Git 网络读回及独立内部核对已通过，最终 Submission 验收待外部完成。
- 网页：`UNVERIFIED`；教师分支及报告 URL 重定向登录页，未声称平台图片渲染通过。

| 提交身份 | 值及用途 |
| --- | --- |
| S | `5d49e31556aa7f759cd64a1de1ac1739d33cf165`；[已验收 GitHub 源](https://github.com/woobowen/Softwaresystemoptimization/tree/5d49e31556aa7f759cd64a1de1ac1739d33cf165/P1) |
| T | `6b42f26926c5dcd740a9bfea8385be0455d7ce53`；[水杉 project01](https://gitea.shuishan.net.cn/SSO.James.2026Fall.DASE/10245102410/src/branch/project01)，本地、远端查询和新的 SSH 网络抓取一致 |
| G | 承载本目录的 GitHub 新增证据提交；[本目录提交历史](https://github.com/woobowen/Softwaresystemoptimization/commits/main/P1/evidence/submission/project01)可定位。确切 G 及推送后远端 SHA 在最终交接回复与忽略缓存回执中保存，不把自身 SHA 再写回制造新提交。 |

教师远端原无 `project01`。依据老师 P1 PDF 的 `project01（需自建）`，从实际默认 `master` 的干净教师初始提交 `414947e374423bad4e6b24a4a175d0e208714c85` 创建，保留教师历史。原基线只有 51 字节的 `README.md`；用户明确授权仅在新 `project01` 替换它，原 blob 为 `790c8b9c3961b74f6fa9b036558712aab58f2104`，原 SHA256 为 `570dc0d9f5cf381aaa5b133fc86ebf3f6ed8b1f21cb97a7b66cb72ff329feca4`。父历史保留原文件，无其他预置文件；未新增旧 README 副本。

## 正式文件映射

从 S 的 `P1/` 去掉最外层前缀，直接放在教师分支根目录。完整 SHA256、Git blob 和实际远端结果见 [package-manifest.json](package-manifest.json)。

| 固定源路径 | 教师路径 | 字节 |
| --- | --- | ---: |
| `P1/README.md` | `README.md` | 2722 |
| `P1/report.md` | `report.md` | 12730 |
| `P1/src/autotuner.py` | `src/autotuner.py` | 46520 |
| `P1/src/matrix_multiplication.c` | `src/matrix_multiplication.c` | 2209 |
| `P1/src/matrix_multiplication.original.c` | `src/matrix_multiplication.original.c` | 1357 |
| `P1/images/framework.svg` | `images/framework.svg` | 3416 |
| `P1/images/grid_median.png` | `images/grid_median.png` | 157782 |
| `P1/images/online_search.png` | `images/online_search.png` | 220073 |
| `P1/images/saved-search-results.png` | `images/saved-search-results.png` | 106543 |
| `P1/images/interfaces-kernel.png` | `images/interfaces-kernel.png` | 154698 |
| `P1/images/build-run.png` | `images/build-run.png` | 54725 |
| `P1/results/goal2r_summary/grid_summary.csv` | `results/goal2r_summary/grid_summary.csv` | 2616 |
| `P1/results/goal2r_summary/search_summary.csv` | `results/goal2r_summary/search_summary.csv` | 5240 |

两份文档的 13 个本地引用全部闭合。五 PNG 已完整解码，SVG 无外部资源；这些图及代码、报告、CSV 均保持 S 原字节。CSV 的 journal 字段是完整工程的来源索引，不是提交包运行依赖。

## 操作与审核

主控 `/root` 唯一负责写入与 commit/push；`/root/package_check` 独立计算包身份、检查引用和图像，仅运行 `list` / `--help`（均退出 0，20 配置）；`/root/independent_review` 直接审实际暂存、README 授权及新抓取的教师远端对象。详见 [review.md](review.md)、[commands.log](commands.log) 和 [remote-verification.json](remote-verification.json)。

教师完整远端树恰为 13 文件，只新增 `project01`；`master` 和所有 homework 分支 SHA 未变。教师提交消息为 `Submit P1 matrix multiplication autotuner`，commit/push 均退出 0。

保护对比覆盖 A1、A2、P1/src、results、tests、report.md、README.md、images、AGENTS.md，以及开始时的 3431 个已跟踪文件与用户输入，均无变化。GitHub 本次仅新增本目录六份内部记录。

新矩阵调用、编译、基准和 n4096 调用均为 0；没有安装依赖、修改全局配置、force push 或向错误教师分支提交。教师载荷未混入 evidence、脚本测试整套工程、提示词、PDF/ZIP、缓存、凭据、其他作业或 GitHub 历史。

README 同名冲突通过用户精确授权关闭；内部 diff 展示与校验器格式问题仅修正内部回执与校验方式，没有改变正式文件。SSH 服务端输出过非致命 locale 警告，对应 Git 网络命令均退出 0；保留原日志，未修改 locale 配置。剩余限制只有教师平台网页渲染不可检查，以及最终外部 Submission 验收待完成。
