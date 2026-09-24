# Paper notes — verified facts ledger

Source: Yoon, Athukoralage, Ameisen, Kauderer-Abrams, Perry, Durrant et al. (Anthropic),
"Autonomous AI agents discover reverse transcriptases with tandem repeat arrays",
2026-09-23. Local PDF: `/tmp/art-paper/art-paper.pdf` (40 pp; main text + Methods +
Supplementary Figures 1–7; Supplementary Notes NOT included in this file).
Every number below was read from the PDF text extraction (pdftotext), not from memory
or press coverage.

## Model identity
- Campaign model: "Claude Mythos 5" (Methods p.28). Public announcement: Mythos 5 =
  restricted-access twin of Claude Fable 5 (same model, different safeguards;
  Anthropic 2026-06 announcement). Public rerun substitute: Fable 5.

## Harness (Methods "Autonomous research harness" p.28; Results p.2-3)
- Every agent = a Claude Code instance; ≤58 concurrent sessions; sandbox 60 CPU cores,
  192 GiB memory, no GPU.
- Launch agent encoded 5 stages as a chain, each closed by scripted completion checks:
  1) input assembly 2) database sweep 3) RT classification 4) neighborhood census
  5) deep dives. Later-stage tasks only open after prior stage passes.
- Roles: worker / supervisor / curator / editor. 49 of 119 tasks revised ≥1×.
- Follow-ups → triage queue; released or rejected with written reason.
- Plans/results/reviews/scripts committed to a version-controlled record readable by
  every agent. Campaign ends when no dispatchable task remains.
- Connectors: metagenomic protein DB, literature search + full text, shared knowledge
  base, GPU job queue (ESMFold esmfold_v1 or ColabFold 1.6.1 alphafold2_ptm on
  A100/L4; 19 jobs).
- ~140 skill documents in sandbox; workers consulted 15; 7 are metagenomic survey
  guides (counting independent occurrences; operonic arrangement vs window background;
  adjudicating candidates; testing novelty claims; annotating uncharacterized families;
  proposing mechanisms with counterfactual evidence; drawing gene-neighborhood figures).

## Campaign accounting (Methods "Campaign accounting" p.30)
- 119 tasks: 107 completed, 10 rejected at triage, 2 stalled (one after 10 revisions,
  one after 10 failed completion checks).
- Task mix: 1 input assembly + 96 analyses + 22 report tasks; 5 stage-seeded,
  16 deep dives, 98 follow-ups.
- 949 sessions = launch 1 + worker 414 + supervisor 375 + curator 107 + editor 52.
- 76.9 agent-hours total (63.7 in worker sessions).
- Tokens: 11.3M uncached input + 14.9M output + 189.5M cache-write = 215.6M; cache
  reads excluded. 21.5 h wall clock, no human intervention.
- Session logs: 7,578 shell commands, 696 DB queries, 131 literature searches,
  61 web requests.

## Report tournament (Methods "Ranking of reports" p.30)
- 19 reports; every ordered pair once = 342 games. Judge = Mythos 5, fixed rubric,
  anonymized file names, 1–5 on impact/novelty/soundness/actionability weighted
  0.35/0.30/0.25/0.10. Soundness ≤2 → automatic loss. Bradley–Terry fit.
- ART report ranked 3rd (32 wins in 36 games).

## Metagenomic DB (Methods "Metagenomic sequence database" p.28-29)
- ~11M biosamples, mainly Logan + ENA + JGI + NCBI. prodigal-gv 2.10.0 default params
  on unannotated assemblies; source gene calls kept for annotated NCBI/JGI.
- Exclusions: incomplete CDS, non-standard AAs, >8,000 residues, degenerate k-mer
  repeats, ≥50% low-complexity (tantan).
- ~15.8B proteins → DIAMOND linear-time clustering at 90% then 70% identity (≥80%
  coverage of shorter), then cascaded 50% identity ≥80% mutual coverage →
  1,939,242,578 clusters at 50% identity. Representative = member closest to 80th
  percentile of length.
- Interface: cluster members, protein/nt sequences, gene neighborhoods, biosample
  records, precomputed Pfam-A; MMseqs2 vs representatives or vs 365M reference set
  (UniProt + nr at 90%).

## RT census (Methods "RT census by the agents" p.29)
- 52 HMMs: 6 Pfam (RVT_1, RVT_2, RVT_3, RVT_N, GIIM, Intron_maturas2) + 45 myRT
  class profiles + 1 Toro profile = 52 (grok review 2026-09-24: 6+45+1=52; the
  separate 38 lineage HMMs are tier-1 classification, not the search panel).
