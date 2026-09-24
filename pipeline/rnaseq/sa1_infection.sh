#!/usr/bin/env bash
# pipeline/rnaseq/sa1_infection.sh -- SA1 infection time-course RNA-seq.
#
# paper Methods p.36-37: BioProject PRJNA836150 -- SA1 infection of
# Staphylococcus lentus, 12 libraries over 3 time points.
# paper: fastp 1.3.6 -- adapter trimming OFF, poly-G trimming ON,
# minimum length 12.
# paper: Bowtie2 --very-sensitive -X 1000 --no-unal against the SA1 genome
# (MW218148.1) plus the S. lentus chromosome (NZ_CP059679.1).
# paper: keep MAPQ >= 10; TPM over 259 features.
#
# Usage: sa1_infection.sh [--dry-run] [ACCESSIONS]
#   ACCESSIONS  file with one SRA run accession per line (the 12 libraries)
#               (default data/rnaseq/PRJNA836150.accessions)
# Env vars (defaults are ours; NOT-IN-PAPER path plumbing):
#   REF_SA1     SA1 genome FASTA        (paper: MW218148.1)
#   REF_HOST    S. lentus chromosome    (paper: NZ_CP059679.1)
#   FEATURES    feature annotation GTF  (paper: 259 features)
#   OUTDIR      output dir              (default results/rnaseq)
set -euo pipefail

DRY_RUN=0
POS=()
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        -h|--help) grep '^#' "$0"; exit 0 ;;
        *) POS+=("$arg") ;;
    esac
done

ACCESSIONS="${POS[0]:-${ACCESSIONS:-data/rnaseq/PRJNA836150.accessions}}"
REF_SA1="${REF_SA1:-data/rnaseq/MW218148.1.fna}"
REF_HOST="${REF_HOST:-data/rnaseq/NZ_CP059679.1.fna}"
FEATURES="${FEATURES:-data/rnaseq/features_259.gtf}"
OUT="${OUTDIR:-results/rnaseq}"

run() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '%s\n' "$1"
    else
        eval "$1"
    fi
}

# TPM from featureCounts output: TPM = (count/len) / sum(count/len) * 1e6.
# paper: TPM over 259 features. NOT-IN-PAPER: counter/normalizer plumbing.
tpm_calc() {
    python3 - "$1" "$2" <<'PY'
import sys

header = None
rows = []
with open(sys.argv[1]) as fh:
    for line in fh:
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip("\n").split("\t")
        if f[0] == "Geneid":
            header = f
            continue
        rows.append(f)
rpk = [[float(c) / float(f[5]) for c in f[6:]] for f in rows]
scale = [s / 1e6 for s in (sum(col) for col in zip(*rpk))]
with open(sys.argv[2], "w") as out:
    out.write("Geneid\t" + "\t".join(header[6:]) + "\n")
    for f, col in zip(rows, rpk):
        tpm = [c / s if s else 0.0 for c, s in zip(col, scale)]
        out.write(f[0] + "\t" + "\t".join(f"{v:.6g}" for v in tpm) + "\n")
PY
}

if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$OUT/fastq" "$OUT/trim" "$OUT/bam"
fi

# paper: combined reference of SA1 genome MW218148.1 + S. lentus NZ_CP059679.1
run "cat \"$REF_SA1\" \"$REF_HOST\" > \"$OUT/sa1_plus_host.fna\""
run "bowtie2-build \"$OUT/sa1_plus_host.fna\" \"$OUT/bt2_sa1_host\""

# NOT-IN-PAPER: accession-file plumbing. In --dry-run without the file we still
# print the per-library commands against 12 placeholder run ids (paper: 12
# libraries), so the dry run is self-contained.
acc_stream() {
    if [[ -f "$ACCESSIONS" ]]; then
        cat "$ACCESSIONS"
    elif [[ "$DRY_RUN" -eq 1 ]]; then
        printf 'SRR_PLACEHOLDER_%02d\n' $(seq 1 12)
    else
        echo "missing accessions file: $ACCESSIONS" >&2
        return 1
    fi
}

while IFS= read -r acc; do
    [[ -z "$acc" || "$acc" == \#* ]] && continue
    # paper: BioProject PRJNA836150, 12 paired-end libraries
    # NOT-IN-PAPER: fetch/prefetch plumbing
    run "prefetch -O \"$OUT/fastq\" \"$acc\""
    run "fasterq-dump --split-files -O \"$OUT/fastq\" \"$acc\""
    # paper: fastp 1.3.6 -- adapter trimming OFF, poly-G trimming ON, min length 12
    run "fastp --disable_adapter_trimming --trim_poly_g --length_required 12 -i \"$OUT/fastq/${acc}_1.fastq\" -I \"$OUT/fastq/${acc}_2.fastq\" -o \"$OUT/trim/${acc}_1.fq.gz\" -O \"$OUT/trim/${acc}_2.fq.gz\""
    # paper: Bowtie2 --very-sensitive -X 1000 --no-unal vs SA1 + host
    run "bowtie2 --very-sensitive -X 1000 --no-unal -x \"$OUT/bt2_sa1_host\" -1 \"$OUT/trim/${acc}_1.fq.gz\" -2 \"$OUT/trim/${acc}_2.fq.gz\" -S \"$OUT/bam/${acc}.sam\""
    # paper: keep MAPQ >= 10
    run "samtools view -b -q 10 \"$OUT/bam/${acc}.sam\" | samtools sort -o \"$OUT/bam/${acc}.sorted.bam\""
done < <(acc_stream)

# paper: TPM over 259 features
# NOT-IN-PAPER: featureCounts for quantification (paper states TPM only)
run "featureCounts -a \"$FEATURES\" -o \"$OUT/counts.tsv\" \"$OUT\"/bam/*.sorted.bam"
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "python3 - $OUT/counts.tsv $OUT/tpm.tsv  # TPM = (count/len)/sum(count/len)*1e6"
else
    tpm_calc "$OUT/counts.tsv" "$OUT/tpm.tsv"
fi
