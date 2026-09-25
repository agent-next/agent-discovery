All findings verified against the tree. Compiling the consolidated report.

---

## VERIFY-BY — `make check` tail

```
ruff check src tests pipeline benchmark
All checks passed!
python3 -m pytest
........................................................................ [ 56%]
.......................................................                  [100%]
127 passed in 9.72s
```

Green tree confirmed (127 passed, as expected). Reviewed branch `devin/build-modules` content at this checkout. I independently spot-verified every major finding's citation and mechanism below; one citation corrected (B3), one cross-agent duplicate merged (C9/D3).

---

## A — Core harness semantics (`src/artharness/`)

**A1 — `src/artharness/roles.py:41` + `runner/base.py:153` — supervisor-proposed tasks are dead wiring; the paper's t0010→t0062 mechanism has no code path.**
The supervisor prompt instructs "write its brief after the verdict under PROPOSED_TASK_BRIEF", and the module docstring claims supervisor briefs land with `origin=FOLLOW_UP`. But `ClaudeCodeBackend.run` only parses `PROPOSE_FOLLOWUP:` and only `if spec.role == "worker"` (`base.py:153`); the orchestrator reads `sout` solely for `.verdict`/`.verdict_notes` (`orchestrator.py:185-187`). Scenario: live supervisor emits `VERDICT: accept` + `PROPOSED_TASK_BRIEF: test for a retron-type ncRNA upstream` → brief silently discarded; the discovery path the paper credits cannot occur. Confidence 0.9. **major** (rule 3).

**A2 — `src/artharness/orchestrator.py:98` — stage gates are polled synchronously before any dispatch; an honest record-store gate can never pass.**
`run_stage_chain` runs `while not gate(prev)` for all prior stages *before* seeding each stage, and `run()` is only callable after the chain returns. A gate checking "did stage-N tasks complete" sees only queued tasks → returns False → re-polled `max_gate_failures` times on identical state → `RuntimeError` at `:101-102`. The only escape is a gate that itself pumps `self.run()` — undocumented, re-entrant. `tests/test_orchestrator.py:54` locks the abort in (rule 4). Confidence 0.6. **major**.

**A3 — `src/artharness/runner/base.py:139` and `:146` — verdict regexes take the FIRST match in the whole transcript; a restated format example beats the real verdict (fails unsafe — rule 6).**
`re.search(r"VERDICT:\s*(accept|revise)\b")` returns the first occurrence anywhere. A supervisor writing "I may return VERDICT: accept if adequate … VERDICT: revise" parses as `accept` → `orchestrator.py:187` accepts work meant to be bounced. An editor echoing "FILE: yes or FILE: no" then concluding `FILE: no` parses `yes` → `file_report` (`:240-243`) files a rejected report — worse than None. Confidence 0.7. **major**.

**A4 — `orchestrator.py:106`/`:111` — `None` dereference when task budget bites during seeding.** `_new_task` returns `None` at `:116-118` when `max_tasks_total` is hit; `opened[stage].append(rec.task_id)` → `AttributeError`, unhandled crash instead of recorded rejection. Confidence 0.95. **minor**.

**A5 — `orchestrator.py:142` — triage-rejection filenames collide.** `triage-rejection-{len(list_tasks())}.md` uses a count that doesn't change between consecutive rejections → second rejection overwrites the first; only the last written reason survives (paper requires written reason per rejection). Confidence 0.9. **minor**.

**A6 — `orchestrator.py:82`/`:152` — `self._sem` guards nothing.** Semaphore acquired/released inside a strictly serial loop; `max_concurrent_sessions=58` advertised but inert; all counters/store writes unguarded if dispatch is ever parallelized. Confidence 0.9. **minor**.

**A7 — `orchestrator.py:200-204` — revision worker passes skip the completion check** that the initial pass enforces at `:160-169`; a revision that deletes/never writes `summary.md` is neither stalled nor noticed — asymmetric stall accounting vs the paper's "ten failed completion checks". Confidence 0.75. **minor**.

**A8 — `orchestrator.py:211` — `report.revised` undercounts.** Incremented only on the accept path; a task stalling after 10 revisions is never counted "revised ≥1×" (paper: 49/119). Confidence 0.8. **minor**.

**A9 — `orchestrator.py:54`/`:63` — `CampaignReport.tasks_total` never populated**; `render()` always prints 0. Confidence 0.95. **minor**.

