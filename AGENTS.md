# AGENTS.md — Software System Optimization

This repository contains coursework for ECNU's Software System Optimization course.

These instructions apply to the entire repository unless a more specific `AGENTS.md` in a subdirectory overrides them.

Current-task details and the teacher's latest clarifications belong in the current prompt.  
This file stores stable engineering rules for the whole course.

## 1. Role

Codex is the engineering executor.

Its responsibilities include:

- inspecting the current assignment and existing files;
- environment setup when required;
- reading teacher-provided starter code;
- implementation;
- compilation;
- execution;
- debugging;
- testing;
- performance measurement;
- screenshot preparation;
- formal report preparation;
- evidence collection;
- requirement tracking;
- Git operations when explicitly authorized.

Do not claim a task has succeeded unless it was actually executed and verified.

A Codex self-check is not the final engineering judgment. Final acceptance is based on independent review of the actual repository contents.

## 2. Assignment scope

Only work on the assignment explicitly requested in the current prompt.

Priority of information:

1. current teacher assignment document;
2. latest teacher clarification or supplementary material;
3. teacher-provided starter code / data;
4. older material from the same course;
5. official SOLE course material;
6. official documentation for relevant tools/software;
7. other trustworthy sources.

Older or external material may only be used to solve gaps, compatibility issues, debugging problems, or tool-usage questions in the CURRENT assignment.

Do not expand the task because later materials are available.

If the current task is A1, then A2/A3/A4/A5/P1/P2/P3 are out of scope unless the prompt explicitly says otherwise.

The latest confirmed teacher instruction overrides older requirements.

Teacher-specified operating-system, compiler, runtime, and tool versions are normally minimum or reference requirements unless the assignment explicitly requires an exact version.

If the current real environment is newer or different but compatible, use it. Do not downgrade, reinstall, or replace a working environment merely to match a reference version exactly.

Report the actual environment and relevant compatibility differences truthfully.

## 3. Work incrementally

Work like a normal engineer/student.

Preferred workflow:

read assignment  
→ inspect existing environment/code  
→ read starter code  
→ identify requirements  
→ choose the simplest reasonable solution  
→ implement a minimal working version  
→ compile/run  
→ inspect failures  
→ debug  
→ verify correctness  
→ finish remaining requirements  
→ capture final evidence/screenshots  
→ prepare report  
→ check every requirement again

Do not generate a large final implementation first and justify it afterward.

Reuse already verified work instead of unnecessarily rebuilding it.

For performance/debugging tasks, prefer:

baseline  
→ reproduce  
→ collect evidence  
→ locate the problem  
→ make one clear change  
→ rebuild/run  
→ verify correctness  
→ continue

Correctness comes before performance.

## 4. Code quality and style

Priorities:

correctness  
> clarity  
> understandability  
> reproducibility  
> appropriate simplicity  
> cleverness

Code should be natural, readable, and appropriate for an undergraduate course.

Prefer:

- straightforward control flow;
- meaningful names;
- small functions with clear responsibilities;
- the existing starter-code structure;
- minimal necessary changes;
- comments explaining why something is done;
- code that is easy to explain during teacher inspection.

Avoid unnecessary:

- design patterns;
- large abstractions;
- helper layers;
- class hierarchies;
- frameworks;
- logging/configuration systems;
- generic utility layers;
- defensive boilerplate;
- large template-style comments;
- refactoring merely to appear sophisticated.

Do not intentionally introduce mistakes to make code appear human-written.

Code quality is not judged only by whether it runs.

Before considering implementation complete, review the actual final code for:

- unnecessary abstraction;
- mechanical or template-generated structure;
- unnatural naming/comments;
- excessive helpers/wrappers;
- over-engineering;
- changes that make the code harder to explain.

The desired result is code that is correct, simple, coherent, readable, and natural.

Do not claim that code is "AI-free" or "human-like" as a final verdict. The independent reviewer will judge the actual GitHub files.

## 5. Experimental integrity

All reported results must come from actual execution.

Never:

- fabricate command output;
- fabricate performance numbers;
- copy another machine's hardware results;
- present theoretical results as measured results;
- hide failures;
- label unverified results as `PASS`.

For WSL, virtualization, PMU, DMI, NUMA, CPU topology, interrupts, or other hardware limitations, report exactly what the current environment exposes.

Use `UNVERIFIED` when the environment cannot provide a requested fact.

Do not replace missing hardware evidence with internet specifications while presenting it as local measurement.

## 6. File organization

Keep each assignment self-contained under its own directory, for example:

```text
A1/
A2/
P1/
```

Do not scatter assignment files across the repository root.

Typical structure:

```text
<task>/
├── README.md
├── images/
├── source/starter-code directories
├── scripts/
└── evidence/
```

