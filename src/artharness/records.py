"""Git-backed task records: the harness's shared, version-controlled memory.

Paper (Methods, p.28): "Plans, results, reviews, and scripts were committed to a
version-controlled record readable by every agent."

Layout under the store root::

    records/t0001/brief.md      the task brief (written by stage chain or supervisor)
    records/t0001/plan.md       worker plan
    records/t0001/summary.md    worker written summary
    records/t0001/verdict.md    supervisor accept/revise decision + notes
    records/t0001/curated.md    curator knowledge entry for this task
    records/t0001/meta.json     status, lineage, counters
    records/t0001/artifacts/    code + data files the worker produced

Every transition commits to git (when git is available), so the record doubles as the
campaign's audit trail.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path


class TaskStatus(StrEnum):
    OPEN = "open"  # brief written, not yet dispatched
    PLANNED = "planned"  # worker wrote a plan
    EXECUTED = "executed"  # worker submitted summary + artifacts
    REVISING = "revising"  # supervisor returned it for revision
    ACCEPTED = "accepted"  # supervisor accepted the result
    CURATED = "curated"  # curator entered findings into the knowledge base
    COMPLETED = "completed"  # terminal, incl. reports after editor review
    REJECTED = "rejected"  # killed at triage with a written reason
    STALLED = "stalled"  # exceeded revision/gate limits


class TaskOrigin(StrEnum):
    SEED = "seed"  # seeded from a stage of the research brief (5 in the paper)
    DEEP_DIVE = "deep_dive"  # seeded from a promoted candidate family (16 in the paper)
    FOLLOW_UP = "follow_up"  # proposed by an agent during work (98 in the paper)
    REPORT = "report"  # writes or revises a report (22 in the paper)


@dataclass
class TaskRecord:
    task_id: str
    stage: str  # 1 input_assembly | 2 database_sweep | 3 rt_classification |
    # 4 neighborhood_census | 5 deep_dives | reports
    origin: TaskOrigin
    status: TaskStatus = TaskStatus.OPEN
    parent: str | None = None  # follow-up lineage parent
    revisions: int = 0
    gate_failures: int = 0
    label: str = ""  # short human-readable topic
    extra: dict = field(default_factory=dict)

    def to_meta(self) -> dict:
        d = asdict(self)
        d["origin"] = self.origin.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_meta(cls, d: dict) -> TaskRecord:
        d = dict(d)
        d["origin"] = TaskOrigin(d["origin"])
        d["status"] = TaskStatus(d["status"])
        return cls(**d)


class RecordStore:
    """Filesystem + git record store. Git commits are best-effort: tests run without git."""

    def __init__(self, root: Path, use_git: bool = True):
        self.root = Path(root)
        self.records = self.root / "records"
        self.records.mkdir(parents=True, exist_ok=True)
        self.use_git = use_git and self._inside_git_repo()

    def _inside_git_repo(self) -> bool:
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"], cwd=self.root, check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    # -- task lifecycle -------------------------------------------------
    def create(self, task_id: str, brief: str, stage: str, origin: TaskOrigin,
               parent: str | None = None, label: str = "") -> TaskRecord:
        rec_dir = self.records / task_id
        if rec_dir.exists():
            raise ValueError(f"task {task_id} already exists")
        (rec_dir / "artifacts").mkdir(parents=True)
        rec = TaskRecord(task_id=task_id, stage=stage, origin=origin, parent=parent,
                         label=label)
        self.write_text(task_id, "brief.md", brief)
        self._write_meta(rec)
        self.commit(f"task({task_id}): open {label} [{origin.value}]")
        return rec

    def get(self, task_id: str) -> TaskRecord:
        meta = self.records / task_id / "meta.json"
        return TaskRecord.from_meta(json.loads(meta.read_text()))

    def list_tasks(self) -> list[TaskRecord]:
        return [self.get(p.name) for p in sorted(self.records.iterdir()) if p.is_dir()]

    def update(self, rec: TaskRecord, message: str) -> None:
        self._write_meta(rec)
        self.commit(message)

    # -- text files ------------------------------------------------------
    def write_text(self, task_id: str, name: str, text: str) -> Path:
        path = self.records / task_id / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def read_text(self, task_id: str, name: str) -> str:
        return (self.records / task_id / name).read_text()

    def artifact_dir(self, task_id: str) -> Path:
        return self.records / task_id / "artifacts"

    # -- internals ---------------------------------------------------------
    def _write_meta(self, rec: TaskRecord) -> None:
        path = self.records / rec.task_id / "meta.json"
        path.write_text(json.dumps(rec.to_meta(), indent=2, sort_keys=True) + "\n")

    def commit(self, message: str) -> None:
        if not self.use_git:
            return
        subprocess.run(["git", "add", "-A", "."], cwd=self.root, check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-qm", message, "--allow-empty"], cwd=self.root,
                       check=True, capture_output=True)

    def next_task_id(self, n: int) -> str:
        return f"t{n:04d}"
