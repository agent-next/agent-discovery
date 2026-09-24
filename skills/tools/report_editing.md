# Report editing

Every task ends with a report plus a structured submission. This is the
artifact curators, editors, and the benchmark grader read — format it for
them, not for yourself.

## Structured findings

Each finding is `{claim, evidence, confidence}` with `confidence` in [0, 1]
(paper, task specification).

- `claim`: one sentence, falsifiable, scoped (name the clade/set it covers).
- `evidence`: the data behind it — counts, E-values, P-values, figure refs.
  Point to artifacts; do not paraphrase them.
- `confidence`: your calibrated number. Reserve > 0.9 for claims with
  convergent evidence; a single supporting test caps it lower.

## Asserted vs hedged

The benchmark counts a claim only when the submission asserts it as a
conclusion — findings listed among hedged possibilities get no credit
(paper). So:

- assert what the evidence supports, as conclusions;
- keep genuine alternatives in a separate "open questions" section, clearly
  marked as non-conclusions;
- do not hedge a real conclusion to look careful — it scores as silence;
- do not assert a hope to look decisive — named over-claims get no credit
  (paper) and erode trust in the whole submission.

## What curators and editors check

- each asserted claim traces to evidence in the task record;
- confidence matches the stated evidence (no 0.95 on a single screen);
- negative results and rejected candidates are present with written reasons
  — triage requires written rejections (paper);
- figures/tables resolve, locus IDs stay anonymized;
- search logs exist for any novelty or literature claim.

## Tournament awareness

Reports are ranked pairwise under a Bradley–Terry model on impact, novelty,
soundness, actionability (paper weights 0.35/0.30/0.25/0.10); soundness <= 2
loses automatically. Soundness failures are unrecoverable — an overstated
report does not just score low, it forfeits. Edit for correctness first.
