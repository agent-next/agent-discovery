# Operonic arrangement scoring

How to test whether a candidate partner gene is co-oriented with — and likely
co-transcribed with — the RT, against a window background.

## The question

A partner that shares the RT's strand and sits immediately adjacent is a
candidate operon member; a partner on the opposite strand or far away is more
likely a coincidental neighbor. The paper's ART loci place the partner beside
the RT next to a 5-prime non-coding tract (paper); the same test applies to
any candidate.

## Feature definition

Call a partner *operonic* relative to its RT when either holds:

- it is on the same strand as the RT, or
- its start lies within 100 bp of the adjacent gene boundary (i.e., it packs
  tightly against the neighboring CDS, the signature of translational
  coupling).

GAP: the 100 bp packing cutoff is our reconstruction — the paper reports a
proximity/arrangement test but does not publish the threshold.

## Permutation test

1. Fix the set of loci and their gene coordinates.
2. For each replicate, randomize the partner's position (and strand) within
   its locus window, keeping the RT and non-coding tract fixed.
3. Recompute the fraction of partners satisfying the feature definition.
4. Run >= 10,000 replicates (GAP: replicate count) and compute the empirical
   P-value: fraction of replicates whose operonic fraction is >= observed.
5. Report the arrangement as significant only at P <= 0.05.

## Reporting

- observed operonic fraction, expected fraction under the null, P-value;
- strand counts (same/opposite) alongside the P-value — the direction of the
  effect matters for mechanism;
- window definition used for randomization (contig bounds vs fixed flank).

## Pitfalls

- Do not randomize across loci of different classes as one pool; stratify by
  RT class first or the test confounds arrangement with clade composition.
- Circular contigs need wrap-aware distance; a partner across the origin can
  still be adjacent.
- A significant result supports co-regulation, not physical interaction; do
  not upgrade the claim beyond what proximity can show.
