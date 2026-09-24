import importlib.util
import json
from pathlib import Path


def _load():
    spec = importlib.util.spec_from_file_location(
        "forensics", Path(__file__).parent.parent / "experiments" / "forensics.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_scan_records_finds_identifier(tmp_path: Path):
    mod = _load()
    (tmp_path / "records" / "t0001").mkdir(parents=True)
    (tmp_path / "records" / "t0001" / "summary.md").write_text(
        "examined contig L0050 from Logan; nothing unusual.")
    (tmp_path / "records" / "t0002").mkdir()
    (tmp_path / "records" / "t0002" / "summary.md").write_text("no relevant hits here.")
    ids = tmp_path / "ids.txt"
    ids.write_text("L0050\nMW218148.1\n")
    hits = mod.scan_records(tmp_path / "records", mod.load_identifiers(ids))
    assert hits == {"t0001": ["L0050"]}


def test_scan_transcripts_counts_dna_and_remarks(tmp_path: Path):
    mod = _load()
    dna = "ACGT" * 60  # 240 nt contiguous run (>= paper's 200-nt threshold)
    (tmp_path / "sessions").mkdir()
    tr = tmp_path / "sessions" / "s1.log"
    tr.write_text(f"retrieved flank of L0050: {dna}\n"
                  "I can see by eye a tandem repeat array!\n"
                  "weather in SF is nice\n")
    ids = tmp_path / "ids.txt"
    ids.write_text("L0050\n")
    out = mod.scan_transcripts(tmp_path / "sessions", mod.load_identifiers(ids))
    assert len(out) == 1
    assert out[0]["dna_runs_ge200nt"] == 1
    assert out[0]["repeat_remarks"] == 1
    assert "tandem repeat" in out[0]["repeat_remark_samples"][0]


def test_short_dna_not_counted(tmp_path: Path):
    mod = _load()
    tr = tmp_path / "s2.log"
    tr.write_text("L0050 flank: ACGT" * 10)  # only 40-nt runs
    ids = tmp_path / "ids.txt"
    ids.write_text("L0050\n")
    out = mod.scan_transcripts(tmp_path / ".", mod.load_identifiers(ids))
    assert out[0]["dna_runs_ge200nt"] == 0


def test_cli_end_to_end(tmp_path: Path):
    mod = _load()
    (tmp_path / "records" / "t0001").mkdir(parents=True)
    (tmp_path / "records" / "t0001" / "summary.md").write_text("hit MW248466.1 here")
    ids = tmp_path / "ids.txt"
    ids.write_text("MW248466.1\n")
    outp = tmp_path / "findings.json"
    import sys

    sys.argv = ["forensics.py", "--records", str(tmp_path / "records"),
                "--identifiers", str(ids), "--out", str(outp)]
    mod.main()
    data = json.loads(outp.read_text())
    assert data["record_hits"] == {"t0001": ["MW248466.1"]}
    assert data["identifiers_searched"] == 1
