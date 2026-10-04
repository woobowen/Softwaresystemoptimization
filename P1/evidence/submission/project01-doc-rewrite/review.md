# Independent review

本次实际使用主控与两个原生子代理（共 3 个角色）。只有主控导出文件、写入 index、commit/push、创建 bare repositories 和执行网络 fetch；两名子代理仅使用只读 Git 命令和 Python 内存分析，输出由主控记录。

## package_check — /root/package_check

输入：固定 S2、T1，教师 staged index，以及从 SSH 网络新 fetch 的 teacher-readback.git。

实际检查：

- 首条 shell 命令 ls -la；读取适用 AGENTS.md。
- 从 S2 Git objects 完整读取两份文档，计算 bytes/SHA256/blob/mode，检查 parent diff 仅修改 P1/README.md、P1/report.md。
- 从教师 index 逐项读取 13 个 stage-0 entries，检查 staged diff 恰为两项 M，无其他 unstaged/untracked 教师文件。
- 从 fresh bare objects 重新读取 T2 commit、parent、tree 与全部 13 个 blobs；两份文档匹配 S2，其余 11 文件匹配 fresh T1。
- 独立解析 inline/image/reference/HTML links；16 次本地链接全部位于教师包，大小写精确，六张图片存在并保持身份。reference/HTML/fragment 链接计数均为 0；2 个外部论文 URL 未下载。

结果：源身份、教师 staged package 与 fresh remote package 检查均通过。未评网页或 GitHub evidence。

实际只读命令包括 git status、show、diff-tree、rev-parse、rev-list、ls-files --stage -z、ls-tree、cat-file blob，以及 Python hashlib 和 Markdown 链接解析。网络 fetch 由主控执行；该代理自行读取新抓取对象，不以主控 manifest 代替检查。

## independent_review — /root/independent_review

输入：实际 teacher index、fresh teacher bare objects、真实 ls-remote refs 前后快照，以及 GitHub 的实际 staged evidence。

已完成的教师提交前审核：

- HEAD=T1，index 恰 13 文件，staged diff 仅 M README.md / M report.md，unstaged/untracked 空。
- 两份文档的 index 与 worktree bytes、SHA256、Git blob、mode 均等于 S2。
- 其他 11 文件逐项 bytes/blob/mode 等于 T1。

已完成的教师网络读回审核：

- fresh refs/heads/project01 = local teacher HEAD = queried remote SHA = 22974c9707d176f3a1abd8603728286b8ebe2270。
- T2 唯一 parent=T1；tree=ea11c0ff6d7e10b291f62e15c82685e7756fa62d；diff-tree 恰两项 M。
- fresh bare=true，无 objects/info/alternates，FETCH_HEAD 来自教师 SSH 网络；全 13 blobs 自行读取并计算身份。
- refs 前后只有 project01: T1 → T2；其余 17 个 advertised refs（包含 HEAD）不变。

上述审核通过。实际只读命令包括 git rev-parse、show、diff-tree、ls-tree、ls-files、cat-file、status，及 Python hashlib/refs 字典比较。

已完成的 GitHub evidence staged 审核：

- 完整 staged diff 只有本目录 5 个纯新增文件；全部 3418 个既有 tracked entries 的 mode/blob 保持 S2 身份，unstaged diff 为空。
- 完整读取 patch 并重建新增字节，与 index blobs 一致；正式文档、P1 src/results/images/tests、A1/A2 和旧 submission evidence 均未变。
- 独立复算 manifest 全部 13 文件的 T1/T2 身份及 S2 文档映射；refs 前后快照、16 条本地链接和 792262 bytes 包总量均一致。
- commands.log 的 109 条真实记录全部 exit 0；60 条 cat-file/ls-tree 输出或摘要通过实际对象复核，未发现越界 mutation。
- 5 文件的凭据、私钥、Authorization、cookie、token 模式扫描无发现；网页状态和 G2 定位方法没有提前声称未执行的结果。

该 staged 审核通过。代理指出首段不应把两人的 Python 调用都写成 python3 -B；主控按实际调用修正为 Python 内存分析。G2 发布后的 fresh fetch 审核将在实际 commit 生成后进行，不在此预写结果。代理不会自行授予最终 Engineering 或 Submission PASS。

## Evidence whitespace check

主控补充运行 git diff --cached --check 时第一次 exit 2：新 evidence README.md 末尾多一个空行。根因是证据文件生成时额外写入一个 LF；仅删除此新文件末尾多余 LF，重新 stage 后同一检查 exit 0。未改动 P1/README.md、P1/report.md 或任何教师文件。原始失败和修复后命令输出保留在 ignored task cache；commands.log 的 109 条记录是此前已完成的教师网络读回阶段快照。

独立 reviewer 的检查器另有一次 exit 1：以全文件断言禁止 python3 -B，误匹配了末尾对该历史措辞修正的正确说明。定位后将断言限定为首段并通过；这是检查条件过宽，没有引起仓库文件修复，也不影响对象身份结论。

## Acceptance boundary

Engineering PASS 沿用已完成的外部验收；两份文档的内容验收沿用 S2。最终 external Submission PASS 等待 ChatGPT 对 T2/G2 完整复核。
