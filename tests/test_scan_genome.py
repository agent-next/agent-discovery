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
    records = mod.read_fasta(fasta)
    assert len(records) == 1 and records[0][0] == "testgen"
    assert len(records[0][1]) == len(genome)


def test_read_fasta_keeps_multi_record_files_separate(tmp_path: Path):
    # S1 finding C7: the old reader concatenated records into one chimeric
    # sequence under the LAST header -- coordinates stopped being contig-relative
    mod = _load()
    fasta = tmp_path / "two.fna"
    fasta.write_text(">c1\nACGTACGTAC\n>c2\nTTTTGGGGCC\n")
    records = mod.read_fasta(fasta)
    assert [("c1", "ACGTACGTAC"), ("c2", "TTTTGGGGCC")] == records


def test_main_scans_each_record_of_a_multi_contig_file(tmp_path: Path,
                                                       capsys):
    # a planted array in contig 2 must still be found (the chimeric merge would
    # shift its coordinates into a nonexistent composite sequence)
    mod = _load()
    rng = random.Random(5)
    genome = _planted_genome(rng)
    fasta = tmp_path / "g.fna"
    fasta.write_text(f">c1\n{'ACGT' * 50}\n>c2\n{genome}\n")
    mod.main([str(fasta)])
    out = capsys.readouterr().out
    assert "== c1" in out and "== c2" in out


def test_scan_genome_finds_planted_array():
    mod = _load()
    rng = random.Random(5)
    genome = _planted_genome(rng)
    hits = mod.scan_genome("testgen", genome, random.Random(0))
    assert hits, "planted array must produce a hit"
    planted = (500, 500 + 14 * (16 + 120))
    assert any(h["start"] < planted[1] and planted[0] < h["end"] and h["R"] >= 4
               for h in hits)


def test_scan_genome_suppression_is_window_local():
    # grok round-4 probe: 6 short-spaced (30 nt) copies at 0..150 must NOT
    # suppress a regular 4-copy run at 4000..4420 — kmer_scan calls it
    mod = _load()
    rng = random.Random(0)
    word = "ACGTACGTTGCAAT"
    parts = []
    for _i in range(6):  # short-spaced run
        parts.append(word)
        parts.append("".join(rng.choice("ACGT") for _ in range(16)))
    parts.append("".join(rng.choice("ACGT") for _ in range(3850)))
    for _ in range(4):  # regular run at ~4000
        parts.append(word)
        parts.append("".join(rng.choice("ACGT") for _ in range(126)))
    parts.append("".join(rng.choice("AT") for _ in range(500)))  # poly-AT tail
    genome = "".join(parts)
    hits = mod.scan_genome("t", genome, random.Random(1))
    regular = [h for h in hits if h["R"] == 4]
    assert regular, f"expected the regular R=4 run to survive suppression: {hits}"
