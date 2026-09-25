"""Tests for benchmark/run_benchmark.py — offline attempt orchestration."""

import json

import pytest
from benchmark.run_benchmark import (
    default_backend,
    format_matrix,
    resolve_backend,
    run_benchmark,
)


def test_run_benchmark_end_to_end_offline(tmp_path):
    def stub(spec):
        return {
            "report": "# attempt report\n",
            "submission": {"findings": [{
                "claim": "nct-1",
                "evidence": "tandem repeat array in the 5-prime tract",
                "confidence": 0.9,
                "asserted": True,
            }]},
        }

    records = run_benchmark(models=["m"], levels=["L3"], attempts=1,
                            outdir=tmp_path, backend=stub, allow_synthetic=True)
    assert len(records) == 1
    run_dir = tmp_path / "runs" / "m" / "L3" / "attempt_001"
    assert (run_dir / "report.md").is_file()
    assert (run_dir / "submission.json").is_file()
    lines = (tmp_path / "results.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["model"] == "m"
    assert rec["level"] == "L3"
    assert rec["attempt"] == 1
    assert rec["score"] >= 1
    assert rec["recognized_repeat_array"] is True


def test_hedged_only_submission_scores_zero(tmp_path):
    def stub(spec):
        return {"report": "", "submission": {"findings": [{
            "claim": "nct-1", "evidence": "one possibility among several",
            "confidence": 0.4, "asserted": False}]}}

    records = run_benchmark(models=["m"], levels=["L3"], attempts=1,
                            outdir=tmp_path, backend=stub, allow_synthetic=True)
    assert records[0]["score"] == 0
    assert records[0]["recognized_repeat_array"] is False


def test_format_matrix_text():
    text = format_matrix(["m1", "m2"], ["L1", "L3"], 2)
    assert text == (
        "benchmark matrix: 2 models x 2 levels x 2 attempts = 8 total\n"
        "  m1 L1 x2\n"
        "  m1 L3 x2\n"
        "  m2 L1 x2\n"
        "  m2 L3 x2"
    )


def test_default_backend_requires_live_gate(monkeypatch):
    monkeypatch.delenv("ARTHARNESS_ALLOW_LIVE", raising=False)
    with pytest.raises(RuntimeError):
        default_backend("x")


def test_resolve_backend_rejects_non_dotted_path():
    with pytest.raises(ValueError):
        resolve_backend("no_dots_here")


def test_resolve_backend_loads_dotted_callable():
    assert resolve_backend("benchmark.run_benchmark.format_matrix") is format_matrix