- hmmsearch --noali -Z 8 --domZ 8 -E 0.01 --domE 0.01 → 3,391,714 candidates.
- Retained: complete RT core (profile coverage ≥0.75), class-specific min length
  225–346. Discarded: fragments n=2,016,377; weak n=1,171,334 (bitscore<25,
  coverage<0.35, no YxDD); other n=622. Thresholds fixed beforehand on 5 reference
  RTs named in the brief (Ec86, LtrA, BPP-1 Brt, AbiK, RT-Cas1 fusion) + 2,339 labeled
  myRT sequences; retained 99.0% of full-length labeled RTs.
- 203,381 retained → MMseqs2 easy-cluster --min-seq-id 0.5 -c 0.8 --cov-mode 0 →
  198,290 clusters.
- Classification tiers: (1) 38 lineage HMMs from myRT (mafft --auto, hmmbuild),
  class-specific bitscore floor + ≥10-bit margin over every other class (precision
  0.997, 5-fold CV); (2) MMseqs2 vs labeled RTs (bitscore ≥150, cov ≥0.5, id ≥30%);
  (3) FastTree -lg -gamma of 2,241 RT domains aligned to RVT_1, 5 nearest labeled
  leaves must agree.
- Classes: retron 11,517; UG 10,759; group II intron 5,461; DGR 3,857;
  CRISPR-associated 2,067; group II-like 827; Abi 680; "novel" 25,737; "unplaced"
  137,385.

## Neighborhood census (Methods "Sampling of RT neighborhoods" p.29-30)
- 7,308 anchors: Abi 680 + group II-like 827 exhaustive; DGR 1,000 and CRISPR-assoc
  1,000 random; UG 700 proportional to clade size; retron 1,000 random + 1 control;
  group II intron 500; novel 60/clade × 16 clades; unplaced 440 largest lineages +
  200 random singletons. Caps defined by the census worker.
- Up to 3 loci per anchor from each of Logan/ENA/JGI/NCBI, 10 kb flanks.
- 7,238/7,308 anchors recovered → 10,983 loci, 79,680 CDS; 85.9% truncated by contig end.

## Partner scoring (Methods p.30)
- Families by best Pfam-A match or MMseqs2 clustering; 3,564 recurring families.
- Three promotion filters (set by worker before census): (1) conserved within ≥1 RT
  clade (≥10% of loci or ≥3 loci); (2) independent occurrences (≥3 clusters at 90% id,
  ≥3 biosamples, beside RTs of ≥2 classes); (3) RT-proximity permutation P ≤ 0.05 +
  on RT strand or ≤100 bp from adjacent gene. Controls designated beforehand.
- 46 met all 3 (+13 controls); 16 promoted after annotation review; a 17th via
  follow-up. Final: only 3 confirmed as unreported RT associations (Supp. Fig. 1B-C).

## Discovery path (Results "An unexpected observation..." p.3-5; Methods p.30-31)
- t0010 worker rejected the "phage RNA polymerase subunit" candidate (lineage-specific
  gene order) but flagged the free-standing retron-like RT in AR9-like jumbo phages.
- t0062 brief (written by t0010's supervisor): test for a retron-type ncRNA upstream.
  Neither brief mentioned repeats or arrays.
- Loci beside the polymerase had median 27 bp upstream vs 940 bp in relatives.
- Worker read the 2,900-nt flank of locus L0050 (228,907 bp Logan contig) directly;
  recognized a tandem array by eye, no tool call between retrieval and recognition; no
  repeat finder ran in the session. Repeat: CATGTGT[AT]TCGCATGT, 14 copies of a 16-nt
  repeat ≤1 mismatch, spacers 100–200 nt. Second locus L0020: ACTTGTA[AT]GAATTTCGCAAGTT.
- Worker's novelty kill-tests (Supp. Fig. 2C): 0/42 spacers match a protein (not
  CRISPR); spacers structured RNA (29/40 more stable than shuffled); 36/39
  polymerase-phages lack the RT; NART control loci lack arrays. Report ranked 3rd/19.
- Humans named the family ART (array-associated RTs) after the campaign.

## ART family + analyses (Methods "Human-directed analyses" p.31-33)
- All post-campaign analyses ran in interactive "Claude Science" sessions
  (authors direct, Claude writes/runs code).
