# P1 提交内部审核

本文件收录真实原生子代理的直接检查记录。主控 `/root` 负责唯一写入、两处 Git 提交及实际网络抓取；`/root/package_check` 负责只读包检查与轻量 CLI；`/root/independent_review` 独立检查实际暂存和网络读回。没有并行修改同一文件，没有新编译或矩阵实验。最终 Submission PASS 由外部验收决定。


## 包代理检查

# P1 提交包代理检查

代理：`/root/package_check`；仅固定 Git 源读取与临时包轻量检查，未修改正式载荷。

状态：READY；时间：2026-10-04T12:12:48.417119+08:00 至 2026-10-04T12:12:48.670860+08:00（Asia/Shanghai）。
源：`5d49e31556aa7f759cd64a1de1ac1739d33cf165:P1/`；13 文件合计 770631 字节，所有大小、SHA256、Git blob 身份与导出包字节相同。
六图 Git 成员合计697237字节；615834字节是已提供外部ZIP身份，不当作解压成员总大小。

已连续阅读全文 report.md/README.md 与三源码；题号1—4、学号姓名、GCC13.3.0及原结论保留。
13 个本地 Markdown/图片链接全部位于包根内，路径大小写准确；两张CSV journal索引仅用于完整工程来源追溯，不是运行依赖。
五PNG通过Pillow verify及完整像素decode；SVG XML解析通过，仅本地#arrow资源引用，无外部依赖或主动内容。
Python import全标准库；默认C源码同目录，普通构建/运行不依赖.git、证据、截图工具或QPC桥。
私钥/账户token/带凭据URL/Authorization/Cookie/绝对本地路径扫描无发现；精确白名单无额外文件。

轻量执行：`python3 -B src/autotuner.py list`退出0，精确20配置；`python3 -B src/autotuner.py --help`退出0。输出与命令时间见package-check.json。
检查后13文件字节仍等于源，无新增缓存/pyc/日志文件；未编译，n4096新调用0，未安装依赖或改全局配置。

发现/修复：无需修复；未发现阻塞。

未授予最终 Submission PASS；READY 是提交包内部检查状态。


## 独立固定源及教师基线预检

# Independent submission preflight

Reviewer: /root/independent_review

Reviewed at (UTC): 2026-10-04T04:10:35.873195+00:00

Source S: `5d49e31556aa7f759cd64a1de1ac1739d33cf165`

## Directly read

- First executed command: `ls -la` in the engineering root; root contains AGENTS.md, P1 handout PDF, submission prompt, A1/A2/P1, and Git metadata.
- Actual root AGENTS.md and the complete submission attachment were read; rg found no more-specific AGENTS.md outside the ignored cache.
- Teacher PDF was extracted with pdftotext and read in full: report.md, sources, OS/CPU/compiler, visible images; `project01（需自建）` is explicit.
- Source README.md and report.md were read continuously from exact Git objects at S. Student identity, GCC 13.3.0, original conclusions and question order remain present.
- Source candidate-files.txt/json were read. They are supporting records, not authority over actual Git bytes.

## Source integrity and package rules

Exact 13-file whitelist: 13 files, 770631 bytes. Thirteen local Markdown links resolve within this whitelist; the two external paper links do not form teacher-package dependencies. SVG is parsed XML with no external referenced resource. Actual identities are recorded in review-preflight.json.

Candidate manifest discrepancies against actual S objects: 0. None.

Confirmed split: teacher root receives only 13 formal files; no evidence/AGENTS/prompts/test suite/QPC/handouts/cache. GitHub alone receives submission evidence. Teacher history must be used for project01; never GitHub main, homework01 or homework02. Main may create the missing branch after inspecting its teacher baseline.

## Result and limits

Source preflight: PASS. Formal package READY remains dependent on direct package and staged review. Teacher remote and G publication have not yet been reviewed. No source writes, dependency installations, compilation, matrix calls, Git mutations or push were performed by this reviewer. Final Submission PASS belongs to the external checker.

