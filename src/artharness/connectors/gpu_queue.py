"""GPU queue connector — structure-prediction job dispatch.

Paper (Methods "Autonomous research harness" p.28): sessions dispatched
structure predictions to a GPU job queue — 19 jobs ran in the campaign. Model
settings used here trace to the paper: ESMFold ``esmfold_v1``; ColabFold 1.6.1
``alphafold2_ptm`` with 5 models and 3 recycles; A100 and L4 GPU targets.

Offline-first: :class:`StubQueue` records submissions in memory and never calls
a GPU. :func:`dispatch` and :func:`run_worker` raise ``NotImplementedError``
unless the owner gate ``ARTHARNESS_ALLOW_LIVE=1`` is set
(``config.live_backend_env``).
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from ..config import CampaignConfig

# paper: esmfold_v1, alphafold2_ptm, 5 models 3 recycles
ESMFOLD_MODEL = "esmfold_v1"
COLABFOLD_MODEL = "alphafold2_ptm"  # ColabFold 1.6.1
COLABFOLD_NUM_MODELS = 5
COLABFOLD_NUM_RECYCLES = 3
GPU_TARGETS = ("a100", "l4")  # paper: A100 / L4

Method = Literal["esmfold", "colabfold"]

_LIVE_ENV = CampaignConfig().live_backend_env


def _live_allowed() -> bool:
    return os.environ.get(_LIVE_ENV) == "1"


@dataclass
class GpuJob:
    job_id: str
    sequences: list[str] | Path  # in-memory sequences or a FASTA path
    method: Method = "esmfold"
    hardware: str = "a100"  # paper targets: "a100" | "l4"
    status: str = "queued"  # queued | running | done | failed
    result_path: Path | None = None  # PDB/mmCIF output dir once a worker finishes


class GpuQueue(Protocol):
    """Anything that can accept, track and yield structure-prediction jobs."""

    def submit(self, job: GpuJob) -> str: ...

    def status(self, job_id: str) -> str: ...

    def collect(self, job_id: str) -> Path: ...


class StubQueue:
    """In-memory queue: records submissions, reports ``queued``, never runs.

    ``collect`` returns the directory under ``workdir`` where a real worker
    would drop PDB/mmCIF results; the stub creates nothing.
    """

    def __init__(self, workdir: Path):
        self.workdir = Path(workdir)
        self.jobs: dict[str, GpuJob] = {}

    def submit(self, job: GpuJob) -> str:
        job.status = "queued"
        self.jobs[job.job_id] = job
        return job.job_id

    def status(self, job_id: str) -> str:
        return self.jobs[job_id].status

    def collect(self, job_id: str) -> Path:
        if job_id not in self.jobs:
            raise KeyError(f"unknown job_id: {job_id}")
        return self.workdir / job_id


def dispatch(queue: GpuQueue, jobs: Iterable[GpuJob]) -> list[str]:
    """Submit a batch through ``queue``. Live dispatch is owner-gated; the
    offline path is ``StubQueue.submit`` called directly."""
    if not _live_allowed():
        raise NotImplementedError(
            f"GPU dispatch is owner-gated: set {_LIVE_ENV}=1 for live runs "
            "(README Safety gates); offline path: StubQueue.submit()"
        )
    return [queue.submit(j) for j in jobs]


def run_worker(queue: GpuQueue) -> None:
    """Placeholder for a real GPU worker pulling jobs off ``queue``.

    GAP: the paper does not describe the worker implementation; nothing here
    runs predictions even when the live gate is open.
    """
    if not _live_allowed():
        raise NotImplementedError(
            f"GPU worker is owner-gated: set {_LIVE_ENV}=1 for live runs "
            "(README Safety gates)"
        )
    raise NotImplementedError("no live GPU worker implemented (GAP)")
