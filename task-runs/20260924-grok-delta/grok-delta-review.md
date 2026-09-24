Round-2 delta check: I will read the current tree on `devin/build-modules` and judge each of the 15 findings from the code, then look at the new PWM, cross-scan, forensics, and scan-window paths for the same defect classes.Quota and filter look updated on the surface. Next I will read the array, orchestrator, and test paths that the other findings actually turn on.Memory flush started.
Memory flush completed.
Memory flush started.
Memory flush completed.
The first execution imported `/tmp/artharness-fresh`, which still slices the upstream prefix. I am re-running the checks against this worktree’s `src`.Memory flush started.
`devin/build-modules` 上 `25937a6..babd1a9` 的当前文件已逐项对过（`PYTHONPATH=src`，避免误导入 `/tmp/artharness-fresh` 里仍使用前缀窗口的旧副本）。`pipeline`、`arrays`、`orchestrator`、PWM、forensics、`scan_genome` 这几组测试退出码为 0。这组测试没有覆盖第二次低于 80% 的列，也没有执行 `ClaudeCodeBackend.run`。

| # | 状态 | 依据 |
| --- | --- | --- |
| 1 | RESOLVED | `NOVEL_CLADES = 16`（`pipeline/census/05_sample_neighborhoods.py:50`）。配额相加为 7,308，与 `TOTAL_ANCHORS` 相同。 |
| 2 | RESOLVED | `is_weak_hit` 要求 bitscore、coverage、`has_yxdd is False` 三者同时成立（`pipeline/census/02_filter.py:145-152`）。`tests/test_pipeline_logic.py:93-110` 把单独一条条件锁成非 weak。 |
| 3 | RESOLVED | coverage = `(hmm_to - hmm_from + 1) / qlen`，列下标 15/16，即 HMMER 1-based 第 16/17 列（`pipeline/census/02_filter.py:126-136`）。夹具 t2 的 model 坐标 1..100、qlen 200，期望 0.5；envelope 1..200 会得到 1.0（`tests/test_pipeline_logic.py:70-83`）。 |
| 4 | NOT-RESOLVED | 标志名已换成 `--member-cover 0.8` / `--mutual-cover 0.8`，`build_subset.sh` 里没有 `--cov-mode`（`:153`、`:161`、`:169`）。DIAMOND 聚类文档写的是百分数：`--member-cover` 默认 80%，示例是 `--member-cover 90`（[Clustering](httpsMemory flush completed.
://github.com/bbuchfink/diamond/wiki/Clustering)，2026-09-24 读取）。`0.8` 是 0.8% 覆盖，不是论文的 80%。`tests/test_pipeline_flags.py:153-154` 把这个数值锁进了断言。本机没有 `diamond` 可执行文件，单位以官方 wiki 为准。 |
| 5 | RESOLVED | 候选链按 `(len(c), score)` 取最大（`src/artharness/arrays.py:352-353`）：先最长，同分再比分。 |
| 6 | RESOLVED | 每个 block-shuffle 内部重新数 10-nt、再找拷贝、再成链、再打分（`src/artharness/arrays.py:359-373`）。 |
| 7 | RESOLVED | 扫描、定界、精确词、PWM、cross-scan 都取序列末端：`arrays.py:171-172`、`:334-336`、`:511`、`:437`、`:479`。探针：前缀 8 拷贝 + 末端 5 拷贝，`kmer_scan` 返回 R=5，第一处拷贝落在末端阵列起点。 |
| 8 | RESOLVED | 只有 `verdict == "accept"` 才接受（`src/artharness/orchestrator.py:187`）。`ClaudeCodeBackend` 用 `VERDICT:\s*(accept\|revise)` 解析 supervisor 输出（`src/artharness/runner/base.py:133-141`）。 |
| 9 | NOT-RESOLVED | 第二次低于 80% 的列关闭区块时，端点仍是 `i + 1`（`src/artharness/arrays.py:278`）。探针列比例 1.0、1.0、0.5、0.6，返回 `(0, 4, "AAAC")`，第 4 列（60%）被算进 repeat。允许的那一次 lapse 是第 3 列；排他终点应是 3。 |
| 10 | RESOLVED | `exact_word_scan`（`src/artharness/arrays.py:506-525`）用末端 3,000 nt、精确 12-nt、`_regular_runs`、不做 shuffle。同一探针对末端阵列给出 R=5、seed `CATGTGTATCGC`。`tests/` 没有调用这个函数。 |
| 11 | RESOLVED | `PLACEHOLDER-CLASS-SPECIFIC` 在 `pipeline/census/02_filter.py:38` 和 `pipeline/census/04_classify.py:35`。各类长度仍是 225，tier-1 floor 仍是 100，并标成占位。 |
| 12 | RESOLVED | `tests/test_pipeline_flags.py:153-154` 通过 `_assert_flags` 要求脚本正文含 `--member-cover 0.8` 和 `--mutual-cover 0.8`。数值问题见第 4 项。 |
| 13 | RESOLVED | curator 写入的是 `cout.result`（`src/artharness/orchestrator.py:215-216`），`SessionLedger.record` 原样落 JSONL（`src/artharness/accounting.py:45-47`）。 |
| 14 | RESOLVED | `docs/paper-notes.md:65` 与 `REPRODUCTION.md:23` 都是 52 条 HMM。系统发育里的 “98 ART+NART”（`docs/paper-notes.md:146`）是序列数，与搜索面板不是同一个数。 |
| 15 | RESOLVED | 单向超过阈值时两边集合都加入（`src/artharness/arrays.py:500-502`）。 |

新问题：

1. **major** — `src/artharness/runner/base.py:137-143`  
   `import re` 写在 `role == "supervisor"` 分支里，`re.findall` 在 worker 分支求值。函数体内的 `import` 使 `re` 成为整个函数的局部变量。worker 会话在解析 `PROPOSE_FOLLOWUP` 时触发 `UnboundLocalError`。用同一控制流执行得到该异常。

2. **major** — `src/artharness/runner/base.py:132-144`，`src/artharness/orchestrator.py:235`  
   editor 的系统提示要求 `FILE: yes` 或 `FILE: no`（`src/artharness/roles.py:53`）。实时 backend 不解析 `FILE:`，`verdict` 保持 `None`。`file_report` 只在 `verdict == "no"` 时拒绝，因此实时编辑的否决会把报告归档。

3. **major** — `src/artharness/roles.py:119-128`  
   知识库条目只在 `verdict_notes` 非空时采用模型正文。`ClaudeCodeBackend` 只给 supervisor 填 `verdict_notes`。curator 的 `result` 文本被丢掉，条目退回固定的 “See task record…” 句子。

4. **major** — `src/artharness/arrays.py:323-327`、`:387-389`、`:439-440`、`:480-481`  
   共识块的起点 `s` 在 `_chain_score` 里被丢掉，`DelimitedArray` 只保存共识字符串。`pwm_extend` 和 `cross_scan` 从 `copy_starts` 起取 `len(repeat)` 个碱基。`s > 0` 时 PWM 对的是 seed 前缀，不是那一段保守列。`tests/test_arrays_pwm.py` 直接传入与真实起点等长的 repeat，不经过这条路径。

5. **minor** — `scripts/scan_genome.py:58-66`  
   零分布窗口是 `seq[run[0]-3000 : run[-1]+WORD+3000]`，shuffle 仍用原 seed。文件头写明这是没有 RT 坐标时的全基因组类比，并写 “exactly as kmer_scan”。`kmer_scan` 里更长的 `<100 nt` 间距会抑制呼叫（`src/artharness/arrays.py:181-183`），这里没有对应步骤。

6. **minor** — `pipeline/census/02_filter.py:195-196`  
   `passes_filters` 已是 AND。`--dry-run` 的 `plan()` 仍打印 “bitscore < 25 OR coverage < 0.35 OR no YxDD”。同文件第 31 行注释也是 “or”。

7. **minor** — `pipeline/census/05_sample_neighborhoods.py:166-168`  
   `NOVEL_CLADES` 只出现在 `plan()` 的算术里。`sample_per_clade` 对 TSV 中的每个 novel clade 都抽 60 条。clade 数不是 16 时，锚点数会离开 7,308。`plan()` 第 206 行在和数已经等于 7,308 时仍打印 `GAP:`。

8. **minor** — `README.md:19`  
   首页仍写 “98 HMMs → 198,290 clusters”。账本和 `REPRODUCTION.md` 已改为 52。

9. **minor** — `experiments/forensics.py:53-74`  
   `scan_transcripts` 的文档写明要判断 repeat 评语是否出现在 ≥200 nt DNA 检索之后。实现只分别计数 `dna_runs_ge200nt` 和 `repeat_remarks`，没有事件顺序。标识符匹配是裸子串 `i in text`（`:47`、`:61`）。

10. **minor** — `src/artharness/arrays.py:376-381`  
    低于 2 倍零分布才用 2,000 次复测的条件只看 `base_max6`。3,000 nt 窗口的零分布更高、且观测分落在它的 1–2 倍之间时，不会复测。

VERDICT: REQUEST_CHANGES
