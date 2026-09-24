"""Genome-wide driver for the paper's k-mer array scan (Methods p.32).

The paper runs the scan per-locus on the ≤3,000-nt window upstream of an RT. When RT
coordinates are not yet known (raw phage genomes), this driver finds candidate arrays
genome-wide with equivalent semantics:

1. count every 14-mer; seed candidates = the most frequent quality-gated words
   (>=3 distinct bases, no homopolymer >=6), floor count >=2 and top-MAX_SEEDS by
   frequency — the genome-wide analogue of the paper's per-window top-20 (a window
   top word can occur only twice when every copy carries a mismatch);
2. find non-overlapping copies (<=2 mismatches) genome-wide per seed;
3. keep runs of >=3 copies with regular spacing 100-450 nt (30% median tolerance);
4. for each candidate window (run +/- MAX_UPSTREAM_SCAN), run the full shuffle
   control as `artharness.arrays.kmer_scan` does, including its suppression rule
   (no call when a longer run of copies is spaced under 100 nt apart). Deviation
   vs the per-locus scan: null seeds here come from the reference window (the
   per-locus scan rediscovers seeds per shuffle).

USAGE: python3 scripts/scan_genome.py genome.fna [genome2.fna ...]
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from artharness.arrays import MIN_RUN, _copies_of, _regular_runs, _seed_ok, mononucleotide_shuffles

WORD = 14
MIN_COUNT_FOR_SEED = 2
MAX_SEEDS = 200
MIN_SPACING = 100  # paper: regular spacing is 100-450 nt, start to start


def arrays_min_spacing() -> int:
    from artharness.arrays import MIN_SPACING as _MS

    return _MS


def _runs_under(positions: list[int], max_gap: int) -> list[list[int]]:
    """Runs of consecutive copies spaced at most max_gap apart."""
    runs: list[list[int]] = []
    cur: list[int] = []
    for prev, nxt in zip(positions, positions[1:], strict=False):
        if nxt - prev <= max_gap:
            if not cur:
                cur = [prev]
            cur.append(nxt)
        else:
            if cur:
                runs.append(cur)
                cur = []
    if cur:
        runs.append(cur)
    return runs


def read_fasta(path: Path) -> tuple[str, str]:
    header = ""
    seq: list[str] = []
    for line in Path(path).read_text().splitlines():
        if line.startswith(">"):
            header = line[1:].split()[0]
        else:
            seq.append(line.strip().upper())
    return header, "".join(seq)


def scan_genome(name: str, seq: str, rng: random.Random) -> list[dict]:
    counts: dict[str, int] = {}
    for i in range(len(seq) - WORD + 1):
        w = seq[i:i + WORD]
        counts[w] = counts.get(w, 0) + 1
    seeds = [w for w, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
             if c >= MIN_COUNT_FOR_SEED and _seed_ok(w)][:MAX_SEEDS]
    hits: list[dict] = []
    for seed in seeds:
        positions = _copies_of(seq, seed, 2)
        if len(positions) < MIN_RUN:
            continue
        for run in _regular_runs(positions):
            # kmer_scan suppression rule: a LONGER run of copies spaced under
            # 100 nt apart suppresses the call (grok round-2: declared but the
            # helper was never wired)
            short_runs = [r2 for r2 in _runs_under(positions, MIN_SPACING - 1)
                          if len(r2) > len(run)]
            if short_runs:
                continue
            lo = max(0, run[0] - 3000)
            hi = min(len(seq), run[-1] + WORD + 3000)
            window = seq[lo:hi]
            # paper control: longest such run in 100 mononucleotide shuffles
            shuf_best = 0
            for shuf in mononucleotide_shuffles(window, 100, rng):
                sb = _copies_of(shuf, seed, 2)
                rr = _regular_runs(sb)
                shuf_best = max(shuf_best, max((len(r) for r in rr), default=0))
            if len(run) > shuf_best:
                hits.append({
                    "genome": name, "start": run[0], "end": run[-1] + WORD,
                    "R": len(run), "seed": seed,
                    "span_kb": round((run[-1] + WORD - run[0]) / 1000, 2),
                    "shuffle_max": shuf_best,
                })
    hits.sort(key=lambda h: -h["R"])
    # dedupe overlapping runs reported from different seeds of the same array
    deduped: list[dict] = []
    for h in hits:
        if not any(h["start"] < d["end"] and d["start"] < h["end"] for d in deduped):
            deduped.append(h)
    return deduped


def main(paths: list[str]) -> None:
    rng = random.Random(20260923)  # paper publication date as fixed seed
    for p in paths:
        name, seq = read_fasta(Path(p))
        hits = scan_genome(name, seq, rng)
        print(f"\n== {name} ({len(seq):,} nt): {len(hits)} array(s) pass shuffle control")
        for h in hits[:8]:
            print(f"  pos {h['start']:,}-{h['end']:,}  R={h['R']} copies  "
                  f"span={h['span_kb']} kb  seed={h['seed']}  shuffle_max={h['shuffle_max']}")


if __name__ == "__main__":
    main(sys.argv[1:])
