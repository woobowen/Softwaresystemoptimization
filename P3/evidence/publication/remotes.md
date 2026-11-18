# Publication and remote readback

Formal files came from a fresh sparse clone of GitHub `main`, commit `313f3f38e4a448981f05c6ce2523e6ed76912108`, repository https://github.com/woobowen/Softwaresystemoptimization. The fresh checkout matched the local P3 tree byte-for-byte; Git tree modes for all five executables were 100755, ELF architectures and debug sections were checked, and README links existed.

Shuishan repository `git@gitea.shuishan.net.cn:SSO.James.2026Fall.DASE/10245102410.git`, branch `project03`, commit `e48f6f3550cbcd13348fd5bc5e8ff1c349ac683b`. The branch was created from remote master initial commit `414947e374423bad4e6b24a4a175d0e208714c85`; the root README was preserved (SHA-256 `570dc0d9f5cf381aaa5b133fc86ebf3f6ed8b1f21cb97a7b66cb72ff329feca4`). A second clone of `project03` returned that commit; all 18 P3 formal files matched `formal-manifest.tsv` in SHA-256, byte size and mode, all report links existed, and P3/evidence was absent. Remote Git modes for five executables were 100755. No web page visual inspection was performed.

The subsequent GitHub commit containing this record only changes internal evidence and does not change the formal files copied to Shuishan. The final GitHub SHA must be read from the review package entry, because writing a commit's own SHA into its tree would create a circular reference.