Commands used: ls; rg --files; cat AGENTS/prompt; pdftotext PDF -; git show; git cat-file blob; git rev-parse; Python stdlib hashing/link/XML reads. All completed commands exited 0. Light-operation exact duration is not recorded.

## Direct package and teacher baseline review

Independently read the actual exported package: all 13 bytes, sizes, SHA256 values and Git blob identities match S. Exactly 13 regular files exist; no extras or symlinks. All five PNGs were verified and decoded with existing Pillow; SVG parsed and has no images/scripts/foreignObject or external resources. Python AST imports are entirely standard library. Source was parsed, not executed. No personal absolute paths or credential patterns were found in textual formal files. Local references continue to resolve. Formal package: READY.

Directly read teacher-write remote, refs, Initial commit metadata, entire baseline tree and its complete README, plus prefetch network-query snapshots. Actual default master at 414947e374423bad4e6b24a4a175d0e208714c85 contains only README.md (51 bytes, blob 790c8b9c3961b74f6fa9b036558712aab58f2104); no other coursework or conflicting baseline artifacts. Appropriate teacher baseline confirmed. project01 does not yet exist. Same-name README replacement is the sole identified path authorization blocker; no stage/commit approval granted before the pending user answer. Source/package READY remains independent from teacher write approval.

Note: proposed-readme.diff fused a no-newline original final line with the first added line; this affects review evidence formatting only, not any source/package bytes. A standard git diff will display the no-newline marker correctly when staged.

Finding diff-presentation is CLOSED: directly re-read corrected actual git diff --no-index, including the missing-final-newline marker. No formal byte alteration was needed. The sole outstanding dependency remains explicit README replacement authorization. Start-protection snapshot lists all nine required protected Git paths plus original tracked files and user inputs; final review will compare actual resulting bytes to this snapshot.


## 最终13文件实际暂存审核

# Independent teacher precommit review

Reviewer: /root/independent_review

Reviewed at UTC: 2026-10-04T06:05:17.221595+00:00

Precommit review: **PASS**. Exact 13-file package is READY. Main may normally commit this stage and push only `HEAD:refs/heads/project01`, after the required fresh remote concurrency check. This is internal approval, not final Submission PASS.

## Teacher repository, history and authorization

Actual origin is the correct `SSO.James.2026Fall.DASE/10245102410` SSH repository. Actual branch is project01. HEAD remains teacher root Initial commit `414947e374423bad4e6b24a4a175d0e208714c85`; no GitHub history is used. Teacher PDF explicitly authorizes `project01（需自建）`; the actual default master tree is a suitable clean baseline.

Directly read exact user authorization and final root README diff in full. Only new-project01 README.md may replace the 51-byte initial template with exact `S:P1/README.md`. The old content remains in parent history, blob `790c8b9c3961b74f6fa9b036558712aab58f2104`, SHA256 `570dc0d9f5cf381aaa5b133fc86ebf3f6ed8b1f21cb97a7b66cb72ff329feca4`. No non-whitelist initial files exist. No orphan/history rewrite/deletion is needed; master/homework branches are excluded from submission.

## Exact final stage and references

Actual stage is README M plus twelve A, exactly the whitelist: 13 regular stage-0 files, mode 100644, total 770631 bytes. There are no unstaged changes or extra payload files. Every actual index and working byte, SHA256, size and Git blob matches the source Git object at `5d49e31556aa7f759cd64a1de1ac1739d33cf165`. Detailed checks and all thirteen Markdown references are in review-staged.json.

Earlier direct review read the entire twelve-addition diff, including 853 Python lines, complete report/SVG/C/CSV contents and five actual binary blobs. These twelve identities remain unchanged; the final README diff has now been read completely. Both reports have thirteen case-exact local references inside the package. Prior actual PNG decode/XML checks remain valid for the unchanged six blobs. Existing CSV/original-C CRLF and missing-final-newline details are preserved. Journal fields are engineering provenance, not missing teacher-package dependencies.

