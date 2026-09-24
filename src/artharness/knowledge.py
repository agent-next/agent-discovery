"""Shared knowledge base.

Paper (Methods, p.28): "After each completed task, a curator agent read the task brief
and the worker's summary and entered the findings into a shared knowledge base.
Relevant entries were included in the prompts of later workers and supervisors."

Implementation: one markdown file per entry under ``entries/`` with a task-id
provenance header, plus term-overlap retrieval to select "relevant entries" for a
prompt. Deliberately simple and auditable — the paper does not specify its retrieval
mechanism (NOT-IN-PAPER: scoring scheme).
"""

from __future__ import annotations

import re
import time
from pathlib import Path

_WORD = re.compile(r"[a-z0-9_]{3,}")


def _terms(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


class KnowledgeBase:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.entries_dir = self.root / "entries"
        self.entries_dir.mkdir(parents=True, exist_ok=True)

    def add(self, task_id: str, title: str, body: str) -> Path:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "entry"
        path = self.entries_dir / f"{task_id}-{slug}.md"
        path.write_text(
            f"---\ntask: {task_id}\ntitle: {title}\nrecorded: "
            f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\n---\n\n{body}\n"
        )
        return path

    def all_entries(self) -> list[tuple[Path, str]]:
        return [(p, p.read_text()) for p in sorted(self.entries_dir.glob("*.md"))]

    def relevant(self, query: str, limit: int = 5) -> list[tuple[Path, str, float]]:
        """Entries ranked by term overlap with the query (0-overlap entries excluded)."""
        q = _terms(query)
        scored = []
        for path, text in self.all_entries():
            overlap = len(q & _terms(text))
            if overlap:
                scored.append((path, text, overlap / max(1, len(q))))
        scored.sort(key=lambda t: t[2], reverse=True)
        return scored[:limit]

    def context_block(self, query: str, limit: int = 5) -> str:
        """Render retrieved entries for injection into a worker/supervisor prompt."""
        hits = self.relevant(query, limit)
        if not hits:
            return ""
        parts = ["# Knowledge base (relevant prior findings)"]
        for path, text, score in hits:
            parts.append(f"\n## {path.stem} (relevance {score:.2f})\n\n{text}")
        return "\n".join(parts) + "\n"
