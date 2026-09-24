"""Census step 5 — sample anchor RTs and their genomic neighborhoods.

paper Methods "Sampling of RT neighborhoods" p.29-30 — the census worker set
per-class sampling caps and drew 7,308 RT clusters as anchors: Abi 680 +
group II-like 827 (exhaustive); DGR 1,000 and CRISPR-assoc 1,000 (random);
UG 700 (proportional to clade size, with clades of fewer than 30 clusters
taken whole); retron 1,000 random + 1 control and group II intron 500 random
(every retron and group II intron cluster carried a single clade label, so
these two classes were sampled at random); novel 60/clade x 29 clades;
unplaced 440 largest lineages + 200 random singletons.
paper: up to 3 loci per anchor from each of Logan / ENA / JGI / NCBI with
10 kb flanks. Loci were recovered for 7,238 of the 7,308 anchors (10,983 loci
with 79,680 coding sequences); 85.9% of windows were truncated by a contig end.
paper: at these caps the worker estimated a family had to occur at 0.3-0.6%
of a class's loci to reach three independent occurrences.

GAP: the stated quotas sum to 8,088 (incl. the retron control), not the
reported 7,308; quotas are kept as stated and TOTAL_ANCHORS is the paper's
reported figure for cross-checking.

Sampling is seeded (deterministic). Stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# paper: reported anchor total
TOTAL_ANCHORS = 7_308

# paper: per-class anchor quotas (see module docstring for the census text)
QUOTA_EXHAUSTIVE: dict[str, int] = {"Abi": 680, "group II-like": 827}
QUOTA_RANDOM: dict[str, int] = {
    "DGR": 1_000,
    "CRISPR-assoc": 1_000,
    "retron": 1_000,
    "group II intron": 500,
}
QUOTA_UG_PROPORTIONAL = 700  # paper: UG 700, proportional to clade size
UG_TAKE_WHOLE_BELOW = 30  # paper: UG clades of fewer than 30 clusters taken whole
RETRON_CONTROLS = 1  # paper: retron random 1,000 + 1 control
NOVEL_PER_CLADE = 60  # paper: novel 60/clade
NOVEL_CLADES = 29  # paper: x 29 clades
UNPLACED_LARGEST_LINEAGES = 440  # paper: 440 largest lineages
UNPLACED_SINGLETONS = 200  # paper: 200 random singletons

# paper: up to 3 loci per anchor from each source, 10 kb flanks
LOCUS_SOURCES: tuple[str, ...] = ("Logan", "ENA", "JGI", "NCBI")
MAX_LOCI_PER_ANCHOR_PER_SOURCE = 3
FLANK_BP = 10_000

# NOT-IN-PAPER: the paper states no sampling seed; fixed for determinism.
DEFAULT_SEED = 1


@dataclass(frozen=True)
class Anchor:
    rt_id: str
    rt_class: str
    clade: str = ""
    is_control: bool = False


@dataclass(frozen=True)
class Locus:
    source: str  # one of LOCUS_SOURCES
    contig: str
    start: int
    end: int


@dataclass
class ClassPool:
    """Available anchors for one RT class."""

    members: list[Anchor] = field(default_factory=list)
    clades: dict[str, list[Anchor]] = field(default_factory=dict)
    singletons: list[Anchor] = field(default_factory=list)
    controls: list[Anchor] = field(default_factory=list)


def sample_exhaustive(members: Sequence[Anchor]) -> list[Anchor]:
    """paper: Abi (680) and group II-like (827) sampled exhaustively."""
    return list(members)


def sample_random(members: Sequence[Anchor], n: int, rng: random.Random) -> list[Anchor]:
    """Uniform sample of up to n anchors (paper: random quotas above)."""
    return rng.sample(list(members), min(n, len(members)))


def sample_proportional(
    clades: Mapping[str, Sequence[Anchor]],
    total: int,
    rng: random.Random,
    take_whole_below: int = UG_TAKE_WHOLE_BELOW,
) -> list[Anchor]:
    """paper: UG 700 proportional to clade size; clades of fewer than 30
    clusters taken whole (small clades are added in full before the remaining
    quota is split proportionally over the rest).

    NOT-IN-PAPER: largest-remainder allocation, then uniform sampling inside
    each clade; the paper does not give the allocation rule.
    """
    small = [a for k, v in clades.items() if len(v) < take_whole_below for a in v]
    big = {k: v for k, v in clades.items() if len(v) >= take_whole_below}
    out = list(small)
    remaining = total - len(out)
    sizes = {k: len(v) for k, v in big.items()}
    pool = sum(sizes.values())
    if pool == 0 or remaining <= 0:
        return out
    exact = {k: remaining * n / pool for k, n in sizes.items()}
    quota = {k: int(v) for k, v in exact.items()}
    remainder = remaining - sum(quota.values())
    by_frac = sorted(exact, key=lambda k: exact[k] - quota[k], reverse=True)
    for k in by_frac[:remainder]:
        quota[k] += 1
    for clade, n in quota.items():
        out.extend(rng.sample(list(big[clade]), min(n, len(big[clade]))))
    return out


def sample_per_clade(
    clades: Mapping[str, Sequence[Anchor]], per_clade: int, rng: random.Random
) -> list[Anchor]:
    """paper: novel 60 anchors per clade (29 clades)."""
    out: list[Anchor] = []
    for members in clades.values():
        out.extend(rng.sample(list(members), min(per_clade, len(members))))
    return out


def sample_largest_lineages(
    lineages: Mapping[str, Sequence[Anchor]], n: int, rng: random.Random
) -> list[Anchor]:
    """paper: unplaced 440 largest lineages (one anchor per lineage).

    GAP: the paper does not say how the anchor within a lineage is chosen;
    sampled uniformly here.
    """
    ordered = sorted(lineages.values(), key=len, reverse=True)
    return [rng.choice(list(members)) for members in ordered[:n]]


def plan_anchors(pools: Mapping[str, ClassPool], rng: random.Random) -> dict[str, list[Anchor]]:
    """Apply the paper's per-class anchor quotas to the available pools."""
    selected: dict[str, list[Anchor]] = {}
    for cls, n in QUOTA_EXHAUSTIVE.items():
        selected[cls] = sample_exhaustive(pools.get(cls, ClassPool()).members[:n])
    for cls, n in QUOTA_RANDOM.items():
        selected[cls] = sample_random(pools.get(cls, ClassPool()).members, n, rng)
    selected["retron"] = list(selected["retron"]) + pools.get(
        "retron", ClassPool()
    ).controls[:RETRON_CONTROLS]
    selected["UG"] = sample_proportional(
        pools.get("UG", ClassPool()).clades, QUOTA_UG_PROPORTIONAL, rng
    )
    selected["novel"] = sample_per_clade(
        pools.get("novel", ClassPool()).clades, NOVEL_PER_CLADE, rng
    )
    unplaced = pools.get("unplaced", ClassPool())
    selected["unplaced"] = sample_largest_lineages(
        unplaced.clades, UNPLACED_LARGEST_LINEAGES, rng
    ) + sample_random(unplaced.singletons, UNPLACED_SINGLETONS, rng)
    return selected


