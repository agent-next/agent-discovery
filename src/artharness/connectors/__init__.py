"""Session connectors — offline-first adapters for the paper harness's tool layer.

Paper (Methods, p.28): each Claude Code session ran with connectors to

- a metagenomic protein database (the cluster subset behind the RT census),
- literature search,
- the shared knowledge base (see :mod:`artharness.knowledge`),
- a GPU queue for structure prediction.

Every connector here is offline-first: no network or GPU call happens unless a
live flag is passed (``live=True`` / ``execute=True``) or the owner gate
``ARTHARNESS_ALLOW_LIVE=1`` is set (``config.live_backend_env``). Tests replay
recorded fixtures through injected transports — no network required.
"""

from .gpu_queue import GpuJob, GpuQueue, StubQueue
from .literature import EuropePMCClient, PaperRef
from .protein_db import MMseqs2Search, ProteinDB

__all__ = [
    "EuropePMCClient",
    "GpuJob",
    "GpuQueue",
    "MMseqs2Search",
    "PaperRef",
    "ProteinDB",
    "StubQueue",
]
