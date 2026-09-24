import random

from artharness.config import CampaignConfig
from artharness.tournament import JudgeScores, bradley_terry, run_tournament


def test_tournament_game_count_19_reports():
    reports = {f"r{i:02d}": f"report {i}" for i in range(19)}
    judge = lambda name, a, other, b: JudgeScores(3, 3, 4, 3)  # noqa: E731
    out = run_tournament(reports, judge, rng=random.Random(0))
    assert out["games"] == 342  # paper: 19 reports -> 342 ordered-pair games


def test_weights_and_soundness_auto_lose():
    cfg = CampaignConfig()
    unsound = JudgeScores(impact=5, novelty=5, soundness=2, actionability=5)
    reports = {"a": "A", "b": "B", "c": "C"}

    def judge(name, a, other, b):
        # `a` is the text of the report being scored in this half-game
        if a == "B":
            return unsound  # weighted 4.25 but soundness 2 -> auto-lose
        return JudgeScores(5, 5, 5, 5) if a == "A" else JudgeScores(4.5, 5, 5, 5)

    out = run_tournament(reports, judge, cfg=cfg, rng=random.Random(0))
    # B scores <=2 on soundness -> loses automatically regardless of weighted total
    assert out["ranking"][0] == "a"
    assert out["wins"]["a"] == 4  # beats b and c in both orders
    assert out["wins"]["b"] == 0


def test_bradley_terry_orders_by_wins():
    names = ["a", "b", "c"]
    wins = {"a": 4, "b": 2, "c": 0}
    s = bradley_terry(wins, names)
    assert s["a"] > s["b"] > s["c"]


def test_perfect_ties_get_equal_strength():
    s = bradley_terry({"a": 1, "b": 1}, ["a", "b"])
    assert s["a"] == s["b"]
