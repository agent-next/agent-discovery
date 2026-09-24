# Adjudicating candidate partner genes

The promotion rules for moving a candidate partner gene from "observed near an
RT" to "reported as associated". Apply all three filters; a candidate must
pass each to be promoted.

## The three filters

### 1. Clade conservation

The candidate recurs across the clade at a nontrivial rate: present in >= 10%
of the clade's loci OR at >= 3 independent loci, whichever is met first.
GAP: thresholds — the paper describes conservation-based triage of partner
candidates but does not publish these cutoffs.

- Below both thresholds: keep the gene on the watchlist; do not promote.
- Count loci, not protein copies — run `independent_occurrences` first.

### 2. Independence

Occurrences must be independent in the sense of `independent_occurrences`:
deduplicated at >= 90% identity, on distinct loci, and — for a claim of
general association — spanning >= 2 RT classes.

- All occurrences in one biosample or one RT class: demote to
  "clade-specific candidate", never claim a general association.

### 3. Proximity / operonic arrangement

The candidate must pass the `operonic_arrangement` permutation test
(P <= 0.05) against randomized positions in the locus window.

- A conserved family that fails the arrangement test is probably a common
  neighbor (e.g., a frequent phage gene), not an RT partner. Reject.

## When to reject outright

- Any filter fails after the full data is in — do not re-run with relaxed
  thresholds to rescue a favorite candidate.
- The candidate's loci are explainable by a single contig assembly artifact
  (duplicated contig ends, mis-binned scaffolds).
- The "partner" is a ubiquitous mobile-element gene (transposase, integrase)
  whose co-occurrence is expected a priori; require the arrangement signal to
  be unusually strong before even keeping it on the watchlist.

## Reporting

For each candidate, log: filter outcomes, the numbers behind each (fraction
conserved, independent count, P-value), and the decision. Rejected candidates
stay in the task record with a written reason — the harness requires written
rejections at triage (paper).
