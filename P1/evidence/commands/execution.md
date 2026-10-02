# 实际执行与日志入口

首 shell 为 ls -la；随后实际读取 pwd/Git root、branch/HEAD/remotes/status/file tree，完整读取本次提示、AGENTS、PDF和C。起始命令输出和输入SHA在 environment/initial_environment.txt、environment/inputs.json。根输入原件保留。

## 目标、测试与预测试

真实 GCC 四级构建、原/新 O3汇编、同源小矩阵全元素、ASan/UBSan和两组n4096抽查的完整命令/输出分别在 environment/kernel_assembly.txt、target_adaptation.diff、target_*_monotonic.jsonl；每行包含真实compiler argv与result。旧版原样记录不混入正式成绩。两类独立测试及反例/修复回归命令在 reviews/code_review.md、reviews/experiment_report_review.md，实验夹具日志在 experiment_mock_tests.log。当前测试总数31+23=54；最后隔离全量执行另记。

预测试 driver 与目标 trial 位于 environment/pretest_* 和 results/pretest*。旧 gettimeofday不一致、我方SIGTERM第五项、安全清理及clock探针记录完整；生成marker失败两文件保留。新预测试九次+噪声三次结束后才冻结正式协议。局部xterm下载而非系统安装记录在 environment/dependencies.md。

## 正式实验

实际执行使用 scripts/experiment.py 的串行 execute，四个完整 plan.json保存生成条件，每个task command是实际argv，driver.jsonl保存task_start/process/end及完整MONOTONICwall；相邻stdout/stderr文件保存CLI原输出。autotuner的measurement行保存被测C的真实stdout/stderr/退出/PID、source/compiler/options/binarySHA、kernel及processwall。

四批按 reference_v1 → selection_v1 → conflict_selection_v1 → holdout_v1 顺序结束，没有离线回放代替在线。results/summary/summary.json列完整protocol/source/plan哈希和成本；重新生成命令按P1/README.md，原始输入不改。正式源码/协议属于measurement checkpoint dea74febda56aa4a2ef8eaa877068d5523bf1842，文稿/图/审核后续提交不同不改变测量代码身份。

四级正式CLI共同准备命令记录在 environment/prepared_builds_formal.jsonl，完整driver在 formal_build_driver.json；compile0.537284秒、driver0.610331秒。正式运行全cache hit，测量cache不复用。正式四批总258进程、0失败、完整driver20609.807102秒，原始UTC/RAW仅诊断，正式成本均MONOTONIC。

## 图与真实截图

真实图生成命令为 README 所示 summarize --reference/--runs/--plots；图可从已存raw重生成。screenshots.json记录实际窗口、执行脚本、退出0、图像SHA与capture日志。保存表截图明确只读取已有成绩；最后隔离新构建/真实运行截图随后补入。图和截图不混称。

## 最后隔离与发布

已实际完成：干净本地clone9ba1427中的完整54/54测试（7.615秒，无skip）、四级冷构建、一CPU0/O3/s128真实n4096（kernel30.583361秒；CLI31.229703秒；rc0/checksum正确）和全部9表/两图重生成逐bytes一致。完整实际argv/stdout/stderr/计时及哈希在 ../reproduction/steps.jsonl、build.jsonl、run.jsonl、comparison.json。新单次数据不加入正式258；source/protocol/raw未变。随后仍需独立两类最终产物审核、安全stage/diff/secret/大文件/links范围检查、GitHub main正常push、实际ls-remote与tree查询。完成后会更新这里的实际证据链接；本文件不把等待项记为成功。

发布格式检查：标准库 csv 默认 CRLF 在普通 git diff --check 中被视为行尾空白；为保留冻结输出，使用一次性 `git -c core.whitespace=cr-at-eol diff --cached --check`，不是改Git配置或改写CSV。optimization_diagnostics.txt 的真实命令输出末尾空行单独保留；其余 staged 文件检查exit0。源代码/报告均无新增行尾空白。

截图集成首次按原生成位置读取 capture.log 时，该日志已由复现审核者移动到其忽略cache；读取失败不涉及目标运行。rg定位到 native-capture.log 后复制成功，未重跑目标或改写数据。
