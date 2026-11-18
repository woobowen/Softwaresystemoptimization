# A4 homework04 submission verification

- Reviewed GitHub source: `ca25b45b5b268be3c7a366cba1210932c8dde3db` (`A4/`).
- Teacher repository: https://gitea.shuishan.net.cn/SSO.James.2026Fall.DASE/10245102410
- Branch: `homework04`; initial commit `414947e374423bad4e6b24a4a175d0e208714c85`.
- Submission commit and `git ls-remote` branch SHA: `5f1330b068b23e08610e51e8543d9b98bb9adf84`.
- Commit: https://gitea.shuishan.net.cn/SSO.James.2026Fall.DASE/10245102410/commit/5f1330b068b23e08610e51e8543d9b98bb9adf84

The package contains 52 files: report, six images, eight source/license files, three scripts, 24 raw reports, eight executable-size records and two CSV files. Internal evidence, build logs, binaries and pilot data were excluded. No selected formal file was modified.

An independent SSH clone of the branch was compared with the isolated local submission and the source commit. All 52 paths, SHA-256 hashes, sizes and Git executable modes matched; `manifest.tsv` records the values. The initial root README blob was unchanged. The branch contains the root README and A4 files only. All README local links resolve, all six PNG files decode, and all 24 reports passed the saved report-format checker. The source compiled with GCC in a separate temporary directory; shell and Python syntax checks passed. No benchmark was rerun. Credential-pattern scan found no matches; this is not a guarantee that all possible secrets were detected.

The web URL returned HTTP 200 but the retrieved page did not contain the report text, so authenticated browser rendering and image display were not verified. SSH Git readback supplied the file-content verification. `git diff --check` reported pre-existing trailing whitespace and CSV CRLF in the frozen source; these bytes were preserved. SSH returned locale warnings but clone and push succeeded.
