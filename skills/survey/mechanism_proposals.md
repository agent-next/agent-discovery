# Proposing mechanisms with counterfactual evidence

A mechanism proposal earns its place only if you can state what observation
would distinguish it from its rivals. Propose hypotheses in pairs and design
the discriminator, not just the story.

## Structure of a proposal

For each candidate mechanism, write:

1. the claim (one sentence),
2. the observations it explains,
3. at least one rival hypothesis,
4. the counterfactual: an experiment or in-silico observation that gives
   different outcomes under the two hypotheses,
5. a falsifiable prediction you can check now or hand to a follow-up task.

## Worked example: the repeat array

The ART loci carry tandem repeat arrays in the 5-prime non-coding tract
(paper). Two rival mechanisms:

- **Primer synthesis** — the array is transcribed and the RT uses it to prime
  or template a specific product.
- **Template switching / storage** — the array stores repeated sequence
  information the RT copies or samples during synthesis.

Discriminators, in the paper's spirit of counterfactual evidence:

- If primer synthesis: the array's RNA product should base-pair or terminate
  at the RT's initiation site; predict a structure (ViennaRNA) and check for
  a fixed priming register across repeats.
- If template switching: individual repeats should appear, in scrambled or
  partial form, in RT-associated products elsewhere in the locus; search
  flanks and partner genes for repeat-derived sequence.
- Both: examine repeat unit boundaries — primer use predicts conserved
  junctions, storage predicts variable copy number without junction
  constraint.

GAP: these specific discriminators are our reconstruction; the paper
requires mechanism proposals to carry testable predictions but does not
publish the per-mechanism tests.

## Falsifiability bar

- "More study is needed" is not a prediction. A prediction names an
  observable quantity and the value range each hypothesis implies.
- Prefer tests executable in the sandbox (alignment, structure prediction,
  RNA folding) before wet-lab suggestions; note wet-lab tests as protocols.
- Report the discriminating experiment in the finding's `evidence` field so
  curators can see the proposal is falsifiable, not just plausible.
