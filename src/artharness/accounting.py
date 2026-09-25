"""Campaign accounting: sessions, agent-hours, tokens.

Paper (Methods, "Campaign accounting", p.30): 119 tasks; 949 sessions = launch 1 +
worker 414 + supervisor 375 + curator 107 + editor 52; 76.9 agent-hours (63.7 in
worker sessions); 215.6M tokens = 11.3M uncached input + 14.9M output + 189.5M
prompt-cache writes; cache reads excluded.

This ledger reproduces that accounting format so a rerun can be compared line by line
with the paper. JSONL persistence, one record per finished session.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROLES = ("launch", "worker", "supervisor", "curator", "editor")


@dataclass
class SessionResult:
    role: str  # one of ROLES
    task_id: str | None
    duration_s: float
    input_tokens_uncached: int
    output_tokens: int
    cache_write_tokens: int
    transcript_path: str | None = None
    over_budget: bool = False  # exceeded spec.max_output_tokens (post-hoc; the
    # claude CLI cannot cap output mid-run)

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_jsonl(cls, line: str) -> SessionResult:
        return cls(**json.loads(line))


class SessionLedger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, result: SessionResult) -> None:
        with self.path.open("a") as fh:
            fh.write(result.to_jsonl() + "\n")

    def sessions(self) -> list[SessionResult]:
        if not self.path.exists():
            return []
        return [SessionResult.from_jsonl(line) for line in
                self.path.read_text().splitlines() if line.strip()]

    def summary(self) -> dict:
        """Campaign totals in the paper's accounting format."""
        sessions = self.sessions()
        by_role = {r: 0 for r in ROLES}
        worker_hours = 0.0
        total_hours = 0.0
        tokens = {"input_uncached": 0, "output": 0, "cache_write": 0}
        for s in sessions:
            by_role[s.role] = by_role.get(s.role, 0) + 1
            total_hours += s.duration_s / 3600
            if s.role == "worker":
                worker_hours += s.duration_s / 3600
            tokens["input_uncached"] += s.input_tokens_uncached
            tokens["output"] += s.output_tokens
            tokens["cache_write"] += s.cache_write_tokens
        return {
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "sessions_total": len(sessions),
            "sessions_by_role": by_role,
            "agent_hours_total": round(total_hours, 1),
            "agent_hours_worker": round(worker_hours, 1),
            "tokens_total": sum(tokens.values()),
            "tokens": tokens,
        }
