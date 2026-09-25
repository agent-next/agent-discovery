# TASKS.md — art-harness build queue

Goal: max reproduction of Yoon et al. 2026 (ART harness). Push every layer until a
real blocker is hit; every blocker gets a WHY/HOW/WHAT entry in REPRODUCTION.md §Gaps.

## Done
- [x] Repo scaffold, packaging, CI (`main` @ 41e2f44, private, agent-next/agent-discovery)
- [x] Harness core: records/knowledge/roles/orchestrator/tournament/accounting/backends (23 tests)
- [x] `arrays.py`: paper-exact k-mer scan + delimitation (Methods p.32), tested on synthetic ART arrays
- [x] Paper verified locally: `/tmp/art-paper/art-paper.pdf` (40 pp; main + Methods + Supp Figs 1–7; NO Supp Notes in file)

## In flight
- [ ] Devin worker `devin/build-modules`: benchmark/ (task statement, rubric 10-claim,
      levels L1–L5, runner), pipeline/ (census 6 steps, art_family 2, rnaseq, db_subset,
      all flag-exact + dry-run), connectors (literature/protein_db/gpu_queue),
      skills/ (7 survey + 5 tools guides), 43 tests — receipt:
      task-runs/20260924-devin-build/
- [ ] gpt6pro Robin/Kosmos borrow-notes: FAILED (upstream timeout, no output) — recorded;
      do not block on it

## Round-2 (grok delta re-verify in flight)
- [x] Round-1 grok review: REQUEST_CHANGES, 15 findings — ALL fixed + pushed (babd1a9)
- [x] grok delta re-verify: rounds 2-5; round-5 VERDICT: APPROVE, 0 new findings (162 tests)
- [x] PR #1 merged to main; v0.1.0 tagged
- [x] local checkout dir renamed art-harness -> agent-discovery (post-review)
- [ ] boss HTML report (goal-html-report) at closeout

## Queued (I own these)
- [ ] docs/paper-notes.md — verified facts ledger with page refs
- [ ] REPRODUCTION.md — paper-element → component map + WHY/HOW/WHAT gap ledger
- [ ] brief/research_brief.md — 6-anchor reconstruction (labeled non-verbatim)
- [ ] Verify Devin PR by execution (fresh clone, make check, dry-runs, key tests)
- [x] Independent review dispatched (grok, b8ahfz2b9) — receipt: task-runs/20260924-devin-build/grok-review.md
- [ ] Merge via authorized gate; tag v0.1.0
- [ ] Session handoff: memory files written (MEMORY.md index update blocked by immutable attr — owner action)

## Blockers ledger (move to REPRODUCTION.md §Gaps when confirmed)
- Supp. Note 1 verbatim brief: not released anywhere (checked: PDF, news page, HN 752
  comments, bioRxiv/arXiv/SS/OA, Wayback) → reconstruct from 6 anchors
- Session transcripts: not released
- Mythos 5 checkpoint + internal signals: restricted-access model; interpretability
  claims not independently re-runnable → substitute Fable 5, mark model-delta
- Planetary DB build (15.8B proteins → 1.94B clusters): needs cluster-class compute;
  provide subset builder + document scale-out path
- Wet lab: protocols documented, execution out of scope (no lab)