**A10 — `orchestrator.py:242` — `file_report` forces `COMPLETED` unconditionally.** No guard on current state: filing on an OPEN/STALLED task flips it to COMPLETED, bypassing worker/supervisor/curator and resurrecting stalled tasks. Confidence 0.7. **minor**.

**A11 — `records.py:31`/`:37`/`:45` — `PLANNED`, `REJECTED`, `TaskOrigin.REPORT` have no producer** (zero assignments/constructions); the paper's 22 report tasks can't be represented as queued tasks. Confidence 0.85. **minor**.

**A12 — `records.py:135` — non-atomic `meta.json` write**; torn write → `JSONDecodeError` in `get()`, which also bricks `list_tasks()`. Confidence 0.8. **minor**.

**A13 — `records.py:142` — `git commit` lacks a pathspec**; `git add -A .` stages under root but `commit` sweeps the entire index — a store inside a larger repo commits unrelated staged changes. Confidence 0.6. **minor**.

**A14 — `roles.py:87` — unguarded `iterdir()` on `artifacts/`**; a worker that removes it crashes `_dispatch` via `FileNotFoundError`. Confidence 0.65. **minor**.

**A15 — `runner/base.py:159` — `duration_s=0.0` hardcoded** (verified at `:159`); `SessionLedger.summary()` reports 0 agent-hours for any real campaign — silently corrupts the 76.9h/63.7h-comparable metric. Confidence 0.9. **minor**.

**A16 — `tournament.py:87-88` — `n_ij = len(names) - 1` is wrong; comment is false.** Every ordered pair plays once → each unordered pair plays **2** games; Hunter MM should use `n_ij = 2`. Benign today only because the uniform factor cancels under per-iteration normalization (`:103`). Confidence 0.85. **minor**.

**A17 — `tournament.py:99` — convergence check is dead**; `delta` compares pre-normalization `new` vs post-normalization `p`, so `delta < 1e-8` is unreachable → always burns all 200 iterations. Confidence 0.8. **minor**.

*Verified clean:* stall counters hit the limit at exactly 10 both ways (`:167`, `:196`); absent-verdict fail-safe direction is correct (`:187`, `:235`) — the residual hole is first-match parsing (A3); tournament 342 games/weights/soundness≤2 all correct; accounting sums match the ledger format; no rule-5 import traps remain.

---

## B — Science correctness (`arrays.py`, `pipeline/**`)

**B1 — `src/artharness/arrays.py:307` — the "single skipped copy" rule is unreachable for the spacing regime it exists for.** `is_skip` is evaluated only inside `if not (lo <= gap <= hi)` (`:306`), requiring gap ∈ (600, 1200] — i.e. base spacing >300 nt. Every observed ART array has start-to-start spacing ≈135–269 nt (ledger, Array structure), so a missing copy yields gap ≈2×spacing ≤ 540, which lands *inside* [60,600] → treated as a normal gap → `abs(gap−med) > 0.3·med` → `break`. Copies at 0,200,400,800,1000 yield a 3-chain instead of the true 5-copy chain, cutting the `(copies−1)` score and potentially dropping below `MIN_RUN`. The greedy iteration also can't skip an interior outlier (0,200,210,400 breaks at the 10-nt gap). Confidence 0.8. **major**.

**B2 — `src/artharness/arrays.py:149` — `_regular_runs` discards the whole run on one irregular in-range gap** instead of keeping the longest regular sub-run. Copies at 0,200,400,700,900,1100 → gaps [200,200,300,200,200], med=200, 300>260 → zero runs kept though {0,200,400} is a regular R=3 run; `kmer_scan` returns `no_array` where the paper calls R=3. Applies symmetrically to the shuffle null, so the false negative survives `r > shuffled_best`. Confidence 0.7. **major**.

