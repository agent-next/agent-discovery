from pathlib import Path

from artharness.accounting import SessionLedger, SessionResult


def test_paper_format_summary(tmp_path: Path):
    ledger = SessionLedger(tmp_path / "l.jsonl")
    # mimic the paper's session mix at 1/10 scale to check the accounting math
    rows = [("launch", 1), ("worker", 41), ("supervisor", 38), ("curator", 11),
            ("editor", 5)]
    for role, n in rows:
        for _i in range(n):
            ledger.record(SessionResult(role=role, task_id=None, duration_s=60.0,
                                        input_tokens_uncached=1000,
                                        output_tokens=1000, cache_write_tokens=1000))
    s = ledger.summary()
    assert s["sessions_total"] == 96
    assert s["sessions_by_role"]["worker"] == 41
    assert s["agent_hours_total"] == 1.6  # 96 min = 1.6 h
    assert s["tokens"]["input_uncached"] == 96_000
    assert s["tokens_total"] == 288_000


def test_empty_ledger(tmp_path: Path):
    s = SessionLedger(tmp_path / "none.jsonl").summary()
    assert s["sessions_total"] == 0 and s["tokens_total"] == 0
