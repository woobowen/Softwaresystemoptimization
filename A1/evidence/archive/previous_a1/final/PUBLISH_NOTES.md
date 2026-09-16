# A1 publication notes

This publication follows the completed A1-FULL-001 assignment. Historical scope/check logs describe that earlier task, when no commit or push was performed. A1-PUBLISH-001 separately authorizes publishing A1; it does not add MIT Git exercises or later coursework.

The course report, C/Python source and Makefiles are unchanged during publication. Only reproduction references were adjusted so they no longer require unpublished local archives or installation logs.

## Included evidence

The repository retains the requirement matrix, original Linux command outputs, installed manual pages (about 280 KiB total), baseline failures, repair diffs, GDB/ASan/Valgrind results, readable coverage reports and final checks. These support interpretation of the actual tool versions and results. `top_plain.txt` is retained because the report links it; other redundant plain terminal transcripts are excluded.

The original `submission_validation.txt`, `SELF_CHECK.md` and requirement matrix document A1-FULL-001. Publication checks are recorded separately in `publish_validation.txt`; the repository manifest is `PUBLISHED_FILES.txt`.

## Local-only files

Teacher PDF handouts, MIT PDF/ZIP and extracted handout text, environment-install history, full package inventories, apt logs, compiler outputs, coverage binary intermediates and duplicate working files are excluded without deleting them. The approximately 185 MiB temporary extracted LLVM/runtime directory under `/tmp` is outside this repository and remains untouched.

Official materials can be obtained from the links in [EXTERNAL_REFERENCES.md](EXTERNAL_REFERENCES.md). The PDF path in the historical scope checklist describes the original local download; that archive is intentionally not published.

## Reproduction provenance

MIT starter ZIP SHA-256:

```text
035076cda3971e7ff0faa4c9fed1003170a62b510bdf81aab44b06661a7c0d02
```

Both temporary Ubuntu packages were version `1:18.1.3-1ubuntu1`, architecture amd64, obtained from the configured official Ubuntu mirror. The original download log remains local; SHA-256 values copied from it are:

```text
libclang-rt-18-dev: 82d5d27d12c0abdf4cefbafa6044e7544a4cbbbec9c04784f5ce326979842b2b
llvm-18: 139cb82e16e75fcdd4a56562804ff9bfb482b65d0929580d621d28088075a27e
```

See [reproduction instructions](../mit6172/REPRODUCTION.md) for temporary extraction and intermediate-stage patches. No package installation, environment change or experiment logic change was needed for publication.
