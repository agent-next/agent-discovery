"""S2 regression tests for pipeline/db/build_subset.sh (S1 findings B3, C3).

Power: the pre-fix tantan lookup keyed the mask dict on the FULL header while
querying with the first token, so the low-complexity filter never fired; the
pre-fix --inputs fallback silently fabricated synthetic benchmark fixtures.
Both tests fail on the pre-fix code.
"""

import re
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "pipeline" / "db" / "build_subset.sh"


def _apply_filters_python() -> str:
    """Extract the python program embedded in apply_filters' heredoc."""
    text = SCRIPT.read_text()
    m = re.search(r"apply_filters\(\) \{\s*python3 - \"\$1\" \"\$2\" \"\$3\" <<'PY'\n(.*?)\nPY\n\}",
                  text, re.DOTALL)
    assert m, "apply_filters heredoc not found"
    return m.group(1)


def _run_filters(proteins: str, masks: str, tmp_path: Path) -> str:
    src = tmp_path / "proteins.faa"
    mask = tmp_path / "tantan.faa"
    out = tmp_path / "filtered.faa"
    src.write_text(proteins)
    mask.write_text(masks)
    subprocess.run(["python3", "-c", _apply_filters_python(), str(src), str(mask),
                    str(out)], check=True)
    return out.read_text()


def test_low_complexity_filter_fires_when_tantan_masks_match(tmp_path: Path):
    lowc = "msmsms" * 40  # masked (lowercase) low-complexity, 240 aa, >=50%
    good = "MKTAYIAKQRQISFVKSHFSRQ" * 4
    proteins = (f">seq1 partial=00 start=1 end=240\n{lowc}\n"
                f">seq2 partial=00 start=1 end=92\n{good}\n")
    masks = (f">seq1 partial=00 start=1 end=240\n{lowc}\n"
             f">seq2 partial=00 start=1 end=92\n{good}\n")
    out = _run_filters(proteins, masks, tmp_path)
    assert "seq1" not in out, ">=50% masked sequence must be dropped"
    assert "seq2" in out


def test_exact_duplicates_are_deduplicated(tmp_path: Path):
    # paper: "Proteins were deduplicated" — the old filter chain kept both
    good = "MKTAYIAKQRQISFVKSHFSRQ" * 4
    proteins = (f">dup1 partial=00\n{good}\n"
                f">dup2 partial=00\n{good}\n")
    masks = f">x\n{good}\n"
    out = _run_filters(proteins, masks, tmp_path)
    assert out.count(">dup") == 1, out


def test_run_benchmark_refuses_missing_inputs_without_opt_in(tmp_path: Path):
    import pytest
    from benchmark.run_benchmark import run_benchmark

    def boom(spec):
        raise AssertionError("backend must not run")

    with pytest.raises(FileNotFoundError, match="synthetic"):
        run_benchmark(models=["m"], levels=["L1"], attempts=1,
                      outdir=tmp_path, backend=boom,
                      inputs_dir=tmp_path / "absent")
    # explicit opt-in fabricates the fixtures and proceeds to run
    recs = run_benchmark(models=["m"], levels=["L1"], attempts=1,
                         outdir=tmp_path / "ok", backend=lambda spec: {
                             "report": "r",
                             "submission": {"findings": []}},
                         inputs_dir=tmp_path / "absent", allow_synthetic=True)
    assert recs and recs[0]["status"] == "ok"
