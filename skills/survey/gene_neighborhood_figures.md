# Gene neighborhood figures

House style for locus figures that go into reports. One page, reproducible,
anonymous — the benchmark inputs carry anonymized locus identifiers (paper),
and figures must not re-identify them.

## Layout

- One horizontal track per locus, drawn to nucleotide scale.
- Genes as block arrows in the direction of transcription: arrowhead toward
  the 3-prime end, so same-strand operons read as parallel arrows.
- RT in one fixed color, candidate partner in a second, all other genes in
  grey; non-coding tracts and repeat arrays as a hatched or braced segment on
  the track — do not draw them as genes.
- Repeat arrays: draw the tract boundary and mark repeat copy number in the
  label, not one box per repeat (arrays can be tens of units).

## Scale and windows

- Show a fixed flank window of 10 kb on each side of the feature of interest
  (GAP: window size — the paper's figures show locus neighborhoods but do
  not publish the exact flank).
- Always include a scale bar in kb; tracks must share one scale so lengths
  are comparable across loci.
- If loci differ greatly in span (the benchmark set spans 1,093–26,554 bp —
  paper), align tracks on the RT start, not on contig ends.

## Labels

- Label tracks by anonymized locus ID only (e.g., `locus_017`); never by
  contig name, accession, or biosample.
- Annotate: strand, gene length where informative, Pfam/family assignment,
  and the specific claim the figure supports.
- Caption states: window size, alignment point, color legend, source script.

## Reproducibility

- Figures are produced by a script committed next to the task receipt, taking
  the gene-calls table as input — no hand-edited diagrams.
- Keep the plotting code deterministic: fixed colors, fixed order (sorted
  locus IDs), no random layout.
- Save as PDF or SVG plus a PNG preview; the report embeds the PNG and links
  the vector file.
