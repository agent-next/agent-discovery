Round-4 只做只读核验：先对 `9f57b4b..HEAD` 的 diff 和那 8 项修复逐条对代码，再跑回归探针和全量测试。Diff 已对齐到 `6df9b55`。接下来按当前源码核对这 8 项，并检查修复本身有没有引入新的错位。Memory flush started.
Memory flush completed.
全量 `make check` 已通过（125）。探针在加载 `02_filter` 时失败了，我改加载方式后重跑行为探针。Memory flush started.
Memory flush completed.
**VERDICT: REQUEST_CHANGES**

`9f57b4b..6df9b55` 上这 8 项目标行为都已在当前源码里，探针也对得上。`make check`：ruff 干净，pytest **125 passed**（6.67s，0 failed / 0 skipped）。`pyproject.toml` 的 `addopts = -q` 只让进度变成点；汇总行和按文件收集数都是 125（上一轮的 49 是把进度行当成了用例数）。

绿的套件没有挡住下面两条新的边界。

| 项 | 状态 | 依据 |
| --- | --- | --- |
| R2#5 抑制已接上 | RESOLVED | `scan_genome` 在报 hit 前调用 `_runs_under(positions, MIN_SPACING - 1)`（`scripts/scan_genome.py:85-92`）。同一条 1600 nt：间距 30 的 6 拷贝 + 间距 140 的 4 拷贝，shuffle 置成 poly-A 后 `scan_genome` 为 `[]`，`kmer_scan` 为 `no_array`。只有规则阵列时两边都报 R=4；短 run 长度等于规则 run（4 对 4）时两边都报 R=4（抑制用的是 `>`）。`arrays_min_spacing()` 仍无人调用；脚本本地 `MIN_SPACING` 与 `artharness.arrays.MIN_SPACING` 都是 100。跨窗口的范围问题见新问题 2。 |
| R2#6 plan 文本 | RESOLVED | `plan()` 打印 `discard weak: bitscore < 25.0 AND coverage < 0.35 AND no YxDD motif, jointly (needs --seqs FASTA to test)`（`pipeline/census/02_filter.py:196-197`）。整段 plan 里没有 ` OR `。`:31-32` 注释已是 AND / jointly。 |
| (1) 扩展后保留 offset | RESOLVED | 与新测试同一夹具：额外拷贝起点恰好是 `[100]`，`block_offset` 仍为 4，返回的是新对象。两个位点先互相分组；`pwm_extend` 之后（A 多 1 个拷贝，B 为 0）分组还在，两边 offset 都是 4。 |
| (2) known-set 与 i=0 | RESOLVED | 阈值 1、只有 `G*12` 得 100 分、已知块是不得分的 `C*12`。输出起点 `[-4, 40, 52, 180, 320]`，offset 4。`-4` 只可能来自窗口位置 0（扫描从 i=0 开始）。`52` 对应块起点 56，也就是已知块 44 再跳一个 motif 宽度；跳过发生在块起点，不是块起点再加 offset。 |
| (3) cross_scan 长度门槛 | RESOLVED | 阈值压到 `-1e9`。motif 12 nt：14 nt 窗口在 offset 4 和 offset 0 都与长窗口位点互相分组；11 nt 窗口两组皆空（`src/artharness/arrays.py:506-508`，门槛是 `len(window) < w`）。 |
| (4) scan_records 词边界 | RESOLVED | `experiments/forensics.py:47` 为 `\b...\b`。`XL0050Y`、`L0050Y` 对 `L0050` 为空；独立的 `L0050` 命中 `t0001`。`MW218148.1` 命中；`MW218148.10` 和 `MW218148.12` 不命中。 |
| (5) 同行 DNA/评语顺序 | RESOLVED | 带上标识符后：`tandem repeat … L0050 then <240 nt DNA>` 的 `repeat_remarks_after_dna` 为 0；`<240 nt DNA> then tandem repeat L0050` 为 1。`tests/test_forensics.py:71-80` 的正文里没有 `L0050`，函数在排序逻辑之前就因未点名返回 `[]`，这条回归测试本身锁不住该分支。更早一行已有 DNA 时的漏计见新问题 1。 |
| (6) fractions → percents | RESOLVED | `pipeline/db/build_subset.sh:149` 为 `(percents)`。命令仍是 `--member-cover 80`（两处）和 `--mutual-cover 80`（`:153,161,169`）。 |

新问题：

1. **minor** — `experiments/forensics.py:74-82`  
   当前行一旦含有 DNA，函数先把该行号放进 `dna_seen_at`，于是 `dna_seen_at[-1] != ln_no` 恒为假，更早行上的 DNA 不再参与判断。探针：第一行是 `L0050` 加 240 nt DNA，第二行是 `tandem repeat suspected then` 再加 240 nt DNA。结果 `repeat_remarks=1`、`dna_runs_ge200nt=2`、`repeat_remarks_after_dna=0`。评语出现时，更早一行已经有过 ≥200 nt DNA。对照：DNA 单独一行、评语在下一行且该行没有 DNA 时，该字段为 1。

2. **minor** — `scripts/scan_genome.py:82-95`  
   短间距 run 用的是全基因组 `positions`，窗口在抑制之后才切开。文件头把这条规则写成与 `kmer_scan` 相同、并且按候选窗口执行（`scripts/scan_genome.py:13-15`）；`kmer_scan` 的拷贝只来自末端 3000 nt（`src/artharness/arrays.py:171-183`）。探针（非周期 14-mer `ACGTACGTTGCAAT`，shuffle 置成 poly-A）：6 个间距 30 的拷贝在 0..150，4 个间距 140 的拷贝在 4000、4140、4280、4420，序列长 5000。`scan_genome` 为 `[]`。`kmer_scan` 为 `array`，R=4，seed 就是这个 14-mer，窗口内起点 `[2000, 2140, 2280, 2420]`（对应基因组上那 4 个规则拷贝）。同一 seed 的全基因组 short run 长度 6、regular run 长度 4。
