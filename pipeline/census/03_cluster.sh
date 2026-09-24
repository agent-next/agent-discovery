#!/usr/bin/env bash
# pipeline/census/03_cluster.sh -- census step 3: cluster retained RT candidates.
#
# paper Methods "RT census by the agents" p.29: MMseqs2 easy-cluster
# --min-seq-id 0.5 -c 0.8 --cov-mode 0 over the 203,381 retained sequences.
# Expected yield: 198,290 clusters (paper census table).
#
# Usage: 03_cluster.sh [--dry-run] [IN_FAA] [OUT_PREFIX] [TMP_DIR]
#   --dry-run   print the mmseqs command instead of executing it
# Defaults (env or positional):
#   IN_FAA      filtered candidate proteins   (default results/census/filtered.faa)
#   OUT_PREFIX  cluster output prefix         (default results/census/clu)
#   TMP_DIR     mmseqs tmp directory          (default results/census/tmp)
# NOT-IN-PAPER: input/output paths are ours; the paper does not name the files.
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

IN_FAA="${POS[0]:-${IN_FAA:-results/census/filtered.faa}}"
OUT_PREFIX="${POS[1]:-${OUT_PREFIX:-results/census/clu}}"
TMP_DIR="${POS[2]:-${TMP_DIR:-results/census/tmp}}"

run() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '%s\n' "$*"
    else
        "$@"
    fi
}

# paper: mmseqs easy-cluster --min-seq-id 0.5 -c 0.8 --cov-mode 0
run mmseqs easy-cluster "$IN_FAA" "$OUT_PREFIX" "$TMP_DIR" \
    --min-seq-id 0.5 -c 0.8 --cov-mode 0