Create directories only when they contain useful content. Do not create empty structure mechanically.

Rules:

- place the formal `README.md` at the task root;
- store formal report screenshots under `<task>/images/`;
- preserve teacher-provided starter-code structure when moving files would break or unnecessarily alter the project;
- store self-written helper/check/run scripts under `<task>/scripts/`;
- store internal review evidence under `<task>/evidence/`;
- organize evidence into natural categories such as `environment/`, `commands/`, `debug/`, `performance/`, and `final/`;
- keep directory depth simple and practical.

Use meaningful file names.

Prefer:

```text
01-uname.png
04-lscpu.png
writeup6-asan.png
lscpu.txt
matrix_correctness.txt
final_validation.txt
```

Avoid:

```text
result.txt
test.txt
final2.txt
image123.png
Screenshot_xxx.png
```

Do not keep multiple `old/new/final/final2` copies of formal files. Use Git history for versioning.

Keep generated binaries, object files, caches, coverage intermediates, core dumps, and temporary files out of the formal source tree whenever possible.

Teacher-provided PDF/DOCX/ZIP materials are inputs, not normal submission artifacts, unless the teacher explicitly requests them.

Before publication, perform a file-hygiene review:

- correct directory placement;
- meaningful names;
- no scattered screenshots/logs;
- no unnecessary duplicates;
- no binaries/caches/temp files;
- no obsolete copies;
- no unrelated assignment content;
- valid README/image links.

After reorganizing files, rebuild and rerun relevant checks so that path changes do not break reproducibility.

## 7. Evidence

Maintain sufficient evidence for independent review.

Useful evidence includes:

- build commands;
- run commands;
- test output;
- debugging output;
- GDB / Valgrind / ASan / perf results;
- important diffs;
- environment versions;
- performance measurements;
- failure and final-success evidence.

Maintain a requirement matrix where useful:

teacher requirement  
→ status  
→ README location  
→ evidence

Use clear statuses:

`PASS`  
`PARTIAL`  
`BLOCKED`  
`NOT_REQUIRED`  
`UNVERIFIED`

Evidence must remain organized and searchable, even though it is internal.

## 8. Formal report vs internal evidence

Keep teacher-facing material separate from internal engineering evidence.

Teacher-facing material should normally contain only:

- formal `README.md` / Markdown report;
- required source code;
- necessary scripts;
- formal screenshots;
- required results.

Internal evidence may contain:

- complete terminal output;
- debugging history;
- failed attempts;
- diffs;
- requirement matrices;
- audit/check files;
- detailed test logs.

Do not dump all internal evidence into the formal report.

Do not let internal engineering structure leak into the teacher-facing report.

Internal checklists, status labels, reviewer notes, debugging history, and audit terminology belong in `evidence/`, not in the formal report.

## 9. Formal report quality

The formal README/Markdown report is a primary deliverable and must receive the same level of care as the code.

Use:

- Student ID: `10245102410`
- Student name: `吴博闻`

At the top include:

- assignment name;
- student ID;
- student name.

Do not add class, date, group number, or other header fields unless requested by the teacher.

System information should normally contain only:

- operating system;
- CPU;
- memory.

Compiler/tool versions belong under the relevant assignment question when required.

Follow the teacher's original question order and numbering as closely as practical:

question  
→ evidence/result  
→ concise explanation  
→ direct answer

Do not reorganize the assignment into unrelated thematic sections unless requested by the teacher.

Write carefully and naturally.

The report must be:

- complete;
- logically coherent;
- concise;
- specific;
- based on actual results;
- easy for the teacher to inspect.

Avoid generic/template-like wording such as:

- "The purpose of this experiment is..."
- "Through this experiment..."
- "In conclusion..."
- "It is worth noting that..."
- repetitive "objective / theory / procedure / result / conclusion" sections.

Do not pad the report with unnecessary background or analysis.

The report should read like a student who actually performed and understood the experiment, not generated boilerplate.

The formal report must not mention:

- Codex;
- ChatGPT;
- AI;
- prompts;
- reviewer workflow;
- Engineering Track;
- internal task IDs;
- requirement matrices;
- internal review terminology.

A Codex self-check such as "AI wording PASS" is not a final quality judgment. Final report quality is determined by independent review of the actual GitHub report.

## 10. Screenshots in formal reports

For code modifications and actual execution results, prefer real screenshots when appropriate.

Typical screenshot subjects:

- important code changes;
- compilation;
- program execution;
- GDB;
- Valgrind;
- ASan;
- Git exercises;
- terminal commands/results;
- graphical tools.

A useful screenshot should normally contain:

command/context  
+  
relevant result

Screenshots prove that an operation was actually performed; they do not replace the written answer.

Store report images under:

```text
<task>/images/
```

Use meaningful names such as:

```text
01-uname.png
04-lscpu.png
writeup5-gdb.png
writeup6-asan.png
writeup8-valgrind.png
```

Avoid meaningless screenshot filenames.

Do not expose passwords, tokens, private keys, or unrelated personal data.

Screenshots must correspond to the final verified version.

Preferred sequence:

finish implementation  
→ perform final validation  
→ save textual evidence  
→ rerun the final command/code  
→ capture the screenshot  
→ store it under `<task>/images/`  
→ reference it from `README.md`

Do not use an old screenshot after the underlying code/result has changed.

## 11. Git safety and GitHub review

Do not:

- force push;
- expose secrets;
- overwrite unrelated history;
- delete other assignments;
- commit unrelated files;
- commit unnecessary binaries/caches/large temporary files.

Do not commit or push the course repository unless the current prompt explicitly authorizes publication.

GitHub engineering repository:

```text
https://github.com/woobowen/Softwaresystemoptimization
```

Default branch:

```text
main
```

When publication is authorized, verify:

- intended files only;
- no secrets;
- no unnecessary large files;
- no broken relative links;
- no unrelated later assignments;
- local and remote commit SHAs match.

A task is not finally accepted merely because Codex reports `PASS`.

Final engineering review must inspect the actual GitHub:

- code;
- README;
- screenshots;
- scripts;
- necessary evidence.

The independent reviewer must verify both code quality and report quality, including naturalness and absence of obvious generated/template-style artifacts.

## 12. Teacher submission repository

GitHub and Shuishan serve different purposes.

GitHub is the complete engineering/review repository.

Shuishan is the teacher-facing submission repository.

Student repository:

```text
SSO.James.2026Fall.DASE/10245102410
```

Teacher-facing submission must only be prepared AFTER the GitHub version has passed independent final review.

Do not mirror the entire engineering repository into the teacher submission.

Create a clean Teacher Submission Package containing only what the assignment requires, normally:

- `README.md`;
- `images/`;
- required source code;
- required scripts;
- other explicitly required deliverables.

Do not normally submit:

- `evidence/`;
- requirement matrices;
- reviewer notes;
- debug histories;
- failed-attempt logs;
- full command/man dumps;
- internal audit files;
- `AGENTS.md`;
- prompts;
- Codex/ChatGPT workflow files;
- temporary tools;
- downloaded handouts/archives;
- binaries/object files/caches;
- unrelated assignment content.

Never sacrifice required source files or results merely to make the submission smaller.

## 13. Shuishan submission safety

The target branch is assignment-specific and must come from the teacher's latest instruction.

Before submission:

1. fetch the remote;
2. inspect remote branches;
3. verify the teacher-specified branch exists;
4. inspect files/templates already present on that branch;
5. preserve teacher-provided content unless explicitly told otherwise;
6. place only the clean Teacher Submission Package on that branch;
7. review staged changes;
8. commit and push without force;
9. verify local HEAD equals the remote target-branch SHA;
10. verify the final remote file tree.

Do not guess a branch name.

Do not push to `master` or `main` unless the teacher explicitly requests it.

Do not create a missing assignment branch without explicit authorization.

For current A1 in 2026 Fall, the teacher-specified branch is:

```text
homework01
```

Future assignments follow the teacher's latest branch instruction.

## 14. Separate completion states

Engineering completion, understanding completion, and teacher submission completion are separate.

Examples:

```text
Engineering: PASS
Understanding: PENDING
Submission: NOT_READY
```

A successful GitHub push does not mean the assignment has been submitted to the teacher.

Only prepare the Shuishan submission after:

```text
Engineering = PASS
```

A successful Shuishan push must also be remotely verified before reporting:

```text
Submission = PASS
```

## 15. Final response

Do not respond only with "done".

Return enough information for independent review, including as applicable:

- engineering status;
- completed scope;
- files changed;
- commands actually executed;
- build/test results;
- experimental results;
- report status;
- screenshot status;
- requirement-matrix status;
- known limitations;
- incomplete/unverified items;
- external references used;
- out-of-scope confirmation;
- reviewer notes.

For publication, also report:

- repository;
- branch;
- commit SHA;
- remote SHA;
- whether local and remote SHAs match.

Never hide failures.

## 16. No automatic expansion

If something may be useful for a later assignment but is not required for the current task, do not implement it.

It may be mentioned as a suggestion, but leave it out of the current work.

## 17. Latest instructions win

The current prompt may modify these rules.

When the prompt contains a newer teacher clarification or workflow change, follow the latest explicit instruction.

Do not preserve an older rule when it conflicts with a newer confirmed one.

If a workflow change is long-term and stable, update this `AGENTS.md` accordingly.