- Family definition: BLASTP from MarsHill RT (GenBank QQM14740.1); profile from 12
  GenBank phage RTs (10 Staphylococcus + 2 Listeria phage LPJP1); hmmsearch HMMER 3.4
  E ≤ 1e-5 → 9,100 proteins; 350–900 aa kept (n=4,379); pooled with 12 phage RTs +
  2,019 myRT references; DIAMOND blastp --very-sensitive E ≤ 1e-5, link at bitscore
  ≥140; MarsHill component = 117 proteins, no reference RT; expand clusters, +706
  members ≥400 aa → 823 full-length RTs; MMseqs2 easy-cluster --min-seq-id 0.9 -c 0.8
  → 230 clusters; FAMSA + FastTree LG; ART = smallest clade containing every locus
  with a type I partner + ≥500 nt non-coding upstream → 95 representatives ART_01–95.
  geNomad 1.12.0 (db 1.9, end-to-end, default) for contig classification.
- Repeat-array detection (k-mer scan): ≤3,000 nt upstream; 20 most frequent 14-nt
  words as seeds (≥3 distinct bases, no homopolymer ≥6); non-overlapping copies ≤2
  mismatches; array called when longest regularly-spaced run R ≥3 (100–450 nt spacing)
  and exceeds longest such run in 100 mononucleotide shuffles; suppressed by longer
  runs spaced <100 nt; R = copy number; <1,500 nt upstream without array =
  not assessed; one R=3 locus retained via exact 12-nt word rule. For phylogeny tips:
  annotated repeat copies or exact 12-nt word ×3 at such spacing.
- Delimitation: ≤6,000 nt upstream, every recurring 10-nt word as seed, copies ≤1
  mismatch, longest chain at near-constant spacing (60–600 nt, 30% tolerance, single
  skipped copy allowed); score = (copies−1) × information content of conserved block
  vs region base composition; retained if beats best chain in each of 200 shuffles
  (50-nt block permutation) in both 3,000- and 6,000-nt windows; chains <2× best
  shuffle retested vs 2,000 shuffles; PWM of repeat; matches above max of 200 shuffled
  regions counted as copies; repeat = contiguous columns ≥80% consensus, 1 lapse
  tolerated; coding repeats (spacings all multiples of 3 within annotated gene) set
  aside; array adjacent to RT when no annotated gene ≥300 nt between last copy and RT.
  Outcome: arrays at 28/95 loci; none at NART loci.
- Phylogeny: 774-sequence set (98 ART+NART, 617 retron, 59 other); domain = Pfam
  RVT_1 envelope ±40 residues; MAFFT L-INS-i; trimAl -gappyout → 254 columns;
  IQ-TREE 3.1.2, ModelFinder BIC → Q.pfam+F+R6; 1,000 UFBoot + 1,000 SH-aLRT;
  midpoint rooted.
- N-terminal region: residues before first Pfam RVT_1 envelope (independent E ≤ 1e-3).
  ART NTD ~180 residues vs ≤50 typical; most variable region of the protein;
  present in every member (second hallmark).
- YxDD: present in 93/95 (2 truncated before motif); pattern [YF].DD.

## Array structure + RNA (Results p.6-9)
- 28 arrays: 0.3–4.1 kb spans; 3–21 copies; repeats 15–49 nt; each with a ~15-nt
  palindromic core; shared within but not across ART clades; spacers 120–220 nt.
- 0/42 spacers match any protein (365M reference set, E ≤ 0.001); spacer folding
  energy z < −2 vs dinucleotide-preserving shuffles for the reported fractions.
- NART (sister clade, polymerase-adjacent RTs): long NTD too, but 0/17 assessable
  loci have arrays, no ART partner; distinct single NTD fold.

## RNA-seq (Methods p.36-37; Results p.8)
- Public data: BioProject PRJNA836150 (SA1 infection of Staphylococcus lentus,
  12 libraries, 3 time points). fastp 1.3.6 (adapter trimming off, poly-G trim, min
  length 12); Bowtie2 --very-sensitive -X 1000 --no-unal vs SA1 genome MW218148.1 +
  S. lentus chromosome NZ_CP059679.1; MAPQ ≥10; TPM over 259 features.
