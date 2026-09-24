"""Benchmark environments L1-L5 (paper Methods "Fixed-input benchmark" p.38).

- L1: prompt carries the 2 RT protein sequences inline; no tools, no env files.
- L2: prompt carries the two corresponding loci as text; no tools.
- L3: no sequence in the prompt; all 96 loci as files in an offline env; tools =
  gene calling, HMMER, BLAST+, MMseqs2, MAFFT, FastTree, ViennaRNA, Python.
- L4 = L3 + predicted structure for every ORF, Foldseek with a local reference
  structure DB, PyMOL, US-align.
- L5 = L4 + literature search, web access, software installation.

Inputs (paper): 96 ART loci of 1,093-26,554 bp with anonymized identifiers,
gene calls, Pfam matches, 1,131 predicted protein structures.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

LEVELS = ("L1", "L2", "L3", "L4", "L5")

# Verbatim task statement — paper Methods "Fixed-input benchmark" p.38
# (canonical text also in task_statement.md).
TASK_STATEMENT = (
    "characterize the RT and predict its function: report every feature you "
    "judge important, the evidence for it, how confident you are, and what "
    "experiment would test your main prediction."
)

# Faithful paraphrase of the surrounding task spec (marked as such in
# task_statement.md — the paper does not give the full prompt verbatim).
_TASK_CONTEXT = (
    "The loci were drawn from a large sequence collection because each encodes "
    "a member of one related group of RTs; nothing else is known about them. "
    "End with a report and a structured submission of findings; each finding is "
    "{claim, evidence, confidence} with confidence in [0, 1]."
)

# Tool inventory per level — paper Methods "Fixed-input benchmark" p.38.
_L3_TOOLS = ["gene calling", "HMMER", "BLAST+", "MMseqs2", "MAFFT", "FastTree",
             "ViennaRNA", "Python"]
_L4_EXTRA = ["Foldseek", "PyMOL", "US-align"]  # Foldseek: local reference structure DB
_L5_EXTRA = ["literature search"]  # plus web_access / software_install flags


@dataclass
class Environment:
    level: str
    prompt: str  # task statement + context + any inline sequences
    tools: list[str]
    workdir: Path  # materialized input dir (empty for L1/L2)
    files: list[Path] = field(default_factory=list)
    web_access: bool = False
    software_install: bool = False


def _env_files(inputs_dir: Path, include_structures: bool) -> list[Path]:
    if not inputs_dir.exists():
        return []
    files = [p for p in sorted(inputs_dir.rglob("*")) if p.is_file()]
    if not include_structures:
        files = [p for p in files if "structures" not in p.parts]
    return files


def _inline(inputs_dir: Path, subdir: str, pattern: str, n: int = 2) -> str:
    """Inline the first ``n`` files as text.

    NOT-IN-PAPER: which two of the 96 loci the paper inlined at L1/L2 is not
    stated; we take the first two fixtures in sorted order.
    """
    files = sorted((inputs_dir / subdir).glob(pattern))
    if len(files) < n:
        return "<synthetic placeholder sequences — run write_synthetic_inputs()>"
    return "\n".join(f.read_text().strip() for f in files[:n])


def build_environment(level: str, inputs_dir: Path,
                      workdir: Path | None = None) -> Environment:
    """Materialize the level's prompt/tools/files view over ``inputs_dir``."""
    inputs_dir = Path(inputs_dir)
    workdir = Path(workdir) if workdir is not None else inputs_dir
    if level == "L1":
        prompt = (f"{TASK_STATEMENT}\n\n{_TASK_CONTEXT}\n\n"
                  f"RT protein sequences:\n{_inline(inputs_dir, 'proteins', '*.faa')}")
        return Environment(level=level, prompt=prompt, tools=[], workdir=workdir)
    if level == "L2":
        prompt = (f"{TASK_STATEMENT}\n\n{_TASK_CONTEXT}\n\n"
                  f"Loci:\n{_inline(inputs_dir, 'loci', '*.fasta')}")
        return Environment(level=level, prompt=prompt, tools=[], workdir=workdir)
    if level in ("L3", "L4", "L5"):
        include_structures = level != "L3"
        tools = list(_L3_TOOLS)
        prompt = f"{TASK_STATEMENT}\n\n{_TASK_CONTEXT}\n\nInput files: loci/, gene_calls.tsv, pfam_matches.tsv"
        if level in ("L4", "L5"):
            tools += _L4_EXTRA
            prompt += ", structures/ (predicted structure per ORF; Foldseek local reference DB)"
        if level == "L5":
            tools += _L5_EXTRA
        return Environment(
            level=level,
            prompt=prompt,
            tools=tools,
            workdir=workdir,
            files=_env_files(inputs_dir, include_structures),
            web_access=level == "L5",
            software_install=level == "L5",
        )
    raise ValueError(f"unknown level {level!r}; expected one of {LEVELS}")


def write_synthetic_inputs(inputs_dir: Path, n_loci: int = 96,
                           seed: int = 0) -> Path:
    """Write small synthetic fixtures so tests and demo runs work offline.

    NOT-IN-PAPER / synthetic: keeps only the file *shape* of the paper inputs
    (96 loci, gene calls, Pfam matches, predicted structures) — tiny sequences,
    one ORF per locus instead of the paper's 1,131 structures, no real biology.
    """
    inputs_dir = Path(inputs_dir)
    loci_dir = inputs_dir / "loci"
    prot_dir = inputs_dir / "proteins"
    struct_dir = inputs_dir / "structures"
    for d in (loci_dir, prot_dir, struct_dir):
        d.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    gene_rows = ["locus\torf\tstart\tend\tstrand"]
    pfam_rows = ["orf\tpfam_id\tpfam_name\tevalue"]
    for i in range(1, n_loci + 1):
        name = f"locus_{i:03d}"
        seq = "".join(rng.choice("ACGT") for _ in range(180))  # real: 1,093-26,554 bp
        prot = "".join(rng.choice("ACDEFGHIKLMNPQRSTVWY") for _ in range(60))
        (loci_dir / f"{name}.fasta").write_text(f">{name} synthetic\n{seq}\n")
        (prot_dir / f"{name}_orf1.faa").write_text(f">{name}_orf1 synthetic\n{prot}\n")
        (struct_dir / f"{name}_orf1.pdb").write_text(
            f"REMARK synthetic placeholder structure for {name}_orf1\nEND\n")
        gene_rows.append(f"{name}\t{name}_orf1\t1\t{len(seq)}\t+")
        pfam_rows.append(f"{name}_orf1\tPF00078\tRVT_1 synthetic\t1e-20")
    (inputs_dir / "gene_calls.tsv").write_text("\n".join(gene_rows) + "\n")
    (inputs_dir / "pfam_matches.tsv").write_text("\n".join(pfam_rows) + "\n")
    return inputs_dir
