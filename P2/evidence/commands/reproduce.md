# 实际命令与复现入口

以下路径从仓库根执行。编译、正式计时、Perf、Cachegrind和内存检查均由root串行调度，没有后台代理并行跑实验。构建日志保留实际 flags；`performance/build-index.json` 将每个样本批次关联到构建与二进制SHA。

## 原始对象与工具检查

```bash
make -C P2/recitation isort DEBUG=1
/usr/lib/linux-tools-6.8.0-147/perf record -e cpu-clock:u -F 999 \
  -o .cache/P2/checkoff1-probe.data -- P2/recitation/isort 10000 10
# 采样随后移至.cache/P2/profiles/checkoff1/perf.data，匹配二进制和源码同目录。
/usr/lib/linux-tools-6.8.0-147/perf report --stdio --no-children \
  -i .cache/P2/profiles/checkoff1/perf.data
/usr/lib/linux-tools-6.8.0-147/perf annotate --stdio -l --source --symbol=isort \
  -i .cache/P2/profiles/checkoff1/perf.data
make -C P2/recitation sum
valgrind --tool=cachegrind --cache-sim=yes --branch-sim=yes \
  --cachegrind-out-file=.cache/P2/sum-probe.cg P2/recitation/sum
# 同样移至profiles/sum-original，未覆盖原始输出。
```

硬件事件检查命令为 `perf stat -e cycles:u,instructions:u,branch-misses:u -- P2/recitation/isort 100 1`；输出为not supported。软件task-clock计数及cpu-clock采样可用，详见 `../environment/`。

Checkoff2统一带源码行的五配置批次实际运行：

```bash
python3 P2/scripts/sum_controls.py
```

现有结果默认禁止覆盖。再次完整复现用两个尚不存在的新目录：

```bash
python3 P2/scripts/sum_controls.py \
  --local .cache/P2/sum-reproduction --output .cache/P2/sum-readable-reproduction
```

脚本只替换官方sum.c中的U、N常量，保持其余代码，记录每个编译命令、运行命令、原始计数、模拟配置和SHA。增加路径参数是结果保护的小改进；最终版本已做语法/帮助和完整源码阅读，未为此重跑全部大访问实验。

## 构建与正常计时

```bash
make -B -C P2/homework DEBUG=0
P2/homework/sort -s 42 65537 2
python3 P2/scripts/measure.py P2/evidence/performance/all-versions \
  --versions sort_a sort_i sort_p sort_c sort_m sort_f
```

`all-versions` 已存在，复跑需选择新输出目录。该脚本每组5进程、R5、seed42、CPU2，自动保存并排除预热，轮换版本次序，复算TIME/AVG一致性。规模为4096、65536、1048576。早期同方法先比较a/i，后比较a/i/p；各阶段日志和原样本保留，不替代最终批次。

W1先以 `make -B DEBUG=1` 构建保存为 `.cache/P2/builds/writeup1-debug-sort`，再以 `DEBUG=0` 构建保存为 `writeup1-release-sort`。两者正常时间均运行：

```bash
python3 P2/scripts/measure.py <新输出目录> --binary <对应二进制> \
  --sizes 65536 --versions sort_a
valgrind --tool=cachegrind --cache-sim=yes --branch-sim=yes \
  --cachegrind-out-file=<对应新cg路径> <对应二进制> \
  -b -s 42 -v sort_a -t random 32768 1
```

上述尖括号是对实际两条配对命令的简写；准确输出位置与原始flags见 `writeup1-*-build.txt`、`../profiling/writeup1/`及 `../performance/writeup1-{debug,release}/`。cg原件和匹配源码快照均有索引。

阈值按8、16、32、64依次运行，保存二进制后完整正确性检查，再使用measure.py的同一协议，仅选择sort_c：

```bash
make -B -C P2/homework DEBUG=0 EXTRA_CFLAGS=-DCOARSE_THRESHOLD=8
# 其他候选仅改为16/32/64，各次强制重建。
```

`../performance/thresholds/selection.json` 保存事先规定指标下的选择。最终不带宏覆盖，coarsen.h默认为32。

## 汇编、递归对照和最终 profiling

```bash
clang -O3 -DNDEBUG -g -Wall -std=gnu99 -gdwarf-3 \
  -Rpass=inline -Rpass-missed=inline -S P2/homework/sort_i.c \
  -o .cache/P2/variants/sort_i.s
nm -S --size-sort .cache/P2/builds/final-release-sort
objdump -d -S --disassemble=sort_recursive_i .cache/P2/builds/final-release-sort
```

