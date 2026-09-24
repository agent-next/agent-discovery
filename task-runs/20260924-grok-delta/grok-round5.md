按你给的两项探针做只读核对：先看 `6df9b55..HEAD` 的差异和对应测试，再跑这两条探针和 `make check`。差异只有取证排序、`scan_genome` 窗口循环和两条探针。接下来对这两段实现和 `kmer_scan` 的窗口语义，并跑测试。代码路径已经对上。接着跑两条探针、一个能证明抑制仍然会触发的对照，以及全量 `make check`。Memory flush started.
**VERDICT: APPROVE**

两项修复都在当前源码里，探针数字与 `kmer_scan` 一致。`make check`：ruff 通过，pytest **127 passed**（9.04s，0 failed / 0 skipped）；`--collect-only` 也是 127。没有新的行为问题。

| 项 | 状态 | 依据 |
| --- | --- | --- |
| 1. 更早一行已有 DNA 时，本行自带 DNA 的评语仍算 after-DNA | RESOLVED | `experiments/forensics.py:74-84`：先取 `prior_dna_lines`（严格更早的行），再把本行写入 `dna_seen_at`。`after` = 已有更早 DNA，或本行 DNA 起点早于评语。探针 `L0050 flank:` + 240 nt，下一行 `tandem repeat suspected then` + 240 nt：`dna_runs=2`，`remarks=1`，`after_dna=1`。对照仍成立：同行评语在 DNA 之前 → `after_dna=0`；同行 DNA 在评语之前 → `1`；评语行在 DNA 行之前 → `0`；只有评语 → `0`。`test_remark_after_dna_on_earlier_line_with_own_dna` 通过。 |
| 2. 抑制和 shuffle 只用窗口内拷贝，命中坐标映回基因组 | RESOLVED | `scripts/scan_genome.py:86-112`：窗口仍是 `run[0]-3000` 到 `run[-1]+WORD+3000`；`win_positions = _copies_of(window, seed, 2)`；仅当窗口内短间距 run 长于窗口内最长规则 run 时跳过；`start/end` 为 `lo + long_run`。用户夹具（5090 nt，精确起点 `0,30,60,90,120,150` 与 `4030,4170,4310,4450`）窗口是 `[1030:5090]`，窗口内拷贝只有 `[3000,3140,3280,3420]`，短间距长度为 0。`scan_genome` 命中 1 条：`start=4030`，`end=4464`，`R=4`，`seed=ACGTACGTTGCAAT`，`shuffle_max=0`。同一序列上 `kmer_scan` 为 `array`，`R=4`，同一 seed，窗口内起点 `[2566,2706,2846,2986]`（对应那 4 个基因组位点）。`test_scan_genome_suppression_is_window_local` 通过。 |

抑制没有被这次修改关掉。短间距 6 拷贝放在规则 run 的窗口内（起点 2000..2150，规则 run 在 Memory flush completed.
4000..4420，间隔大于 450 nt 所以不会并成一条不规则 run）：同一 seed 的 `short_lens=[6]`，`scan_genome` 为 `[]`。同一构造、短拷贝移到 0..150：命中 `R=4`，`start=4000`，`end=4434`，seed 不变。

新问题：无。
