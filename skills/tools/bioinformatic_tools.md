# Bioinformatic toolset

The offline tools available from L3 up (paper: gene calling, HMMER, BLAST+,
MMseqs2, MAFFT, FastTree, ViennaRNA, Python at L3; Foldseek, PyMOL, US-align
added at L4). Short guidance per tool; check `--help` for the installed
version's flags.

## prodigal-gv — gene calling

- Use: call ORFs on contigs/loci, including giant-virus and phage gene
  models (gv variant).
- Key flags: `-p meta` for fragmented metagenomic contigs; `-a`/`-d` for
  protein/nucleotide FASTA output.
- Output: FASTA + GFF/Gbk coordinates — feed `coordinates`-style tables.

## HMMER — profile HMMs

- `hmmsearch`: query HMM vs protein DB; report conditional E-values.
- `hmmbuild`: build a family HMM from a MSA — required before any novelty
  or conservation screen of your own family.
- Key flags: `--domtblout` for parseable domain tables; `--cut_ga` only when
  the profile defines gathering thresholds.

## BLAST+ / DIAMOND — pairwise search

- BLAST+: small query sets, need exact statistics (`-outfmt 6` for tables).
- DIAMOND: large-scale screens vs big protein sets; `--ultra-sensitive`
  when remote homology matters, and say the mode used in the report.

## MMseqs2 — clustering and fast search

- `mmseqs easy-search`: representative vs reference-set screens (novelty).
- `mmseqs easy-cluster`: deduplicate a family — this is the 90%-identity
  dedup step in `independent_occurrences`. GAP: threshold.
- Output: TSV; record `--min-seq-id` and coverage mode used.

## MAFFT / FAMSA — alignment

- MAFFT `--auto` default; `linsi` for small families where accuracy matters.
- FAMSA: very large families where MAFFT is too slow.
- Always inspect the alignment before treeing; a bad MSA makes a confident
  wrong tree.

## FastTree / IQ-TREE — phylogeny

- FastTree: quick placement of hundreds of sequences (`-gamma -lg`).
- IQ-TREE: final trees for claims — model selection plus ultrafast
  bootstrap (`-m MFP -B 1000`); report support values.
- trimAl first: `-automated1` to strip unreliable columns before IQ-TREE.

## ViennaRNA — tract folding

- `RNAfold`/`RNAalifold` for repeat-array and non-coding-tract secondary
  structure; conserved structure across an alignment (`RNAalifold`) is the
  evidence that matters, not a single fold.

## Foldseek / US-align / PyMOL — structures (L4+)

- Foldseek `easy-search`: predicted structure vs local reference DB
  (paper: local reference structure DB); report E-value and aligned length.
- US-align: TM-score between two structures; TM >= 0.5 suggests same fold.
  GAP: interpretation threshold is standard practice, not stated in paper.
- PyMOL: figure rendering and hit inspection; script it (`-c script.py`),
  never hand-edit a figure.