- Array-derived RNAs = 8% of intracellular phage RNA at 15 min post infection.
- Small-RNA-seq (wet lab): plasmids in E. coli DH10B; native-locus positions
  9,448–12,951 under PLtetO-1 on pSC101 (carbenicillin); heterologous J23119 promoter
  + araBAD-driven RT on pMB1 (kanamycin); hot formamide extraction (95% formamide,
  18 mM EDTA, 65 °C, 5 min); Zymo Clean & Concentrator-5 (≥17 nt retained), in-column
  DNase; NEBNext rRNA Depletion (Bacteria) on 500 ng; Quick CIP + T4 PNK end repair;
  NEBNext Multiplex Small RNA kit (adaptors + RT primer diluted 2×); 1.5× SPRI;
  NextSeq 2000 2×151, 20% PhiX; BCL Convert 4.2.11; fastp 1.3.6; Bowtie2 v2.5.5
  --end-to-end -D 20 -R 3 -N 0 -L 12 -i S,1,0.50 -X 1000; SAMtools 1.24; MAPQ ≥2
  (plasmid libraries) / ≥10 (infection libraries); array RNA = contiguous runs ≥40 nt
  at ≥half max coverage.

## Partners (Methods "Partner genes and partner types" p.37; Results p.9)
- Partner = first gene downstream of RT. Types: I (double GNAT-like fold, ~600 aa,
  59 lineages), II (all-helical ~270 aa, 7 lineages), III (~170 aa, 3 lineages;
  carries a second recurring family directly downstream). HHblits profile merging at
  ≥90% probability over ≥half of both profiles; 36 partners searched vs Pfam-A at
  --cut_ga: no clear hits for types II/III folds.
- Co-folding (AF2-multimer / Boltz-2): ipTM ~0.6. NTD-partner co-evolution on 30-tip
  subset, 379 same-type pairs, Spearman.

## Replicates + benchmark (Methods p.38; Results p.12-13)
- 10 replicate campaigns, same harness and brief: 3,084 task records, 5,632
  transcripts; searched for 130 RT ids + 171 contig ids + cultured-phage names from
  the original; 11 sessions named a relevant contig; sessions parsed for ≥200 nt
  contiguous DNA + remarks on repeats: NONE read the upstream DNA; array missed in
  every rerun.
- Fixed-input benchmark: 7 Claude models × 5 levels × 100 attempts = 3,500 attempts,
  each isolated in Claude Code with 1M-token output budget. Inputs: 96 ART loci
  (1,093–26,554 bp, anonymized ids, gene calls, Pfam matches) + 1,131 predicted
  structures. L1 = 2 RT protein seqs in prompt; L2 = 2 loci as text in prompt; L3 =
  files + gene calling, HMMER, BLAST+, MMseqs2, MAFFT, FastTree, ViennaRNA, Python;
  L4 += structures for every ORF, Foldseek local DB, PyMOL, US-align; L5 += literature
  search, web, software install. Grading: 10 binary claims (3 on 5′ nc tract, 2 on RT,
  5 on partner); judge = Mythos 5, submission + rubric only; programmatic keyword
  screen preselects findings (no grade contribution); claims counted only when
  asserted as a conclusion (not hedged alternatives); no credit for specified
  over-claims; repeat-array claim asserted = "recognized".
- Key results (Results p.12-13): with sequences directly in context, models describe
  the array ≥90%; with tools, as low as 32% (model-dependent); reading ≥200 nt
  contiguous DNA raises recognition 16–32 pp; Mythos 5 reaches 96% with ≥2,000 nt
  in context.
- Interpretability: Evo 2 + gLM2 log-likelihood profiles spike on repeat copies
  (control: copies shuffled in place); Mythos 5 sparse-dictionary features
  "repeat-signal 1" (tokens repeating an earlier pattern verbatim) and "repeat-signal
  2" (letters in repeated motifs / garbled text) fire from copy 3 on (means 0.85–1.62
  per copy; 0.00 when copies shuffled); both also fire on non-DNA repeats planted in
  random alphanumerics (0.48/0.75 vs 0.05/0.01) → generic repeat detectors.

## External anchor points for the research brief (Supp. Note 1, NOT in the PDF)
1. Goal: identify novel RT systems on the basis of new partner-gene associations
   (Results p.3).
2. Mission directed at partner protein-coding genes, not ncDNA features (Results p.3).
3. Five stages (Methods p.28).
4. Five reference RTs named in the brief: Ec86, LtrA, BPP-1 Brt, AbiK, RT-Cas1 fusion
   (Methods p.29).
5. Brief did not mention repeats or arrays (Methods p.31, verbatim negative).
6. Census thresholds "fixed beforehand" on those references + 2,339 labeled myRTs
   (Methods p.29); sampling caps and promotion filters were agent-defined, not brief
   content (Methods p.29-30).
