"""Tests for benchmark/levels.py — L1-L5 environment construction."""

import pytest
from benchmark.levels import (
    TASK_STATEMENT,
    Environment,
    build_environment,
    write_synthetic_inputs,
)


@pytest.fixture
def inputs_dir(tmp_path):
    return write_synthetic_inputs(tmp_path / "inputs")


def _loci(inputs_dir):
    return sorted((inputs_dir / "loci").glob("*.fasta"))


def test_write_synthetic_inputs_shape(tmp_path):
    inputs = write_synthetic_inputs(tmp_path / "inputs")
    assert len(_loci(inputs)) == 96
    assert (inputs / "gene_calls.tsv").is_file()
    assert (inputs / "pfam_matches.tsv").is_file()
    assert len(list((inputs / "proteins").glob("*.faa"))) == 96
    assert len(list((inputs / "structures").glob("*.pdb"))) == 96
    gene_lines = (inputs / "gene_calls.tsv").read_text().strip().splitlines()
    assert gene_lines[0] == "locus\torf\tstart\tend\tstrand"
    assert len(gene_lines) == 97  # header + 96 loci


def test_l1_inlines_two_protein_sequences_no_tools(inputs_dir):
    env = build_environment("L1", inputs_dir)
    assert isinstance(env, Environment)
    assert env.prompt.startswith(TASK_STATEMENT)
    proteins = sorted((inputs_dir / "proteins").glob("*.faa"))
    for f in proteins[:2]:
        assert f.read_text().strip() in env.prompt
    assert env.tools == []
    assert env.files == []
    assert env.web_access is False
    assert env.software_install is False


def test_l2_inlines_two_loci_no_tools(inputs_dir):
    env = build_environment("L2", inputs_dir)
    assert env.prompt.startswith(TASK_STATEMENT)
    for f in _loci(inputs_dir)[:2]:
        assert f.read_text().strip() in env.prompt
    assert env.tools == []
    assert env.files == []


def test_l3_files_without_inline_sequence(inputs_dir):
    env = build_environment("L3", inputs_dir)
    assert "Input files: loci/, gene_calls.tsv, pfam_matches.tsv" in env.prompt
    # No inline sequence: neither the first locus nor the first protein text.
    assert _loci(inputs_dir)[0].read_text().strip() not in env.prompt
    first_protein = sorted((inputs_dir / "proteins").glob("*.faa"))[0]
    assert first_protein.read_text().strip() not in env.prompt
    # Files: all 96 loci + gene/pfam tables present; structures/ excluded.
    files = set(env.files)
    assert set(_loci(inputs_dir)) <= files
    assert inputs_dir / "gene_calls.tsv" in files
    assert inputs_dir / "pfam_matches.tsv" in files
    assert not any("structures" in p.parts for p in env.files)
    assert env.tools == ["gene calling", "HMMER", "BLAST+", "MMseqs2", "MAFFT",
                         "FastTree", "ViennaRNA", "Python"]
    assert env.web_access is False
    assert env.software_install is False


def test_l4_adds_structures_and_structure_tools(inputs_dir):
    env = build_environment("L4", inputs_dir)
    assert any("structures" in p.parts for p in env.files)
    for tool in ("Foldseek", "PyMOL", "US-align"):
        assert tool in env.tools
    assert "MMseqs2" in env.tools  # L3 toolset retained
    assert env.web_access is False
    assert env.software_install is False


def test_l5_adds_literature_search_and_flags(inputs_dir):
    env = build_environment("L5", inputs_dir)
    assert "literature search" in env.tools
    assert "Foldseek" in env.tools
    assert env.web_access is True
    assert env.software_install is True


def test_unknown_level_raises(inputs_dir):
    with pytest.raises(ValueError):
        build_environment("L9", inputs_dir)