noinline源从sort_i.c复制，只应用 `../profiling/writeup3/noinline.diff`。构建命令与正常构建相同，仅用该源替换sort_i.c并加 `-I P2/homework`。原源码仍保持inline。noinline版先通过276个单版本qsort用例，正常计时N65536/1048576、R5/5进程，CG仍N32768/R1/random。

每个正式版本CG用以下形式，a/i/p/c/m/f各执行一次：

```bash
valgrind --tool=cachegrind --cache-sim=yes --branch-sim=yes \
  --cachegrind-out-file=.cache/P2/profiles/final/sort_m.cg \
  .cache/P2/builds/final-release-sort -b -s 42 -v sort_m -t random 32768 1
cg_annotate --auto=yes --show-percs=no .cache/P2/profiles/final/sort_m.cg
```

Perf版本a/i/p/m/f各执行一次，以m为例：

```bash
taskset -c 2 /usr/lib/linux-tools-6.8.0-147/perf record -e cpu-clock:u \
  -F 999 --call-graph dwarf,8192 -o .cache/P2/profiles/perf-versions/sort_m.data \
  -- .cache/P2/builds/final-release-sort -b -s 42 -v sort_m -t random 1048576 20
/usr/lib/linux-tools-6.8.0-147/perf report --stdio --no-children --call-graph none \
  -i .cache/P2/profiles/perf-versions/sort_m.data
/usr/lib/linux-tools-6.8.0-147/perf annotate --stdio -l --source --symbol=sort_m \
  -i .cache/P2/profiles/perf-versions/sort_m.data
```

f annotate的symbol为sort_recursive_f，i/p同理。原始data、匹配最终二进制/源码不删，只在本地cache保存；导出和SHA进入审核包。

## 内存与失效检测

```bash
make -B -C P2/homework \
  CFLAGS='-O1 -DNDEBUG -g -Wall -std=gnu99 -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=all' \
  LDFLAGS='-lrt -lm -fsanitize=address,undefined'
ASAN_OPTIONS=detect_leaks=1 P2/homework/sort -s 42 1025 2
clang -O1 -DNDEBUG -g -Wall -std=gnu99 -fno-omit-frame-pointer \
  -fsanitize=address,undefined -fno-sanitize-recover=all -I P2/homework \
  P2/evidence/review/check-extremes.c P2/homework/sort_m.c P2/homework/sort_f.c \
  P2/homework/isort.c P2/homework/util.c -o .cache/P2/diagnostics/check-extremes
ASAN_OPTIONS=detect_leaks=1 .cache/P2/diagnostics/check-extremes
make -B -C P2/homework DEBUG=0
cmp P2/homework/sort .cache/P2/builds/final-release-sort
valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all \
  --errors-for-leak-kinds=all --error-exitcode=99 P2/homework/sort -s 42 1025 1
```

分配计数编译 `../review/count-allocations.c` 与六个sort、isort、util源，`-O3 -DNDEBUG -g -Wall -std=gnu99 -I P2/homework -Wl,--wrap=malloc,--wrap=free -lrt -lm`，输出 `.cache/P2/diagnostics/count-allocations` 后单独运行。计数源完整保留。

失败传播诊断只在cache副本把sort_a正文改为 `if(p<r) for(int i=p;i<=r;i++) A[i]=0;`，同正常flags链接原驱动，选择sort_a/N8/R1，实际返回1，日志 `../correctness/failure-propagation.txt`。最终sort_a从未应用此修改。

## 截图

`screenshots/*.sh` 中每条命令都实际在xterm显示，`scripts/capture_terminal.py` 通过带认证的临时Xvfb与ffmpeg抓取。显示的计时/采样为已保存的真实记录，没有为截图生成新正式时间样本。完整操作和SHA在 `screenshots.jsonl`。

## 外部来源

- 老师DOCX与官方PDF/ZIP的SHA：`../environment/input-sha256.txt`。
- [MIT原题](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/796439e646c02f44348d50b1836ff7f9_MIT6_172F18hw2.pdf)、[官方代码](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/b050ca87021170ea0319bce601ae17d3_MIT6_172F18_hw2.zip)。已读全文及所有源码。
- [GCC inline文档](https://gcc.gnu.org/onlinedocs/gcc/Inline.html)：核对GNU99与GNU89 inline语义区别；实际是否内联以本机Clang remarks和汇编为准。
- Cachegrind实际选项由本机 `valgrind --tool=cachegrind --help` 核对，默认cache-sim为no，故显式开启。未使用他人学生作业。
