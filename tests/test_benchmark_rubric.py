"""Tests for benchmark/rubric.py — the 10-claim offline grading proxy."""

import pytest
from benchmark.rubric import (
    GROUP_NC_TRACT,
    GROUP_PARTNER,
    GROUP_RT,
    Claim,
    Finding,
    Rubric,
    Submission,
    default_rubric,
    grade_submission,
    screen_findings,
)


def _sub(*findings):
    return Submission(findings=list(findings))


def test_rubric_has_ten_claims_in_three_groups():
    rubric = default_rubric()
    assert len(rubric.claims) == 10
    assert len({c.id for c in rubric.claims}) == 10
    groups = {}
    for c in rubric.claims:
        groups.setdefault(c.group, []).append(c.id)
    assert len(groups[GROUP_NC_TRACT]) == 3
    assert len(groups[GROUP_RT]) == 2
    assert len(groups[GROUP_PARTNER]) == 5


def test_repeat_array_claim_identified():
    rubric = default_rubric()
    assert rubric.repeat_array_claim.is_repeat_array
    assert rubric.repeat_array_claim.group == GROUP_NC_TRACT


def test_asserted_scores_but_same_claim_hedged_does_not():
    rubric = default_rubric()
    asserted = grade_submission(_sub(Finding(claim="nct-1", asserted=True)), rubric)
    hedged = grade_submission(_sub(Finding(claim="nct-1", asserted=False)), rubric)
    assert asserted.asserted["nct-1"] is True
    assert asserted.score == 1
    assert hedged.asserted["nct-1"] is False
    assert hedged.score == 0


def test_hedged_possibilities_never_credit_any_claim():
    rubric = default_rubric()
    sub = _sub(*(Finding(claim=c.id, asserted=False) for c in rubric.claims))
    grade = grade_submission(sub, rubric)
    assert grade.score == 0
    assert not any(grade.asserted.values())


def test_overclaim_terms_get_no_credit():
    rubric = Rubric(claims=(
        Claim("rep-1", GROUP_NC_TRACT, "the tract contains a repeat array",
              is_repeat_array=True),
        Claim("rt-x", GROUP_RT, "the locus encodes a reverse transcriptase",
              overclaim_terms=("proven",)),
    ))
    overclaimed = _sub(Finding(
        claim="the locus encodes a reverse transcriptase",
        evidence="proven beyond doubt by our analysis"))
    measured = _sub(Finding(
        claim="the locus encodes a reverse transcriptase",
        evidence="pfam RVT_1 hit at 1e-40"))
    assert grade_submission(overclaimed, rubric).asserted["rt-x"] is False
    assert grade_submission(measured, rubric).asserted["rt-x"] is True


def test_screen_preselects_but_does_not_grade():
    rubric = default_rubric()
    # Token overlap maps this claim to rt-2, but it has no screen term and no
    # rubric reference, so the screen drops it before the judge sees it.
    dropped = Finding(claim="belongs to a single related group")
    kept = Finding(claim="belongs to a single related group",
                   evidence="seen at the rt locus")
    assert screen_findings(_sub(dropped), rubric) == []
    assert screen_findings(_sub(kept), rubric) == [kept]
    assert grade_submission(_sub(dropped), rubric).score == 0
    assert grade_submission(_sub(kept), rubric).asserted["rt-2"] is True


def test_claim_id_reference_bypasses_keyword_screen():
    rubric = default_rubric()
    # "prt-5" alone contains no screen keyword; only the rubric-id match saves it.
    f = Finding(claim="prt-5")
    assert screen_findings(_sub(f), rubric) == [f]
    assert grade_submission(_sub(f), rubric).asserted["prt-5"] is True


def test_exact_wording_reference_is_graded():
    rubric = default_rubric()
    rt1 = next(c for c in rubric.claims if c.id == "rt-1")
    grade = grade_submission(_sub(Finding(claim=rt1.wording)), rubric)
    assert grade.asserted["rt-1"] is True


def test_score_bounds_and_full_marks():
    rubric = default_rubric()
    empty = grade_submission(_sub(), rubric)
    full = grade_submission(
        _sub(*(Finding(claim=c.id) for c in rubric.claims)), rubric)
    assert empty.score == 0
    assert full.score == 10
    assert 0 <= empty.score <= 10
    assert 0 <= full.score <= 10


def test_recognized_repeat_array_iff_repeat_claim_asserted():
    rubric = default_rubric()
    rep = rubric.repeat_array_claim
    yes = grade_submission(_sub(Finding(claim=rep.id)), rubric)
    no = grade_submission(_sub(Finding(claim="rt-1")), rubric)
    assert yes.recognized_repeat_array is True
    assert no.recognized_repeat_array is False


def test_confidence_out_of_range_raises():
    with pytest.raises(ValueError):
        Finding(claim="x", confidence=1.5)
    with pytest.raises(ValueError):
        Finding(claim="x", confidence=-0.01)
    Finding(claim="x", confidence=0.0)
    Finding(claim="x", confidence=1.0)
