# Counting independent occurrences

How to count whether a candidate partner gene recurs independently across the
RT collection — the filter that separates a real association from a single
locus amplified by clustering.

## Why it matters

The census clustered ~1.9B proteins into 198,290 clusters and kept 10,983
RT-encoding loci across 9 RT classes (paper). Most proteins therefore have
many near-identical copies, and raw hit counts measure cluster size, not
biological recurrence. A partner seen 500 times in one biosample is weaker
evidence than a partner seen 5 times in 5 biosamples.

## Procedure

1. Collect every protein matching the candidate family across all loci under
   review (HMM hits, cluster members, or annotation matches).
2. Deduplicate: collapse proteins sharing >= 90% pairwise identity into one
   occurrence. GAP: threshold — the paper describes independence filtering but
   does not publish this cutoff.
3. Require each surviving occurrence to sit on a distinct contig/locus; merge
   overlapping hits on the same contig.
4. Count distinct biosamples (independent metagenomic samples) across the
   surviving occurrences.
5. Record the RT class of the neighboring RT for each occurrence. Treat the
   association as robust only when the partner appears beside >= 2 RT classes.
   GAP: threshold — guards against a within-clade artifact.

## Reporting

Report all three numbers, never a single count:

- raw hits (before deduplication),
- independent occurrences (after dedup, distinct loci),
- distinct biosamples and RT classes spanned.

State the denominator explicitly (e.g., "occurrences per RT class X loci").

## Pitfalls

- Never report raw hits as evidence of recurrence; inflated by cluster size.
- Check biosample labels before counting: re-sequencing or co-assembly of the
  same sample is not independence. GAP: biosample identity rule.
- A partner fused to the RT in some loci still counts; note fusion separately
  since it changes the mechanism interpretation.
- If all occurrences fall in one RT class, report the association as
  clade-specific, not general, and say so in the claim wording.
