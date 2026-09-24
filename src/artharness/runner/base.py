"""Pluggable session backends.

In the paper every agent was "an instance of Claude Code configured with Claude
Mythos 5" (Methods p.28). Here a *session backend* is any object that takes a
SessionSpec and returns a SessionResult plus written outputs.

- :class:`ScriptedBackend` — deterministic, offline; used by tests and by the dry-run
  orchestrator. It replays a scenario dict.
- :class:`ClaudeCodeBackend` — real sessions. Refuses to run unless the owner sets
  ``ARTHARNESS_ALLOW_LIVE=1`` (README "Safety gates"). Not exercised by tests.

Model identity (verified 2026-09-24): "Claude Mythos 5" is the restricted-access twin
of the publicly available Claude Fable 5; a public rerun should pin Fable 5 and record
the substitution in its receipt.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ..accounting import SessionResult


class SessionBackend(Protocol):
    """Anything that can run a role session: ScriptedBackend, ClaudeCodeBackend."""

    def run(self, spec: SessionSpec) -> BackendOutput: ...


@dataclass
class SessionSpec:
    role: str  # launch | worker | supervisor | curator | editor
    task_id: str | None
    system_prompt: str
    user_prompt: str
    workdir: Path
    skills_dir: Path | None = None  # sandbox skill library (paper: ~140 guides)
    max_output_tokens: int = 0
    extra: dict = field(default_factory=dict)


@dataclass
class BackendOutput:
    result: SessionResult
    proposed_followups: list[str] = field(default_factory=list)
    verdict: str | None = None  # supervisor: "accept" | "revise"
    verdict_notes: str | None = None


class ScriptedBackend:
    """Offline backend. ``scenario`` maps (role, task_id) -> BackendOutput.

    A default acceptance flow is synthesized when a key is missing, so a dry-run
    campaign can complete without per-task scripting. With ``write_outputs=True``
    (the default) worker sessions also write plan.md/summary.md into the task
    directory, simulating the completion check the orchestrator applies to real
    worker output.
    """

    def __init__(self, scenario: dict | None = None, tokens_per_session: int = 1000,
                 duration_s: float = 60.0, write_outputs: bool = True):
        self.scenario = scenario or {}
        self.tokens_per_session = tokens_per_session
        self.duration_s = duration_s
        self.write_outputs = write_outputs
        self.calls: list[SessionSpec] = []

    def run(self, spec: SessionSpec) -> BackendOutput:
        self.calls.append(spec)
        if spec.role == "worker" and self.write_outputs and spec.workdir.exists():
            if not (spec.workdir / "summary.md").exists():
                (spec.workdir / "plan.md").write_text("# plan (scripted)\n")
                (spec.workdir / "summary.md").write_text("# summary (scripted)\n")
        key = (spec.role, spec.task_id)
        out = self.scenario.get(key)
        if out is None:
            if spec.role == "supervisor":
                out = BackendOutput(
                    result=self._result(spec), verdict="accept",
                )
            else:
                out = BackendOutput(result=self._result(spec))
        return out

    def _result(self, spec: SessionSpec) -> SessionResult:
        return SessionResult(
            role=spec.role,
            task_id=spec.task_id,
            duration_s=self.duration_s,
            input_tokens_uncached=self.tokens_per_session,
            output_tokens=self.tokens_per_session,
            cache_write_tokens=self.tokens_per_session,
            transcript_path=None,
        )


class ClaudeCodeBackend:
    """Real Claude Code session adapter (owner-gated).

    The paper's harness ran Claude Code with connectors (metagenomic DB, literature,
    knowledge base, GPU queue). Those connectors map to MCP servers configured in the
    session environment; this adapter shells out to the ``claude`` CLI in print mode.
    """

    def __init__(self, model: str, config) -> None:
        if os.environ.get(config.live_backend_env) != "1":
            raise RuntimeError(
                f"live LLM backend requires {config.live_backend_env}=1 "
                "(owner gate; see README Safety gates)"
            )
        self.model = model

    def run(self, spec: SessionSpec) -> BackendOutput:
        cmd = [
            "claude", "-p", spec.user_prompt,
            "--model", self.model,
            "--append-system-prompt", spec.system_prompt,
            "--output-format", "json",
        ]
        proc = subprocess.run(cmd, cwd=spec.workdir, capture_output=True, text=True,
                              check=True)
        # Token fields follow claude CLI JSON output; adjust when wiring live runs.
        import json

        payload = json.loads(proc.stdout)
        usage = payload.get("usage", {})
        text = payload.get("result", "")
        verdict = verdict_notes = None
        if spec.role == "supervisor":
            # The supervisor system prompt requires a literal VERDICT: line.
            # Missing/unparseable verdict returns None — the orchestrator fails
            # toward revision (grok review 2026-09-24).
            import re

            m = re.search(r"VERDICT:\s*(accept|revise)\b", text, re.IGNORECASE)
            if m:
                verdict = m.group(1).lower()
                verdict_notes = text[m.end():].strip()[:2000] or None
        proposed = re.findall(r"PROPOSE_FOLLOWUP:\s*(.+)", text) \
            if spec.role == "worker" else []
        return BackendOutput(
            result=SessionResult(
                role=spec.role,
                task_id=spec.task_id,
                duration_s=0.0,
                input_tokens_uncached=int(usage.get("input_tokens", 0)),
                output_tokens=int(usage.get("output_tokens", 0)),
                cache_write_tokens=int(usage.get("cache_creation_input_tokens", 0)),
                transcript_path=payload.get("transcript_path"),
            ),
            proposed_followups=[p.strip() for p in proposed],
            verdict=verdict,
            verdict_notes=verdict_notes,
        )
