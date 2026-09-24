"""The campaign orchestrator: stage chain, task queue, triage, dispatch loop.

Faithful mechanics from the paper (Methods p.28, "Autonomous research harness"):

- launch stage chain: "A launch agent encoded the five stages of the research brief as
  a chain, with each stage closed by scripted completion checks... No task of a later
  stage was opened until the preceding stage was completed."
- worker/supervisor loop: 49 of 119 tasks revised at least once; stalls recorded
  "after ten revisions" / "after ten failed completion checks".
- triage: "Follow-up tasks proposed by agents during the work entered a triage queue,
  from which the harness released or rejected with a written reason" (10 rejected).
- curation after each completed task; editor review before filing reports.
- termination: "A campaign ended when no task remained that could be dispatched."

Gates are *scripted* callables supplied by the caller (the paper's completion checks
were scripts, not model judgments). The orchestrator never invents scientific
acceptance criteria.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .accounting import SessionLedger
from .config import CampaignConfig
from .knowledge import KnowledgeBase
from .records import RecordStore, TaskOrigin, TaskRecord, TaskStatus
from .roles import Roles

STAGES = (
    "1_input_assembly",
    "2_database_sweep",
    "3_rt_classification",
    "4_neighborhood_census",
    "5_deep_dives",
)

# Gate signature: stage_name -> True when the stage's scripted completion check passes.
Gate = Callable[[str], bool]

# Triage signature: (brief, parent_record) -> (release: bool, reason: str).
# A rejection MUST carry a written reason (paper: "released or rejected with a
# written reason"). Default policy: release everything; budget caps are enforced
# separately in Orchestrator._new_task.
TriagePolicy = Callable[[str, TaskRecord | None], tuple[bool, str]]


@dataclass
class CampaignReport:
    tasks_total: int = 0
    completed: int = 0
    rejected_at_triage: int = 0
    stalled: int = 0
    revised: int = 0
    follow_ups: int = 0
    reports_filed: int = 0

    def render(self) -> str:
        lines = [f"tasks_total={self.tasks_total} completed={self.completed} "
                 f"rejected_at_triage={self.rejected_at_triage} stalled={self.stalled}",
                 f"revised>=1: {self.revised}  follow_ups_opened: {self.follow_ups}  "
                 f"reports_filed: {self.reports_filed}"]
        return "\n".join(lines)


class Orchestrator:
    def __init__(self, cfg: CampaignConfig, store: RecordStore, kb: KnowledgeBase,
                 ledger: SessionLedger, backend, gates: dict[str, Gate],
                 triage: TriagePolicy | None = None, skills_dir: Path | None = None):
        self.cfg = cfg
        self.store = store
        self.kb = kb
        self.ledger = ledger
        self.roles = Roles(backend, store, kb, skills_dir)
        self.gates = gates
        self.triage = triage or (lambda brief, parent: (True, ""))
        self.queue: deque[str] = deque()
        self._sem = threading.Semaphore(cfg.max_concurrent_sessions)
        self.report = CampaignReport()

    # -- stage chain ---------------------------------------------------------
    def run_stage_chain(self, briefs: dict[str, list[str]],
                        deep_dive_labels: dict[str, list[str]] | None = None) -> None:
        """Encode the research brief as a chain of seeded tasks (paper: 5 stage tasks,
        16 deep dives). Each stage's tasks enqueue only after the previous stage's
        scripted gate passes."""
        opened: dict[str, list[str]] = {}
        for i, stage in enumerate(STAGES):
            for prev in STAGES[:i]:
                gate = self.gates.get(prev)
                if gate is None:
                    raise ValueError(f"stage {prev} has no scripted completion gate")
                failures = 0
                while not gate(prev):
                    failures += 1
                    if failures >= self.cfg.max_gate_failures:
                        raise RuntimeError(
                            f"gate for {prev} failed {failures} times; aborting chain")
            opened[stage] = []
            for brief in briefs.get(stage, []):
                rec = self._new_task(stage, brief, TaskOrigin.SEED)
                opened[stage].append(rec.task_id)
        deep_dive_labels = deep_dive_labels or {}
        for stage, labels in deep_dive_labels.items():
            for label in labels:
                rec = self._new_task(stage, f"Deep dive: {label}", TaskOrigin.DEEP_DIVE)
                opened.setdefault(stage, []).append(rec.task_id)

    # -- task creation / triage ------------------------------------------------
    def _new_task(self, stage: str, brief: str, origin: TaskOrigin,
                  parent: str | None = None, label: str = "") -> TaskRecord | None:
        if len(self.store.list_tasks()) >= self.cfg.max_tasks_total:
            self._reject_uncreated(brief, "task budget exhausted (max_tasks_total)")
            return None
        rec = self.store.create(self.store.next_task_id(len(self.store.list_tasks()) + 1),
                                brief, stage, origin, parent=parent, label=label)
        self.queue.append(rec.task_id)
        if origin is TaskOrigin.FOLLOW_UP:
            self.report.follow_ups += 1
        return rec

    def _reject_uncreated(self, brief: str, reason: str) -> None:
        # Budget rejections are still "rejected with a written reason"; the reason is
        # recorded in the campaign log (no task dir exists to hold it).
        self.report.rejected_at_triage += 1
        (self.store.root / "triage-rejections.log").open("a").write(
            f"REJECTED: {reason}\nbrief: {brief[:400]}\n\n")

    def propose_followup(self, brief: str, parent: TaskRecord,
                         proposed_by: str = "worker") -> None:
        ok, reason = self.triage(brief, parent)
        if ok:
            self._new_task(parent.stage, brief, TaskOrigin.FOLLOW_UP, parent=parent.task_id,
                           label=f"followup by {proposed_by}")
        else:
            self.report.rejected_at_triage += 1
            self.store.write_text(
                parent.task_id, f"triage-rejection-{len(self.store.list_tasks())}.md",
                f"REJECTED AT TRIAGE\nreason: {reason}\n\nbrief:\n{brief}\n")
            self.store.commit(f"triage({parent.task_id}): reject follow-up — {reason}")

    # -- dispatch loop ------------------------------------------------------------
    def run(self) -> CampaignReport:
        """Run until the queue is exhausted (paper's termination condition)."""
        while self.queue:
            task_id = self.queue.popleft()
            rec = self.store.get(task_id)
            with self._sem:
                self._dispatch(rec)
        return self.report

    def _dispatch(self, rec: TaskRecord) -> None:
        while True:
            out = self.roles.worker(rec)
            self.ledger.record(out.result)
            if not (self.store.records / rec.task_id / "summary.md").exists():
                # A worker that produced no summary counts as a failed completion check
                # (paper stall mode 2: "after ten failed completion checks").
                rec.gate_failures += 1
                rec.status = TaskStatus.OPEN
                self.store.update(rec, f"task({rec.task_id}): completion check failed "
                                       f"({rec.gate_failures}/{self.cfg.max_gate_failures})")
                if rec.gate_failures >= self.cfg.max_gate_failures:
                    self._stall(rec, "completion checks")
                    return
                continue

            rec.status = TaskStatus.EXECUTED
            self.store.update(rec, f"task({rec.task_id}): worker submitted summary")
            break

        # worker-proposed follow-ups enter triage
        for fu in out.proposed_followups:
            self.propose_followup(fu, rec, proposed_by="worker")

        # supervisor review loop
        while True:
            sout = self.roles.supervisor(rec)
            self.ledger.record(sout.result)
            if sout.verdict == "revise":
                rec.revisions += 1
                rec.status = TaskStatus.REVISING
                self.store.write_text(
                    rec.task_id, f"verdict-r{rec.revisions}.md",
                    f"VERDICT: revise\n\n{sout.verdict_notes or ''}\n")
                self.store.update(rec, f"task({rec.task_id}): supervisor revise "
                                       f"({rec.revisions}/{self.cfg.max_revisions})")
                if rec.revisions >= self.cfg.max_revisions:
                    self._stall(rec, "revisions")
                    return
                # worker revises (one more worker pass); follow-ups still queue
                out = self.roles.worker(rec)
                self.ledger.record(out.result)
                for fu in out.proposed_followups:
                    self.propose_followup(fu, rec, proposed_by="worker")
                continue
            break

        self.store.write_text(rec.task_id, "verdict.md",
                              f"VERDICT: accept\n\n{sout.verdict_notes or ''}\n")
        rec.status = TaskStatus.ACCEPTED
        self.store.update(rec, f"task({rec.task_id}): supervisor accepted")
        if rec.revisions >= 1:
            self.report.revised += 1

        # curator enters findings into the shared knowledge base
        self.roles.curator(rec)
        self.ledger.record(_curator_result(rec))
        rec.status = TaskStatus.CURATED
        self.store.update(rec, f"task({rec.task_id}): curated")

        self.report.completed += 1

    def _stall(self, rec: TaskRecord, mode: str) -> None:
        rec.status = TaskStatus.STALLED
        self.store.update(rec, f"task({rec.task_id}): STALLED after {mode}")
        self.report.stalled += 1

    # -- reports -----------------------------------------------------------------
    def file_report(self, task_id: str, report_text: str) -> Path | None:
        """Write a draft report and route it through editor review (52 editor sessions
        for 19 reports in the paper). Editor-rejected reports are NOT filed."""
        rec = self.store.get(task_id)
        draft = self.store.write_text(task_id, "report-draft.md", report_text)
        eout = self.roles.editor(task_id, draft)
        self.ledger.record(eout.result)
        if eout.verdict == "no":
            self.store.write_text(task_id, "report-review.md",
                                  f"FILE: no\n\n{eout.verdict_notes or ''}\n")
            self.store.commit(f"report({task_id}): editor rejected")
            return None
        final = self.store.write_text(task_id, "report.md", report_text)
        self.store.commit(f"report({task_id}): filed after editor review")
        rec.status = TaskStatus.COMPLETED
        self.store.update(rec, f"task({task_id}): report filed")
        self.report.reports_filed += 1
        return final


def _curator_result(rec: TaskRecord):
    from .accounting import SessionResult

    return SessionResult(role="curator", task_id=rec.task_id, duration_s=0.0,
                         input_tokens_uncached=0, output_tokens=0, cache_write_tokens=0)
