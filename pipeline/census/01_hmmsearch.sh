#!/usr/bin/env bash
# pipeline/census/01_hmmsearch.sh -- census step 1: profile-HMM scan of the sequence DB.
#
# paper Methods "RT census by the agents" p.29: 52 profile HMMs assembled from
# six Pfam profiles (RVT_1, RVT_2, RVT_3, RVT_N, GIIM, Intron_maturas2), the 45
# class-specific myRT profiles, and one profile built from a Toro alignment,
# run against all database representatives.
# paper flags: hmmsearch --noali -Z 8 --domZ 8 -E 0.01 --domE 0.01
# Expected yield: 3,391,714 candidate hits (paper census table).
#
# Usage: 01_hmmsearch.sh [--dry-run] [HMM_DB] [SEQ_DB] [DOMTBLOUT]
#   --dry-run   print the hmmsearch command instead of executing it
# Defaults (env or positional):
#   HMM_DB     concatenated 52-profile HMM library   (default data/hmm/rt_profiles_52.hmm)
#   SEQ_DB     protein sequence database             (default data/seq/seqdb.faa)
#   DOMTBLOUT  hmmsearch --domtblout output          (default results/census/hmmsearch.domtblout)
# NOT-IN-PAPER: input/output paths are ours; the paper does not name the DB files.
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

HMM_DB="${POS[0]:-${HMM_DB:-data/hmm/rt_profiles_52.hmm}}"
SEQ_DB="${POS[1]:-${SEQ_DB:-data/seq/seqdb.faa}}"
DOMTBLOUT="${POS[2]:-${DOMTBLOUT:-results/census/hmmsearch.domtblout}}"

run() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '%s\n' "$*"
    else
        "$@"
    fi
}

# paper: hmmsearch --noali -Z 8 --domZ 8 -E 0.01 --domE 0.01 over 52 profile HMMs
run hmmsearch --noali -Z 8 --domZ 8 -E 0.01 --domE 0.01 \
    --domtblout "$DOMTBLOUT" "$HMM_DB" "$SEQ_DB"
