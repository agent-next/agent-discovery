Round-3 只做只读核对：先对上 `babd1a9..9f57b4b` 的实际代码和测试，再逐条判定，最后跑 `make check`。不改任何文件。差异已经对上。接下来按当前源码核对每条判定，并检查 `scan_genome`、`cross_scan` 和 consensus 边界有没有新的错位。Memory flush started.
Memory flush completed.
Memory flush started.
Memory flush completed.
验收标准已经落到具体行号。接下来用探针跑边界例子，并同时跑 `make check`。Memory flush started.
Memory flush completed.
**VERDICT: REQUEST_CHANGES**

`babd1a9..9f57b4b`（HEAD `9f57b4b`）已按当前源码和探针核对。`make check` 通过：ruff 干净，pytest **121 passed**（6.81s，0 failed / 0 skipped）。提示里的 49 与这次收集到的用例数不一致。绿的套件没有覆盖下面仍失败的行为。

| 项 | 状态 | 依据 |
| --- | --- | --- |
| R1#4 | RESOLVED | `pipeline/db/build_subset.sh:153,161,169` 为 `--member-cover 80`（两处）和 `--mutual-cover 80`。脚本里没有 `--member-cover 0.8`。DIAMOND wiki [Clustering](https://github.com/bbuchfink/diamond/wiki/Clustering) 写明 `--member-cover` / `--mutual-cover` 单位是百分数，默认 80%。`tests/test_pipeline_flags.py:153-154` 断言同一字符串。 |
| R1#9 | RESOLVED | 10 条拷贝、列比例 1.0, 1.0, 0.5, 0.6，`_consensus_block` 返回 `(0, 3, 'AAC')`（`src/artharness/arrays.py:281`，第二次低于 80% 的列作排他终点）。`tests/test_arrays_pwm.py::test_consensus_block_second_lapse_excluded` 断言 `(0, 3)`。该夹具实际列比例是 1.0, 1.0, 0.75, 0.75，同样在第二处 lapse 收到 `(0, 3)`。 |
| R2#1 | RESOLVED | `src/artharness/runner/base.py` 只有模块级 `import re`（`:20`）。AST 无函数内 `import re`。模拟 `ClaudeCodeBackend.run` 的 worker 文本 `PROPOSE_FOLLOWUP: count spacers` 得到 `['count spacers']`，无 `UnboundLocalError`。 |
| R2#2 | RESOLVED | editor 解析 `FILE:\s*(yes\|no)`（`base.py:146-149`）。探针：`FILE: yes` → `yes`，`FILE: no` → `no`，`FILE: YES` → `yes`，无该行 → `None`，`FILE: yesterday` → `None`。`file_report` 在 `verdict != "yes"` 时不归档（`orchestrator.py:235-239`）。`verdict is None` 时返回 `None`，不写 `report.md`，审查文件首行是 `FILE: no`。 |
| R2#3 | RESOLVED | `BackendOutput.text`（`base.py:53,168`）。`Roles.curator` 使用 `out.text or self._synthesized_entry(...)`（`roles.py:107`）。探针里 curator 文本 `LIVE ENTRY: ...` 写入知识库，存根句未出现。 |
| R2#4 | RESOLVED（读取路径） | `delimit_array` 写入 `block_offset=blk_s`（`arrays.py:392-396`）。`pwm_extend` / `cross_scan` 用 `p+off` 取保守块（`:446-447`、`:489-490`）。带 offset 4 的扩展找回了间距外的额外拷贝（14 → 15）。两个命名测试在 121 通过的套件里。扩展成功后的新对象把该字段丢回 0，见新问题 1。 |
| R2#5 | NOT-RESOLVED | 文件头写明包含 `<100 nt` 抑制（`scripts/scan_genome.py:13-15`）。`scan_genome` 的 `co_names` 不含 `mod_runs_under` 或 `arrays_min_spacing`；这两个函数（`:38-59`）没有被扫描循环调用（`:85-95`）。同一条序列（规则间距 4 拷贝，紧挨间距 6 拷贝），shuffle 置空后：`kmer_scan` 为 `no_array`，`scan_genome` 仍报 `(start=0, R=4)`。 |
| R2#6 | NOT-RESOLVED | `02_filter.py --dry-run` 仍打印 `discard weak: bitscore < 25.0 OR coverage < 0.35 OR no YxDD motif`（`pipeline/census/02_filter.py:195-196`）。模块 docstring 已改成 jointly/and。`:31` 注释仍是 `bitscore < 25 or coverage < 0.35`。 |
| R2#7 | RESOLVED | `05_sample_neighborhoods.py --dry-run` 打印 `total anchors: 7,308`，输出中没有 `GAP`（`pipeline/census/05_sample_neighborhoods.py:205-207`，`TOTAL_ANCHORS = 7308`）。 |
| R2#8 | RESOLVED | `README.md:19` 为 `52 HMMs`。README 中没有 `98 HMMs`。 |
| R2#9 | RESOLVED | 转录本按行行走。DNA 在评语之前：`repeat_remarks_after_dna=1`。评语在 DNA 之前：`repeat_remarks_after_dna=0`（`experiments/forensics.py:71-85`）。`L0050` 不命中 `XL0050Y`；`MW218148.1` 能命中。`repeat_remarks` 仍是全部评语计数（先出现的评语该字段为 1）。`scan_records` 仍是裸子串，见新问题 4。 |
| R2#10 | RESOLVED | `null_margin = max(base_max3, base_max6)`，再判断 `score < 2 * null_margin`（`arrays.py:383-384`）。`score=12, base_max3=10, base_max6=4` 会复测；只拿 `2 * base_max6` 时这一例不会。高于 2 倍（30 vs 10/4）不复测；未同时超过两个零分布（9 vs 10/4）不复测。 |

新问题：

1. **major** — `src/artharness/arrays.py:470-472`  
   `pwm_extend` 在找到额外拷贝时新建 `DelimitedArray`，不传 `block_offset`，默认回到 0。无额外拷贝时返回原对象，所以 `test_pwm_extend_uses_block_offset` 看不出这件事。探针：输入 offset 4，输出 offset 0，且是新对象。前缀不同、核心相同的两个位点，带着 offset 4 时 `cross_scan` 互相分组；经过 `pwm_extend` 之后两组都是空。

2. **minor** — `src/artharness/arrays.py:454-458`  
   `known = {p+off}`，跳过条件却是 `i-off in known`。拷贝起点 20、offset 4 时，真正的块起点是 24，跳过发生在 28。扫描从 `i = off` 开始，窗口开头 `off` 个碱基不会被看。这次间距 136 的额外拷贝仍被找回。

3. **minor** — `src/artharness/arrays.py:504-506`  
   `cross_scan` 用被扫描位点自己的 `block_offset` 做长度门槛 `len(window) < w+off`。阈值压到 `-1e9` 后，含完整 motif 的 14 nt 窗口在 offset 0 时与长窗口位点分组，offset 4 时两组都空（`14 < 12+4`）。

4. **minor** — `experiments/forensics.py:47`  
   `scan_records` 仍是 `i in text`。`XL0050Y` 被记成标识符 `L0050`。转录本路径已用词边界。

5. **minor** — `experiments/forensics.py:71-77`  
   同一行先检查 DNA 再检查评语。一行 `tandem repeat then <240 nt DNA>` 得到 `repeat_remarks_after_dna=1`。

6. **minor** — `pipeline/db/build_subset.sh:149`  
   命令已是百分数 80，注释仍写 `--member-cover / --mutual-cover (fractions)`。`:150` 的 `--cov-mode` 只出现在“这不是合法参数”的注释里。
