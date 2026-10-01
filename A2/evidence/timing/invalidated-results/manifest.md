# Timing-invalidated results

这些结果均来自真实运行。随后复现的系统 clock anomaly 使性能计时不可信；全部退出正式 results，不用于最终报告的性能结论。原生 raw、HTML、编号和资源未修改。逐文件 SHA256 见 [file-manifest.json](file-manifest.json)。

| Run ID | 原用途 | Original path | New path | Raw SHA256 | 原因 |
|---|---|---|---|---|---|
| SPECjvm2008.006 | 旧完整 Base | `A2/results/base/SPECjvm2008.006` | `A2/evidence/timing/invalidated-results/base/SPECjvm2008.006` | `8c67caaa971974eab807797577bd1c22b9bd1a477aeb02f6be6a0d2cc2849d47` | 系统计时异常 |
| SPECjvm2008.007 | compress 原配置第 1 次 | `A2/results/repeat/SPECjvm2008.007` | `A2/evidence/timing/invalidated-results/repeat/SPECjvm2008.007` | `4a66c063774cc6db571e03d1226f402d0cae3c3cf5030c2ae8d2fe3b410840ec` | 系统计时异常 |
| SPECjvm2008.008 | compress 原配置第 2 次 | `A2/results/repeat/SPECjvm2008.008` | `A2/evidence/timing/invalidated-results/repeat/SPECjvm2008.008` | `1d90d9ce386d0d24c1448680f699ee4312d2d4065bc3e318c9aaa6d789353d34` | 系统计时异常 |
| SPECjvm2008.009 | compress 原配置第 3 次 | `A2/results/repeat/SPECjvm2008.009` | `A2/evidence/timing/invalidated-results/repeat/SPECjvm2008.009` | `4717cfd2e59b19e04b166a47a02d34cc79a092b40ca1c8470646b8ec3783ab27` | 系统计时异常 |
| SPECjvm2008.011 | Serial GC 第 1 次 | `A2/results/parameter/SPECjvm2008.011` | `A2/evidence/timing/invalidated-results/parameter/SPECjvm2008.011` | `4ca01bb1d598a39418c6c9409cadc6876c583669738b284ede24d896a183657d` | 系统计时异常 |
| SPECjvm2008.012 | Serial GC 第 2 次 | `A2/results/parameter/SPECjvm2008.012` | `A2/evidence/timing/invalidated-results/parameter/SPECjvm2008.012` | `e3b69246198fbf2def4aa3890b968ccfb96a42a8afe0e458d956629abb64cef7` | 系统计时异常 |
| SPECjvm2008.013 | Serial GC 第 3 次 | `A2/results/parameter/SPECjvm2008.013` | `A2/evidence/timing/invalidated-results/parameter/SPECjvm2008.013` | `b9b5fc47ea8d2a2f20009282833aaa8ba3e7b70562838c21e4445e72fc483893` | 系统计时异常 |
| SPECjvm2008.014 | 独立 compress timing diagnostic | `A2/evidence/compress-investigation/standalone-diagnostic/native-results/SPECjvm2008.014` | `A2/evidence/timing/invalidated-results/diagnostic/SPECjvm2008.014` | `a0239382835f1363555b1fea706c7241b7dcd3f3f1ade76e7a84745c3cd62027` | 系统计时异常 |

## 已在 evidence 中的兼容性与短测

以下目录本来就在内部 evidence，未移动。它们是兼容性/诊断材料，均不用于正式性能结论；原生 validity 仅保留当时 SPEC 的判断，不能证明计时可靠。其原路径与现路径相同，raw 和所有资源保持原样。

| Run ID | 原用途 | 原路径 = 现路径 | Raw SHA256 |
|---|---|---|---|
| SPECjvm2008.001 | Java 21 preflight | `A2/evidence/compatibility/java21-preflight/native-results/SPECjvm2008.001` | `1e5d8e0c22c8cd8155607f47bb03bc35d5c87a89845d8be59b0ebf40b978b860` |
| SPECjvm2008.002 | JDK 8 preflight failure | `A2/evidence/compatibility/jdk8-preflight/native-results/SPECjvm2008.002` | `0e585ea86ce2056c35940138fe0f16d2a74f10d186a1108d0e8c801c43904fc7` |
| SPECjvm2008.003 | runner JDK 8 smoke | `A2/evidence/runner/spec-smoke-jdk8/native-results/SPECjvm2008.003` | `7718b5106f9257ee300e8a80105535b229d7ca64b6f0aab896d48bada2a12194` |
| SPECjvm2008.004 | JDK 7 preflight / 字体故障 | `A2/evidence/compatibility/jdk7-preflight/native-results/SPECjvm2008.004` | `ad447e3e14a9fc482da35084d840dd6a876e6ffe97d84d8c6a5132cf005b6a02` |
| SPECjvm2008.005 | JDK 7 FreeType 修复短测 | `A2/evidence/compatibility/jdk7-preflight-fixed/native-results/SPECjvm2008.005` | `3d970fa022c89b3252d4af323d40fd0af2f37679da2b5755ca0b989fda14bca3` |
| SPECjvm2008.010 | Serial GC smoke | `A2/evidence/parameter/smoke/native-results/SPECjvm2008.010` | `b62284eaa1e55d535f23e9a37d5ac8ac4f38fe0b3182a339a96f1856b797e289` |

`.004` 的 79 个空 JPEG 来自原始字体失败，保留不补造。发布前另做全部 14 个 native directory 的逐文件 SHA256 核对，并检查 HTML 的本地资源链接；检查结果记录在 `../../final/checkpoint-local-validation.json`。本次没有新的性能测量，也没有修改上述原生文件。
