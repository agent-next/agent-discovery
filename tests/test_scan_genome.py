import importlib.util
import random
from pathlib import Path


def _load():
    spec = importlib.util.spec_from_file_location(
        "scan_genome", Path(__file__).parent.parent / "scripts" / "scan_genome.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


REPEAT = "CATGTGTATCGCATGT"


def _planted_genome(rng: random.Random) -> str:
    parts = []
    for _ in range(14):
        seq = list(REPEAT)
        for pos in rng.sample(range(len(REPEAT)), 1):
            seq[pos] = rng.choice([b for b in "ACGT" if b != seq[pos]])
        parts.append("".join(seq))
        parts.append("".join(rng.choice("ACGT") for _ in range(120)))
    flank = "".join(rng.choice("ATGC") for _ in range(500))
    return flank + "".join(parts) + flank


def test_scan_genome_reads_fasta(tmp_path: Path):
    mod = _load()
    genome = _planted_genome(random.Random(5))
    fasta = tmp_path / "g.fna"
    fasta.write_text(f">testgen\n{genome}\n")
    name, seq = mod.read_fasta(fasta)
    assert name == "testgen" and len(seq) == len(genome)


def test_scan_genome_finds_planted_array():
    mod = _load()
    rng = random.Random(5)
    genome = _planted_genome(rng)
    hits = mod.scan_genome("testgen", genome, random.Random(0))
    assert hits, "planted array must produce a hit"
    planted = (500, 500 + 14 * (16 + 120))
    assert any(h["start"] < planted[1] and planted[0] < h["end"] and h["R"] >= 4
               for h in hits)