**B3 — `pipeline/db/build_subset.sh:87` (keys built at `:68`/`:75`) — tantan low-complexity filter is dead wiring (rule 3).** `masked` is keyed by the *full* header line (`name = line[1:]`), but the lookup uses `header.split()[0]`. prodigal headers always contain spaces and tantan echoes the full header → `masked.get(...)` returns `""` for every sequence → the "≥50% low-complexity" exclusion never removes anything. *(Citation corrected from the finder's :83; the buggy line is `:87`.)* Confidence 0.8. **major**.

**B4 — `pipeline/census/06_score_partners.py:112` — `proximity_qualifies` adds an `rt_adjacent` conjunct the paper doesn't state.** Ledger filter 3: `P ≤ 0.05 AND (on RT strand OR ≤100 bp from adjacent gene)`. Requiring direct RT adjacency first undercounts the observed statistic → inflated permutation p-values → real families under-promoted. `tests/test_pipeline_logic.py:384` locks the extra conjunct in (rule 4-adjacent). Confidence 0.55. **major**.

**B5 — `arrays.py:465` — `pwm_extend` can emit negative copy starts** (`extra.append(i - off)` with `i < block_offset`), corrupting `spacings` and downstream coordinates. Confidence 0.6. **minor**.

**B6 — `arrays.py:417` — `build_pwm` ZeroDivisionError** when a base is absent from the window: `background[b]=0.0` isn't caught by `.get(b, 0.25)` since the key exists. Confidence 0.7. **minor**.

**B7 — `arrays.py:277` — consensus block tolerates unlimited non-consecutive lapses** (`lapses` resets per ≥80% column); ledger reads "1 lapse tolerated" — if that caps the whole block, repeat length and IC score are inflated. Interpretation-dependent. Confidence 0.45. **minor**.

**B8 — `pipeline/census/05_sample_neighborhoods.py:47` — `UG_TAKE_WHOLE_BELOW = 30` tagged `# paper:` but absent from the ledger** ("UG 700 proportional to clade size" only); needs `NOT-IN-PAPER:`/`GAP:` per rule 9. Same class: `arrays.py:319` reuses `MIN_RUN` as the delimitation minimum chain length — the paper states no copy minimum there. Confidence 0.55. **minor**.

**B9 — `pipeline/art_family/family_definition.sh:6` — `mafft --auto + hmmbuild` attributed to the paper** for the 12-phage-RT profile; the ledger assigns that toolchain to the census tier-1 lineage HMMs and says only "profile from 12 GenBank phage RTs". Provenance over-claim (rule 9). Confidence 0.55. **minor**.

**B10 — missing paper rules with no GAP label:** "coding repeats (spacings all multiples of 3 within annotated gene) set aside" and "array adjacent to RT when no annotated gene ≥300 nt between last copy and RT" are implemented nowhere and unflagged. Confidence 0.6. **minor**.

**B11 — `arrays.py:267` and `:331` — nondeterministic consensus tie-breaks**: `max(set(col), key=col.count)` depends on hash order → `repeat`/`block_offset` can vary across `PYTHONHASHSEED`s — delimitation output non-reproducible. Confidence 0.6. **minor**.

*Verified clean:* hmmsearch flags exact; `02_filter.py` domtblout indices + weak-hit AND semantics correct; `03_cluster.sh` real flags/units; `04_classify.py` 10-bit margin and class arithmetic; quotas close at exactly 7,308; phylogeny envelope ±40 bed math, `-gappyout`, MFP/BIC, `-B 1000`, `-alrt 1000`, midpoint root; family-definition bitscore≥140, 350–900/≥400 aa, `--min-seq-id 0.9 -c 0.8`, genomad; RNA-seq fastp/Bowtie2/MAPQ flags; window tails `[-3000:]`/`[-6000:]` (rule 7 ✓), `block_offset` threading (rule 8 ✓), shuffle counts 100/200/2000.

---

## C — Benchmark / connectors / scripts / experiments

**C1 — `benchmark/run_benchmark.py:66-73` (with `:169-170`) — level environment is dead wiring: sessions get identical capabilities and an empty workdir.** `SessionSpec` has no field for tools/files/web/install, and nothing consumes `spec.env` (only tests read `env.*`). Consequences: (a) the L1→L5 tool ladder exists only in prompt text — the benchmark's measured variable is never varied; (b) `env.files` (the 96 loci, tables, structures) is never copied into `spec.run_dir`, which is `mkdir`'d empty — L3–L5 agents are told "Input files: loci/, …" but run in an empty directory. `ARTHARNESS_ALLOW_LIVE=1 … --levels L3` records levels that never differed. Confidence 0.85. **major** (rule 3).

**C2 — `benchmark/rubric.py:180` (negation source at `:156`) — claim-matching is negation-blind; an asserted denial earns the claim and `recognized`.** `"not"` is stripped in `_STOP`; any asserted finding sharing ≥2 content tokens maps to a claim. A submission asserting as conclusion "the 5′ non-coding tract contains *no* tandem repeat array" shares 7 tokens with nct-1 → `score+1` and `recognized_repeat_array=True` — the headline metric fires on the opposite conclusion. Confidence 0.85. **major**.

**C3 — `benchmark/run_benchmark.py:154-157` — `--inputs` silently fabricates synthetic data** when `inputs_root/<level>/loci` is absent: `write_synthetic_inputs(ldir)` writes 180-nt random placeholders *into the user's inputs dir* and results record nothing marking them synthetic; the required `L1/…/L5/` layout is documented nowhere. Confidence 0.65. **major**.

**C7 — `scripts/scan_genome.py:62-70` — `read_fasta` silently concatenates multi-record FASTA under the last header.** On multi-contig `.fna` every record's sequence is appended to one string and `header` ends as the last record's id; contig junctions fabricate 14-mers and copy-spacings that don't exist — two contigs with 2 copies each yield a phantom 4-copy "array" reported under the wrong contig. Confidence 0.8. **major**.

**C9/D3 (merged) — `src/artharness/connectors/protein_db.py:212` — `min_seq_id=0.9` misattributes the paper, locked by a test.** Comment reads `# paper: searches at 90% identity`; the paper's 90% is the *clustering* identity of the 365M reference set — the stated tier-2 search thresholds are bitscore ≥150 / cov ≥0.5 / id ≥30%. `tests/test_protein_db.py:84` asserts the miscited value (rule 4). Every default `mmseqs easy-search` is far more stringent than anything the paper states. Confidence 0.8. **major** (rule 1 + 9).

**C4 — `benchmark/levels.py:62-63`,`:95` — L3+ file sets leak `proteins/*.faa`** (L1's payload; excluded only `structures`), and the L3 prompt enumerates only `loci/, gene_calls.tsv, pfam_matches.tsv` — prompt and file set disagree. Confidence 0.7. **minor**.

**C5 — `levels.py:73-76` — `_inline` takes the first two sorted `*.faa`**, which with real inputs are likely two ORFs of the same locus, not the two loci's RTs. Confidence 0.55. **minor**.

**C6 — `levels.py:83` — L1/L2 `env.workdir` defaults to the full inputs tree**, leaking all 96 loci/proteins/structures to any backend that honors it (masked today by C1). Confidence 0.6. **minor**.

**C8 — `scripts/scan_genome.py:38-41`,`:35`,`:33-34`,`:86-87`,`:102` — dead helper + duplicated/unlabeled constants.** `arrays_min_spacing()` is never called (verified: only the definition exists); local `MIN_SPACING = 100` duplicates `artharness.arrays.MIN_SPACING` — a fix wouldn't propagate; `MIN_COUNT_FOR_SEED`, `MAX_SEEDS`, literals `3000`/`100` duplicate named constants without `NOT-IN-PAPER:` labels (rule 9). Confidence 0.8. **pre-existing/minor** (noted in the round-4 receipt).

**C10 — `protein_db.py:174-175` — `proteins_beside` mislabels a paper constant as NOT-IN-PAPER** ("paper does not specify the neighborhood window size") while `flank_bp=10_000` is exactly the paper's 10 kb flanks. Inverted provenance. Confidence 0.7. **minor**.

**C11 — `protein_db.py:163` — `neighbors()` crashes on NULL coordinates** (`row["start"] - flank_bp` → TypeError; schema permits NULL at `:47-48`). Confidence 0.75. **minor**.

**C12 — `run_benchmark.py:101`,`:98` — `asserted` defaults True; malformed finding aborts the run.** `f.get("asserted", True)` grades unflagged hedged findings as asserted conclusions (inflation, compounds C2); `f["claim"]` → KeyError kills a 3,500-attempt run on one malformed submission. `AttemptSpec.seed` (`:50`,`:171`) is never read. Confidence 0.7. **minor**.

**C13 — `literature.py:89` — EuropePMC `search` crashes on `"resultList": null`** (AttributeError; malformed JSON/timeout/HTTP errors propagate raw, no retry). Offline gating itself is correct. Confidence 0.55. **minor**.

**C14 — `gpu_queue.py:45` — `GpuJob.hardware` unvalidated** despite `GPU_TARGETS` at `:29`. Confidence 0.8. **minor**.

**C15 — `experiments/forensics.py:30`,`:72`,`:92` — per-line DNA regex misses wrapped sequences**; ≥200-nt DNA printed as wrapped FASTA (60–80 nt/line) yields `dna_runs_ge200nt=0` — false negative on the measured quantity; and the metric counts lines-containing-a-run, not runs. (The round-4 prior-line ordering fix at `:74-85` is correct.) Confidence 0.55. **minor**.

*Hygiene:* no credentials/tokens/internal hosts/absolute paths in scope; SQL parameterized; single subprocess call is list-based; `urlencode` for queries; live gating consistent (`execute`/`live`/`ARTHARNESS_ALLOW_LIVE`).

---

## D — Tests honesty + docs

**D1 — `tests/test_forensics.py:71-80` — vacuous test: the same-line remark-before-DNA case is never exercised.** The fixture transcript `"tandem repeat suspected then {dna}\n"` contains no identifier, so `named` is empty at `experiments/forensics.py:63-66` → transcript skipped → `out == []` holds for *any* ordering logic. Had it included the id, a correct implementation returns a record and the test fails. Mutation demo: change `forensics.py:84` to drop the start-order check → test still passes. Zero regression power on the exact behavior it names (Bars violation). Confidence 0.95. **major**.

**D2 — `benchmark/run_benchmark.py:4-5` vs `runner/base.py:120-127` — the 1M-token output budget is never enforced.** `max_output_tokens` is plumbed through `SessionSpec` (`base.py:43`) but `ClaudeCodeBackend.run` never reads it — no flag, no truncation. `config.py:36` `benchmark_max_output_tokens` is read nowhere. Docstring claims the paper's per-attempt isolation control is reproduced; it's only recorded into results.jsonl. Confidence 0.9. **major**.

**D3 — merged into C9** (`protein_db.py:212` miscited constant + `test_protein_db.py:84` locks it).

**D4 — `REPRODUCTION.md:42-43` — verification ladder targets the wrong array/copy number and a nonexistent script.** "The MarsHill locus (MW248466.1) must yield a 14-copy array call" — MarsHill's array has **5** copies with a 14-nt core (`ATATGAATACGTAT`); 14 copies belongs to the L0050 discovery contig. The repo's own real-data receipt (`task-runs/20260924-devin-build/real-genome-scan.txt:2`) shows R=5 with exactly that seed on MW248466.1 — the criterion is permanently unsatisfiable as written. And no MarsHill array-check script exists in `pipeline/art_family/` (only `family_definition.sh`, `phylogeny.sh`); nothing downloads ENA. Confidence 0.85. **major**.

**D5 — `REPRODUCTION.md:44-45` — benchmark-parity levels misattributed.** "Loci in context ≥90%" is **L2** (L1 is two protein sequences); "as low as 32%" is **L4** (Opus 5), not L3; 96% is the ≥200-nt dose-response figure, not per-level. Confidence 0.8. **minor**.

**D6 — `src/artharness/arrays.py:518-537` — `exact_word_scan` (the paper's "exact 12-nt word ×3" rule) has no test and no call site** anywhere in `pipeline/`/`scripts/`/`experiments/` — a regression ships silently (rule 3). Confidence 0.9. **minor**.

**D7 — `experiments/forensics.py:31-32` — `REPEAT_WORDS` keyword list decides what counts as "remarks on repeats"** but carries no NOT-IN-PAPER/GAP marker; the paper publishes no term list. Confidence 0.8. **minor**.

**D8 — `tests/test_pipeline_flags.py:149`,`:155` — flag-oracle asserts comment-only tokens** (`">=50%"`, `"80th"` exist only in comments); the oracle passes even if `apply_filters`/`select_reps` were deleted — checks documentation, not behavior. Confidence 0.9. **minor**.

**D9 — `TASKS.md:29-34` contradicts repo state** — paper-notes/REPRODUCTION/brief listed "Queued" and v0.1.0 unchecked while `:24` says PR #1 merged and v0.1.0 tagged; all files exist. Confidence 0.7. **pre-existing**.

*Verified correct (no finding):* quota sum 7,308; class counts → 198,290; all external-tool flags vs ledger; weak-hit AND semantics; benchmark task_statement verbatim match; brief labeled reconstruction everywhere.

---

**Cross-cutting notes**
- The five-round grok fixes hold up: verdict fail-safe *direction*, window tails, `block_offset` threading, weak-hit AND, flag realism are all correctly handled. The residual classes are **dead wiring** (A1, A6, A11, B3, C1, D2, D6 — the biggest cluster), **negation/polarity blindness** (C2, C12), and **vacuous/comment-oracle tests** (D1, D8).
- Non-finding: paper-notes' own component sum 11.3+14.9+189.5 = 215.7 vs stated 215.6M is a rounding artifact in the ledger/paper, not a code bug.
- Top priority if a fix round follows: A1, A3, B1, B3, C1, C2, C7, C9, D2, D4.

GOAL_COMPLETE