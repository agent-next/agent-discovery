# Testing novelty claims

A novelty claim ("first report of family X beside RTs") is only as strong as
the searches that failed to find a prior description. Run all required
searches before writing the word "novel".

## Required searches

Run each of these and record the query, database version, and date:

1. **HMM/profile search** — build an HMM of the family (hmmbuild) and scan it
   against Pfam and any reference profile DBs in the environment; also scan
   reference HMMs back against your proteins. A hit to an existing profile
   defeats sequence-level novelty.
2. **MMseqs2 vs reference sets** — search the family's representatives
   against the reference protein sets available in the environment (cluster
   representatives, RefSeq-like subsets). Record the best hit identity and
   coverage; a > 30% identity full-length hit to an annotated protein is
   presumptive prior art. GAP: identity guideline.
3. **Literature** — at L5 or with the literature connector, search Europe PMC
   for the family's distinctive features (architecture, neighborhood,
   organism), not just its name — novel families have no name yet.
4. **Neighborhood literature** — search for the *system* (RT + partner +
   tract), not only the protein; a known protein in an unknown arrangement
   can still support a system-level novelty claim.

## What defeats a novelty claim

- A profile-DB hit covering the family's conserved core.
- A reference-set hit at high identity over most of the length.
- A published description of the same gene arrangement, even under a
  different name.
- Any of the above in a different clade still weakens "first report"; scope
  the claim to the clade where it survives.

## Calibrated wording

- Never write "novel" unqualified. Write "no match in <databases searched>
  as of <date>".
- Report the negative results with the same care as positives: which DBs,
  which versions, best-hit statistics.
- Put the residual risk in the confidence score, not in extra adjectives —
  the structured finding carries `confidence` in [0, 1] (paper).