Actual full-index binary staged diff SHA256: `7f9eed67675fa92e89bcb741c16152d2ee2bc5f7a760ca9284cea38c3886d69b`. Main cached diff is the same diff after text capture normalizes 100 CRLF display lines. This affects diff presentation only; actual index/source/working bytes were independently compared.

## Identity and issue closure

Direct author and committer checks match the user existing configuration woobowen. Planned message is `Submit P1 matrix multiplication autotuner`. No internal reviewer/AI wording enters teacher content.

README conflict is CLOSED by the precise user answer, recorded before replacement. Proposal missing-newline display is CLOSED using actual git diff. One reviewer verifier exited 1 when incorrectly comparing ordinary diff bytes against the main full-index binary diff; diagnosis found different flags and text-capture normalization. Matching flags/display handling plus all thirteen direct byte checks exited 0. No formal content repair was needed.

No remaining precommit blocker. Teacher commit/push and actual network readback remain pending; only after them can submission become SUBMITTED. Final Submission PASS belongs to the external checker.

Read-only commands: ls; git status/diff/var/branch/rev-parse/rev-list/remote/ls-files/show; source cat-file; Python stdlib hashing and local-link inspection. One reviewer format-assumption failure (exit 1) is recorded above; corrected diagnosis and final check exited 0. No Git mutations, installation, C compilation or matrix invocation. Exact lightweight operation durations were not saved.


## 教师网络读回独立审核

# Independent teacher remote review

Reviewer: /root/independent_review

Reviewed at UTC: 2026-10-04T06:12:06.915019+00:00

Status: **SUBMITTED**; internal remote content review passed. Final Submission PASS is reserved for external acceptance.

S: `5d49e31556aa7f759cd64a1de1ac1739d33cf165`

T: `6b42f26926c5dcd740a9bfea8385be0455d7ce53`

Teacher parent: `414947e374423bad4e6b24a4a175d0e208714c85`

## Direct remote-object review

Directly inspected fresh bare teacher-readback.git, FETCH_HEAD, its actual branch ref, T metadata, full tree and parent tree, all thirteen remote blobs, and the original parent README. Actual logged init --bare and SSH fetch --depth=2 were read; neither local clone nor object alternates are used. Writer HEAD, fresh fetched project01 and the reviewer own network ls-remote all equal T.

All thirteen formal files match actual S:P1/path bytes, SHA256, size, Git blob and mode 100644. Total 770631 bytes. Complete remote tree has exactly thirteen files, no extra evidence/cache/credentials/handouts/other coursework. T versus teacher parent changes only README M plus twelve A. The original 51-byte README and its blob/SHA256 remain in the parent history; replacement is covered by exact user authorization. No other preset file exists to preserve. Detailed independent identities are in review-remote.json.

The two remotely fetched Markdown documents have thirteen local references, all case-exact, included and inside the teacher package. Previous actual image decode checks apply to the unchanged source-identical blobs; no images, code or benchmarks were regenerated.

## Independent network query and scope

Reviewer directly performed `git ls-remote --symref <exact teacher SSH URL> HEAD refs/heads/*` with strict host checking and existing authentication; exit 0. Comparing all returned refs against the initial actual remote snapshot shows only the new project01=T ref. Default master and every homework branch remain unchanged. Network fetch produced only harmless locale warnings and exited 0; no global config was changed.

## Web visibility and limits

Directly read actual HTTPS records for project01 and report.md: both returned a login page via redirect, so authenticated teacher-platform Markdown and image rendering are UNVERIFIED. Git readback/content identities and webpage rendering are separate. No screenshot or rendered-image observation is claimed. External checker may inspect the logged-in teacher page.

