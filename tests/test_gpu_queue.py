"""Tests for artharness.connectors.gpu_queue — owner-gated GPU dispatch."""

import pytest

from artharness.connectors.gpu_queue import (
    COLABFOLD_MODEL,
    COLABFOLD_NUM_MODELS,
    COLABFOLD_NUM_RECYCLES,
    ESMFOLD_MODEL,
    GpuJob,
    StubQueue,
    dispatch,
    run_worker,
)

LIVE_ENV = "ARTHARNESS_ALLOW_LIVE"


def test_gpujob_defaults():
    job = GpuJob(job_id="j1", sequences=["MKT"])
    assert job.method == "esmfold"
    assert job.hardware == "a100"
    assert job.status == "queued"
    assert job.result_path is None


def test_model_constants():
    assert ESMFOLD_MODEL == "esmfold_v1"
    assert COLABFOLD_MODEL == "alphafold2_ptm"
    assert COLABFOLD_NUM_MODELS == 5
    assert COLABFOLD_NUM_RECYCLES == 3


def test_stub_queue_submit_status_collect(tmp_path):
    q = StubQueue(tmp_path)
    jid = q.submit(GpuJob(job_id="j1", sequences=["MKT"], method="colabfold"))
    assert jid == "j1"
    assert q.status("j1") == "queued"
    assert q.collect("j1") == tmp_path / "j1"


def test_stub_queue_collect_unknown_raises(tmp_path):
    q = StubQueue(tmp_path)
    with pytest.raises(KeyError):
        q.collect("missing")


def test_dispatch_and_worker_gated(monkeypatch, tmp_path):
    monkeypatch.delenv(LIVE_ENV, raising=False)
    q = StubQueue(tmp_path)
    with pytest.raises(NotImplementedError):
        dispatch(q, [GpuJob(job_id="j1", sequences=["A"])])
    with pytest.raises(NotImplementedError):
        run_worker(q)


def test_dispatch_through_stub_when_gated(monkeypatch, tmp_path):
    monkeypatch.setenv(LIVE_ENV, "1")
    q = StubQueue(tmp_path)
    jobs = [GpuJob(job_id="a", sequences=["AA"]),
            GpuJob(job_id="b", sequences=["BB"])]
    ids = dispatch(q, jobs)
    assert ids == ["a", "b"]
    assert q.status("a") == "queued"
    assert q.status("b") == "queued"
    # GAP: the worker body raises even when the live gate is open
    with pytest.raises(NotImplementedError):
        run_worker(q)