def locus_window(locus: Locus, flank: int = FLANK_BP) -> tuple[int, int]:
    """paper: neighborhood = locus +/- 10 kb flanks (clamped at 0)."""
    return max(0, locus.start - flank), locus.end + flank


def plan() -> str:
    quota_sum = (
        sum(QUOTA_EXHAUSTIVE.values())
        + sum(QUOTA_RANDOM.values())
        + RETRON_CONTROLS
        + QUOTA_UG_PROPORTIONAL
        + NOVEL_PER_CLADE * NOVEL_CLADES
        + UNPLACED_LARGEST_LINEAGES
        + UNPLACED_SINGLETONS
    )
    lines = [
        "census step 05 -- anchor sampling and neighborhood extraction (dry-run plan)",
        "  anchor quotas (paper):",
        f"    Abi {QUOTA_EXHAUSTIVE['Abi']} exhaustive; "
        f"group II-like {QUOTA_EXHAUSTIVE['group II-like']} exhaustive",
        f"    DGR {QUOTA_RANDOM['DGR']} random; "
        f"CRISPR-assoc {QUOTA_RANDOM['CRISPR-assoc']} random",
        f"    UG {QUOTA_UG_PROPORTIONAL} proportional to clade size"
        f" (clades < {UG_TAKE_WHOLE_BELOW} clusters taken whole)",
        f"    retron {QUOTA_RANDOM['retron']} random + {RETRON_CONTROLS} control",
        f"    group II intron {QUOTA_RANDOM['group II intron']} random",
        f"    novel {NOVEL_PER_CLADE}/clade x {NOVEL_CLADES} clades",
        f"    unplaced {UNPLACED_LARGEST_LINEAGES} largest lineages "
        f"+ {UNPLACED_SINGLETONS} random singletons",
        f"  reported total: {TOTAL_ANCHORS:,} anchors"
        f" (GAP: stated quotas sum to {quota_sum:,})",
        f"  neighborhoods: up to {MAX_LOCI_PER_ANCHOR_PER_SOURCE} loci per anchor"
        f" from each of {'/'.join(LOCUS_SOURCES)}, {FLANK_BP // 1000} kb flanks",
    ]
    return "\n".join(lines)


def load_anchor_tsv(path: str | Path) -> dict[str, ClassPool]:
    """Read anchors TSV: rt_id, rt_class, clade, kind(member|control|singleton).

    NOT-IN-PAPER: TSV plumbing; the paper fixes quotas, not file formats.
    """
    pools: dict[str, ClassPool] = defaultdict(ClassPool)
    with Path(path).open() as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if not row or row[0].startswith("#") or len(row) < 4:
                continue
            anchor = Anchor(rt_id=row[0], rt_class=row[1], clade=row[2])
            pool = pools[anchor.rt_class]
            kind = row[3]
            if kind == "control":
                pool.controls.append(
                    Anchor(anchor.rt_id, anchor.rt_class, anchor.clade, is_control=True)
                )
            elif kind == "singleton":
                pool.singletons.append(anchor)
            else:
                pool.members.append(anchor)
            if anchor.clade:
                pool.clades.setdefault(anchor.clade, []).append(anchor)
    return dict(pools)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("anchors", nargs="?",
                    help="TSV: rt_id, rt_class, clade, kind(member|control|singleton)")
    ap.add_argument("--out", help="selected anchors TSV (default stdout)")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED,
                    help=f"sampling seed (default {DEFAULT_SEED}; NOT-IN-PAPER)")
    ap.add_argument("--dry-run", action="store_true", help="print the step plan and exit")
    args = ap.parse_args(argv)

    if args.dry_run:
        print(plan())
        return 0
    if not args.anchors:
        ap.error("anchors TSV is required unless --dry-run")

    rng = random.Random(args.seed)
    pools = load_anchor_tsv(args.anchors)
    selected = plan_anchors(pools, rng)

    out = Path(args.out).open("w") if args.out else sys.stdout
    total = 0
    try:
        for cls in sorted(selected):
            for anchor in selected[cls]:
                total += 1
                flag = "\tcontrol" if anchor.is_control else ""
                out.write(f"{anchor.rt_id}\t{cls}\t{anchor.clade}{flag}\n")
    finally:
        if args.out:
            out.close()
    print(f"selected {total} anchors (paper: {TOTAL_ANCHORS:,})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