No new remote-content findings or remaining Git blocker. README authorization and diff-verifier issues were already closed in precommit review. No final Submission PASS is assigned. Reviewer used read-only Git objects plus one harmless SSH remote query; no fetch/commit/push, installation, C build or matrix calls. All commands in this remote-review phase exited 0. GitHub evidence review is the next pending phase.


## GitHub 证据审核

# Independent GitHub evidence prepublication review

Reviewer: /root/independent_review

Reviewed at UTC: 2026-10-04T06:23:53.135403+00:00

Prepublication evidence review: **PASS**. Main may normally commit/push only the six reviewed evidence additions to origin main, after adding this conclusion and checking the planned small review-metadata increment. Actual G publication and fresh network readback remain pending.

## Actual index and content reviewed

Directly read all six actual index files in full: README, external engineering acceptance, 13-file manifest, remote verification JSON, complete 1034-line commands log, and independent review records. Checked exact staged name-status and full diff; all six are new regular evidence files, and every added diff body exactly reconstructs its index bytes. No other file is staged.

S `5d49e31556aa7f759cd64a1de1ac1739d33cf165`, teacher T `6b42f26926c5dcd740a9bfea8385be0455d7ce53`, teacher Initial parent, precise root-README authorization, thirteen source/teacher identities, all formal references, real SSH fetch and preserved remote refs are consistent with independently reviewed actual objects. Web login limits and absence of rendered-platform-image claims are accurate. G is intentionally resolved by the containing commit/final handoff, avoiding a self-SHA loop.

Commands preserve actual export/fetch/commit/push/readback exits and SHAs. Missing-project01 probe exit 128 and changed-template diff exit 1 are visible, as is the prior reviewer verifier exit 1 and corrected exit 0; no failure was removed. Locale warnings remain nonfatal. No credential URL, token, private key, authentication cookie/header or full SSH config appears. Needed known repository/path/author provenance remains; unrelated baseline author identity was removed. Actual root plus two native subagent roles match their directly read artifacts.

## Protected source and user work

Actual origin is `https://github.com/woobowen/Softwaresystemoptimization.git`, branch main; HEAD and fetched origin/main remain S. Author/committer match existing woobowen configuration. Compared the entire index: all original 3412 source entries are unchanged, only six evidence additions. Nine protected Git scopes match S: A1, A2, P1/src, results, tests, report.md, README.md, images, AGENTS.md. Independently hashed all 3431 start files/inputs including modes; none changed. Original six untracked inputs remain untracked and unchanged. Existing separate teacher checkout remains clean on original homework01 SHA. No user work was overwritten or stashed.

## Closed diagnostic and next actions

This GitHub reviewer verifier initially exited 1 because an unanchored substring split counted a historical `diff --git` string inside commands.log as a seventh file. Actual staged path count was always six. The minimal checker correction recognizes only real line-start headers, reconstructs all six additions and verifies their index bytes; recheck exited 0. No formal or shared evidence content was changed by this reviewer.

No publication blocker. Main will copy this conclusion to review.md, add corresponding review fields/closed diagnostic to remote-verification.json, and replace the evidence README fixed issue count with unnumbered wording. Then only this small increment needs review; no frozen source/image re-audit or experiments. After normal main commit/push, independently network-read G and compare six evidence objects plus protected formal identities; keep final G receipt in ignored cache.

Submission remains SUBMITTED pending external final acceptance; teacher platform rendering remains UNVERIFIED. No install, compilation, benchmark, global config mutation, force push or wrong-branch submission. This reviewer used read-only Git/JSON/hash checks and its own ignored cache files. One local checker diagnostic exit 1 was corrected as described; all remaining commands and final checks exited 0.


本段记录已完成的六文件实际暂存预审。最终仅补录这份结论、校验器诊断及 README 无次数措辞；该小增量与 G 推送后的网络确认单独记入忽略缓存最终回执，不为记录本记录自身的后续确认而循环制造提交。
