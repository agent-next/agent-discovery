"""Fixed-input benchmark rubric (paper Methods "Fixed-input benchmark" p.38; Fig 4B).

The rubric scores 10 binary claims in three groups — 3 x "5-prime non-coding
tract", 2 x "RT", 5 x "partner" (paper Fig 4B). The exact claim wordings are not
published, so every wording below is a GAP placeholder; the group structure and
the 3/2/5 counts are exact.

Grading rules from the paper:

- a claim is counted only when the submission asserts it as a conclusion, not
  when it is listed as one of several hedged possibilities;
- over-claims named in the rubric receive no credit;
- the judge sees only the submission and the rubric;
- a programmatic keyword screen preselects relevant findings for the judge and
  does not contribute to the grade.

The paper's judge is a language model (Mythos 5, paper Methods p.38) that sees
only the submission and the rubric. The offline proxy here: a finding counts as
asserted unless it matches the hedge patterns below (or an explicit
``asserted=False`` says so). The paper-faithful submission format
{claim, evidence, confidence} carries no asserted field, so hedging must be
read from the text — a default-True flag credited every hedged list as a
conclusion (S1 finding C2). The RULE is the paper's; the hedge heuristic is
NOT-IN-PAPER.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Claim groups (paper Fig 4B)
GROUP_NC_TRACT = "5-prime non-coding tract"
GROUP_RT = "RT"
GROUP_PARTNER = "partner"


@dataclass(frozen=True)
class Claim:
    id: str
    group: str  # one of GROUP_*
    wording: str  # GAP: placeholder — the paper does not publish claim wordings
    wording_gap: bool = True
    is_repeat_array: bool = False  # the "recognized repeat array" headline claim
    # GAP: the rubric's named over-claims are not published; mechanism kept.
    overclaim_terms: tuple[str, ...] = ()


@dataclass
class Finding:
    """One structured finding: {claim, evidence, confidence} (paper task spec).

    ``asserted`` is the offline proxy for the LLM judge's "stated as a
    conclusion vs listed as a hedged possibility" test — NOT-IN-PAPER mechanism,
    paper rule.
    """

    claim: str  # rubric claim id, claim wording, or free text
    evidence: str = ""
    confidence: float = 1.0
    asserted: bool | None = None  # None = derive from hedge scan of the text

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")


@dataclass
class Submission:
    findings: list[Finding]
    report_path: str | None = None


@dataclass
class Rubric:
    claims: tuple[Claim, ...]

    @property
    def repeat_array_claim(self) -> Claim:
        for c in self.claims:
            if c.is_repeat_array:
                return c
        raise ValueError("rubric has no repeat-array claim")


@dataclass
class GradeResult:
    asserted: dict[str, bool] = field(default_factory=dict)  # claim id -> asserted
    score: int = 0  # 0-10
    recognized_repeat_array: bool = False


def default_rubric() -> Rubric:
    """The 10 binary claims (paper Fig 4B). Wordings are GAP placeholders."""
    return Rubric(
        claims=(
            # 3 x 5-prime non-coding tract
            Claim("nct-1", GROUP_NC_TRACT,
                  "the 5-prime non-coding tract contains a tandem repeat array",
                  is_repeat_array=True),
            Claim("nct-2", GROUP_NC_TRACT,
                  "the 5-prime non-coding tract has a conserved secondary structure"),
            Claim("nct-3", GROUP_NC_TRACT,
                  "the 5-prime non-coding tract acts as a template/primer region"),
            # 2 x RT
            Claim("rt-1", GROUP_RT,
                  "the locus encodes a reverse transcriptase"),
            Claim("rt-2", GROUP_RT,
                  "the reverse transcriptase belongs to a single related RT group"),
            # 5 x partner
            Claim("prt-1", GROUP_PARTNER,
                  "the RT has a partner protein encoded at the same locus"),
            Claim("prt-2", GROUP_PARTNER,
                  "the partner protein has a predicted structural fold"),
            Claim("prt-3", GROUP_PARTNER,
                  "the partner protein contributes to RT function"),
            Claim("prt-4", GROUP_PARTNER,
                  "the partner protein is conserved across the locus collection"),
            Claim("prt-5", GROUP_PARTNER,
                  "the partner protein associates with the non-coding tract"),
        )
    )


# Paper rule: "asserted as a conclusion, not listed as one of several hedged
# possibilities". A paper-faithful submission has no asserted field, so hedging
# is read off the claim text (NOT-IN-PAPER heuristic; conservative word list).
_HEDGES = (
    "may", "might", "could be", "possibly", "perhaps", "alternative",
    "alternatively", "one of several", "unclear", "unknown", "speculative",
    "speculatively", "hypothesis", "hypothesized", "hypothetical", "plausible",
    "not confirmed", "unconfirmed", "candidate",
)


def _is_hedged(finding: Finding) -> bool:
    text = f"{finding.claim} {finding.evidence}".lower()
    return any(re.search(rf"\b{re.escape(h)}\b" if " " not in h
                         else re.escape(h), text) for h in _HEDGES)


# NOT-IN-PAPER: the paper says a programmatic screen preselected findings but does
# not publish its keyword list; these terms cover the rubric's topic space.
_SCREEN_TERMS = (
    "repeat", "array", "tandem", "rt", "reverse transcriptase", "non-coding",
    "noncoding", "tract", "partner", "primer", "template", "orf", "locus",
    "pfam", "fold", "structure", "5-prime",
)


def screen_findings(submission: Submission,
                    rubric: Rubric | None = None) -> list[Finding]:
    """Keyword screen that preselects relevant findings for the judge.

    Paper rule: the screen only filters what the judge sees; it contributes
    nothing to the grade. When ``rubric`` is given, a finding that names a
    rubric claim id or its wording verbatim always passes — referencing the
    rubric is definitionally relevant (NOT-IN-PAPER: the paper's keyword list
    is unpublished, so claim ids are covered explicitly).
    """
    claim_ids = {c.id.lower() for c in rubric.claims} if rubric else set()
    selected = []
    for f in submission.findings:
        text = f"{f.claim} {f.evidence}".lower()
        tokens = set(re.findall(r"[a-z0-9'-]+", text))
        # a rubric id embedded in free text ("nct-1 claim is supported") names
        # the rubric — substring match, not token equality, or the finding is
        # silently dropped and the grade decided by the screen (S1 finding C)
        if any(cid in text for cid in claim_ids):
            selected.append(f)
            continue
        if any((t in text) if " " in t else (t in tokens) for t in _SCREEN_TERMS):
            selected.append(f)
            continue
        if rubric is not None and f.claim.strip().lower() in claim_ids | {
            c.wording.lower() for c in rubric.claims
        }:
            selected.append(f)
    return selected


_STOP = {
    "the", "a", "an", "of", "in", "is", "and", "or", "to", "for", "that",
    "this", "with", "gap", "placeholder", "wording", "not", "published",
}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9'-]+", text.lower()) if t not in _STOP}


def _match_claim(finding: Finding, rubric: Rubric) -> Claim | None:
    """Map a finding to a rubric claim — offline proxy for the LLM judge's mapping.

    NOT-IN-PAPER mechanism: canonical path is referencing the claim id (or exact
    wording); a token-overlap fallback handles free-text claims.
    """
    text = finding.claim.strip().lower()
    for c in rubric.claims:
        if text in (c.id.lower(), c.wording.lower()):
            return c
    best, best_hits = None, 0
    # the paper's judge sees the whole finding; free-text topics often live in
    # the evidence ("nct-1 claim is supported" + repeat-array evidence) — the
    # old claim-only token match left such findings unmapped
    ftoks = _tokens(f"{finding.claim} {finding.evidence}")
    for c in rubric.claims:
        hits = len(ftoks & _tokens(c.wording))
        if hits > best_hits:
            best, best_hits = c, hits
    return best if best_hits >= 2 else None


def _is_overclaim(finding: Finding, claim: Claim) -> bool:
    text = f"{finding.claim} {finding.evidence}".lower()
    return any(t.lower() in text for t in claim.overclaim_terms)


def grade_submission(submission: Submission, rubric: Rubric) -> GradeResult:
    """Offline grader: the paper's judge is an LLM that sees only the submission
    and the rubric; this function is the programmatic proxy for it.

    Grades only the screened findings (the screen's paper role); a finding
    credits its claim only when asserted as a conclusion and not an over-claim.
    """
    asserted = {c.id: False for c in rubric.claims}
    for f in screen_findings(submission, rubric):
        is_asserted = f.asserted if f.asserted is not None else not _is_hedged(f)
        if not is_asserted:
            continue
        claim = _match_claim(f, rubric)
        if claim is None or _is_overclaim(f, claim):
            continue
        asserted[claim.id] = True
    return GradeResult(
        asserted=asserted,
        score=sum(asserted.values()),
        recognized_repeat_array=asserted[rubric.repeat_array_claim.id],
    )
