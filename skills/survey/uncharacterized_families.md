# Annotating uncharacterized protein families

Procedure for families with no database annotation — the common case for ART
partner candidates. Goal: a defensible functional hint plus a disciplined
name, not a forced assignment.

## Order of operations

1. **Domain search first.** Scan all members against Pfam with hmmsearch;
   scan reference profile HMMs against the family too (asymmetric searches
   catch weak matches). Record conditional E-values, not just hits.
   The environment ships per-ORF Pfam matches for the benchmark loci (paper).
2. **Structure search second.** At L4+, run Foldseek on each predicted
   structure against the local reference structure DB (paper: Foldseek with
   a local reference DB at L4). A structural hit at low sequence identity is
   the strongest remote-homology evidence available. Record TM-score-aligned
   hits and inspect them in PyMOL / with US-align before trusting them.
3. **Neighborhood context third.** Read the gene neighborhood: what sits
   beside the family across loci, what its operonic partner is, whether it
   fuses to the RT or the tract. Context often constrains function more than
   fold resemblance does.

## Reading the evidence

- concordant domain + structure + context: propose a function, with the
  confidence set by the weakest leg;
- structure hit only: report "fold resembling X" — do not claim the
  function, folds are reused;
- context only: report the association, leave function open.

## Naming discipline

- Name families descriptively, never after a guessed mechanism:
  `ART-partner-<clade>-<n>` style IDs beat names like "nuclease-X" unless the
  catalytic residues are demonstrably conserved. GAP: naming convention.
- If you assign a functional name, state the residue/motif evidence inline;
  curators will check it.
- Keep a stable family ID once minted; downstream tasks and the shared
  knowledge base key on it.

## Pitfalls

- Do not let one strong Foldseek hit override a contradictory domain profile.
- Predicted structures on small/low-confidence ORFs are unreliable; check
  confidence metrics where available before searching. GAP: per-model
  confidence handling.
- An uncharacterized family is a valid result — "conserved, no detectable
  homolog, consistent with a dedicated role" is a reportable finding.
