"""Tests for artharness.connectors.protein_db — SQLite subset + MMseqs2 wrapper."""

import pytest

from artharness.connectors.protein_db import MMseqs2Search, ProteinDB


def _db():
    db = ProteinDB(":memory:")
    db.insert_biosample("bs1", "SRA", metadata='{"site": "soil"}')
    db.insert_contig("c1", "SRA", biosample_id="bs1", length=100_000)
    db.insert_contig("c2", "SRA", biosample_id="bs1", length=50_000)
    db.insert_cluster("cl1", "p1", size=3)
    db.insert_cluster("cl2", "p4", size=1)
    # contig c1: p1 (anchor) 1000-2000, p2 2500-3000 nearby, p3 8000-9000 far
    db.insert_protein("p1", cluster_id="cl1", contig_id="c1", start=1000,
                      end=2000, strand="+", length=1000, sequence="M" * 10)
    db.insert_protein("p2", cluster_id="cl1", contig_id="c1", start=2500,
                      end=3000, strand="-", length=500)
    db.insert_protein("p3", cluster_id="cl1", contig_id="c1", start=8000,
                      end=9000, strand="+", length=1000)
    # contig c2: p4 overlaps p1's coordinates but on a different contig
    db.insert_protein("p4", cluster_id="cl2", contig_id="c2", start=1000,
                      end=2000, strand="+", length=1000)
    db.insert_pfam("p1", "PF00078", bitscore=250.0, coverage=0.95)
    db.insert_pfam("p2", "PF00078", bitscore=100.0, coverage=0.50)
    return db


def test_schema_roundtrip():
    db = _db()
    n = db.conn.execute("SELECT COUNT(*) AS n FROM proteins").fetchone()
    assert n["n"] == 4
    p1 = db.conn.execute(
        "SELECT * FROM proteins WHERE protein_id = 'p1'").fetchone()
    assert p1["contig_id"] == "c1"
    assert p1["start"] == 1000 and p1["end"] == 2000
    assert p1["strand"] == "+"
    assert p1["sequence"] == "M" * 10
    bs = db.conn.execute(
        "SELECT * FROM biosamples WHERE biosample_id = 'bs1'").fetchone()
    assert bs["source"] == "SRA"
    assert bs["metadata"] == '{"site": "soil"}'
    pf = db.conn.execute(
        "SELECT * FROM pfam WHERE protein_id = 'p1'").fetchone()
    assert pf["pfam_id"] == "PF00078"
    assert pf["bitscore"] == 250.0
    db.close()


def test_neighbors_window_excludes_self_and_out_of_window():
    db = _db()
    ids = [r["protein_id"] for r in db.neighbors("p1", flank_bp=1000)]
    # p3 is out of window, p4 is on another contig, p1 (self) excluded
    assert ids == ["p2"]


def test_neighbors_unknown_protein_raises():
    db = _db()
    with pytest.raises(KeyError):
        db.neighbors("nope", flank_bp=100)


def test_cluster_members():
    db = _db()
    ids = [r["protein_id"] for r in db.cluster_members("cl1")]
    assert ids == ["p1", "p2", "p3"]
    assert db.cluster_members("cl-empty") == []


def test_proteins_beside_anchors_on_pfam():
    db = _db()
    rows = db.proteins_beside("PF00078", flank_bp=1000)
    # anchors p1 + p2 included; p3 out of both windows; p4 on another contig
    assert [r["protein_id"] for r in rows] == ["p1", "p2"]


def test_mmseqs2_build_command_both_modes():
    # default omits --min-seq-id: the paper's only quoted SEARCH threshold is
    # E <= 0.001; the old 0.9 default discarded remote homologs (S1 C9)
    for mode, target in (("representatives", "/db/reps"),
                         ("reference365m", "/db/ref365m")):
        s = MMseqs2Search(mode=mode, db_paths={mode: target})
        cmd = s.build_command("query.fasta")
        assert cmd == ["mmseqs", "easy-search", "query.fasta", target,
                       "resultDB", "tmp"]
        assert not any("min-seq-id" in c for c in cmd)


def test_mmseqs2_min_seq_id_is_opt_in():
    s = MMseqs2Search(mode="representatives", db_paths={"representatives": "/db/reps"},
                      min_seq_id=0.5)
    cmd = s.build_command("query.fasta")
    assert cmd[-2:] == ["--min-seq-id", "0.5"]


def test_mmseqs2_run_requires_execute_flag():
    s = MMseqs2Search(mode="representatives",
                      db_paths={"representatives": "/db/reps"})
    with pytest.raises(RuntimeError):
        s.run("query.fasta")


def test_mmseqs2_bad_mode_raises():
    with pytest.raises(ValueError):
        MMseqs2Search(mode="bogus")
