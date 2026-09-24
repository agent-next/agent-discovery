"""Report tournament: pairwise LLM-judged comparisons + Bradley-Terry fit.

Paper (Methods, "Ranking of reports", p.30): 19 reports, "Every ordered pair of
reports was compared once (342 games)". The judge scored each report 1-5 on impact,
novelty, soundness, actionability with weights 0.35/0.30/0.25/0.10; "The report with
the higher weighted score won, and a report with a soundness score of 2 or less lost
automatically. Ratings were fitted to all games with a Bradley-Terry model."
(The ART report ranked third, 32 wins in 36 games.)

This design descends from FutureHouse Robin (Ghareeb et al., Nature 655:497, 2026),
which ranks candidates via LLM-judged pairwise tournaments fit with
Bradley-Terry-Luce; see docs/paper-notes.md.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from itertools import permutations

from .config import CampaignConfig


@dataclass
class JudgeScores:
    impact: float
    novelty: float
    soundness: float
    actionability: float

    def weighted(self, weights: dict[str, float]) -> float:
        return (self.impact * weights["impact"]
                + self.novelty * weights["novelty"]
                + self.soundness * weights["soundness"]
                + self.actionability * weights["actionability"])


# JudgeFn(report_a_name, report_a_text, report_b_name, report_b_text) -> scores for A.
# The tournament harness anonymizes file names before calling (paper: judge read
# "two reports under anonymized file names").
JudgeFn = object  # typing placeholder: callable with that signature


def run_tournament(reports: dict[str, str], judge: JudgeFn,
                   cfg: CampaignConfig | None = None,
                   rng: random.Random | None = None) -> dict:
    """All ordered pairs, once each: n reports -> n*(n-1) games (19 -> 342)."""
    cfg = cfg or CampaignConfig()
    rng = rng or random.Random(0)
    names = sorted(reports)
    wins: dict[str, int] = defaultdict(int)
    games = 0
    for a, b in permutations(names, 2):
        # anonymize by shuffling opaque labels per game
        labels = [f"report-{i}" for i in ("X", "Y")]
        rng.shuffle(labels)
        sa = judge(labels[0], reports[a], labels[1], reports[b])
        sb = judge(labels[1], reports[b], labels[0], reports[a])
        wa = sa.weighted(cfg.judge_weights)
        wb = sb.weighted(cfg.judge_weights)
        if sa.soundness <= cfg.soundness_auto_lose:
            wa = -math.inf
        if sb.soundness <= cfg.soundness_auto_lose:
            wb = -math.inf
        if wa > wb:
            wins[a] += 1
        elif wb > wa:
            wins[b] += 1
        games += 1
    strengths = bradley_terry(wins, names)
    ranking = sorted(names, key=lambda n: strengths[n], reverse=True)
    return {"games": games, "wins": dict(wins), "strengths": strengths,
            "ranking": ranking}


def bradley_terry(wins: dict[str, int], names: list[str],
                  iters: int = 200, tol: float = 1e-8) -> dict[str, float]:
    """Maximum-likelihood Bradley-Terry strengths via MM algorithm (Hunter 2004).

    Unreferenced names get the prior strength 1.0 (NOT-IN-PAPER: paper does not
    specify regularization; ties in win counts resolve to equal strengths).
    """
    idx = {n: i for i, n in enumerate(names)}
    p = [1.0] * len(names)
    w = [wins.get(n, 0) for n in names]
    # ties counts: games against each opponent total = len(names) - 1
    n_ij = len(names) - 1
    for _ in range(iters):
        new = list(p)
        for i in range(len(names)):
            denom = 0.0
            for j in range(len(names)):
                if i == j:
                    continue
                denom += n_ij / (p[i] + p[j])
            if denom > 0:
                new[i] = w[i] / denom
        delta = max(abs(a - b) for a, b in zip(p, new))
        s = sum(new)
        p = [x / s * len(names) for x in new]  # normalize geometric-mean=1
        if delta < tol:
            break
    return {n: p[idx[n]] for n in names}
