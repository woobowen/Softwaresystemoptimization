# project01 documentation sync

本目录记录已验收文档从固定 GitHub 对象同步到水杉 project01 的结果。工程验收沿用此前外部结论；本次仅进行字节同步、Git 提交和远端对象核对，最终 Submission PASS 等待 ChatGPT。

## Git identities

- GitHub repository: https://github.com/woobowen/Softwaresystemoptimization
- Branch: main
- S2: e7e3d4e2bfbf6b2c30b3b9f4b73a68372c48102a
- Teacher repository: git@gitea.shuishan.net.cn:SSO.James.2026Fall.DASE/10245102410.git
- Teacher branch: project01
- T1: 6b42f26926c5dcd740a9bfea8385be0455d7ce53
- T2: 22974c9707d176f3a1abd8603728286b8ebe2270
- T2 parent: T1
- GitHub evidence parent: S2（执行开始时 local HEAD 与 origin/main 均为 S2）。
- G2: 首次增加本目录的 GitHub commit。自身 commit SHA 无法写入其自身文件而保持同一 SHA；实际值在发布后查询、fresh fetch 核对并随最终回复提供。可用下列命令解析：

```bash
git log -1 --diff-filter=A --format=%H -- P1/evidence/submission/project01-doc-rewrite/README.md
```

## Exact document mapping

| Mapping | bytes | SHA256 | Git blob | mode | match |
|---|---:|---|---|---|---|
| S2:P1/README.md → T2:README.md | 6997 | f5688c43e23a778a618bed1611fb178533c51b050bc5ad42c95c329a3f3e273b | 3c40548ee9d19e13d48b41762e7f7fbe3d140dc0 | 100644 | yes |
| S2:P1/report.md → T2:report.md | 30086 | b49961d639fd34e19079ced6409d9eeb12d485674c25b7ef1d74761c9c39eb68 | f3f30a790733d0bc88a33c717d8006c01582eda2 | 100644 | yes |

T1 → T2 只有 README.md、report.md 修改；其余 11 个正式文件 bytes、SHA256、blob、mode 均不变。教师完整 tree 仍恰为指定 13 文件，详情见 [package-manifest.json](package-manifest.json)。16 处本地 Markdown 链接有效且大小写一致，README/report 互链有效；六张图片沿用 T1 原始对象。

## Teacher remote verification

- local teacher HEAD = queried remote SHA = fresh SSH network fetch SHA = T2。
- Fresh bare repository 从空仓库初始化，无 object alternates、无本地对象复制。
- T2 tree: ea11c0ff6d7e10b291f62e15c82685e7756fa62d。
- master、homework01、homework02、homework03–15 及其他 advertised refs/HEAD 均与提交前相同；仅 project01 从 T1 前进到 T2。
- 两名原生只读子代理均独立读取 fresh Git objects；审核范围和结果见 [review.md](review.md)。

完整 refs 前后记录及 HTTP 访问结果见 [remote-verification.json](remote-verification.json)。Git 命令、实际输出摘要和 exit code 见 [commands.log](commands.log)。

## Web rendering

UNVERIFIED。未认证 HTTPS 访问 project01、README.md、report.md 均收到 302 并转到 /user/login，最终为 Sign In - 水杉码园。未看到文档渲染页面，不据此修改或重复提交任何文件。

## Protection

GitHub 的 P1/README.md、P1/report.md、src、results、images、tests、A1、A2 和旧 submission evidence 均保持执行前对象身份。水杉未增加 evidence、tests、scripts、缓存、编译产物、讲义、备份或其他作业。

没有新 benchmark，没有新 n4096 调用，没有重新生成图片或截图，没有安装包，没有全局配置修改，没有 amend/rebase/force push。

GitHub publication 的实际 G2 SHA、local/remote equality 与 fresh fetch 结果只能在 G2 生成后验证，因此由最终回复及远端 commit/tree 提供；本记录不提前声称未来的 push 或 readback 成功。
