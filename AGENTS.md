# AGENTS.md — art-harness

## What this repo is

A reproduction of the Anthropic ART autonomous-research-harness paper (see README).
Parameter sources are cited as `paper p.NN` / `paper Methods §name` — every constant in
`pipeline/` and `benchmark/` traces to the paper PDF (local copy referenced in
`docs/paper-notes.md`).

## Rules for agents working here

- Read `REPRODUCTION.md` before touching anything: it maps every paper element to code.
- Python under `src/artharness/` and `pipeline/*.py` is tested code: `make check` must
  pass before any commit. Shell scripts under `pipeline/*.sh` are parameter wrappers —
  keep every flag identical to the paper citation next to it.
- Do not invent paper parameters. If a value is not in the paper, mark it
  `# NOT-IN-PAPER: <reason>` in code and `GAP:` in docs.
- The reconstructed research brief lives in `brief/research_brief.md`; it is a
  reconstruction from six anchors (cited inline), NOT the verbatim original.
  Never present it as Anthropic's text.
- Task receipts: `task-runs/<YYYYMMDD>-<topic>/`.
- Commit small, one logical change per commit, Conventional Commits, no AI attribution.
- Worktrees for multi-file work: `.worktrees/<task>-<YYYYMMDD>` (org convention).
- Offline by default: unit tests must not hit the network. Live connectors get a
  `--live` flag and a recorded-fixture test mode.
