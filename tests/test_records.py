from pathlib import Path

from artharness.knowledge import KnowledgeBase
from artharness.records import RecordStore, TaskOrigin, TaskStatus


def test_task_lifecycle_roundtrip(tmp_path: Path):
    store = RecordStore(tmp_path, use_git=False)
    rec = store.create("t0001", "find novel RT partners", "4_neighborhood_census",
                       TaskOrigin.SEED, label="census")
    assert rec.status is TaskStatus.OPEN
    rec.status = TaskStatus.EXECUTED
    rec.revisions = 2
    store.update(rec, "task(t0001): executed")
    got = store.get("t0001")
    assert got.status is TaskStatus.EXECUTED and got.revisions == 2
    assert got.origin is TaskOrigin.SEED
    store.write_text("t0001", "summary.md", "found 3 partner families")
    assert "partner families" in store.read_text("t0001", "summary.md")
    assert store.artifact_dir("t0001").is_dir()
    assert [r.task_id for r in store.list_tasks()] == ["t0001"]
    assert store.next_task_id(7) == "t0007"


def test_create_rejects_duplicate(tmp_path: Path):
    store = RecordStore(tmp_path, use_git=False)
    store.create("t0001", "b", "5_deep_dives", TaskOrigin.DEEP_DIVE)
    import pytest

    with pytest.raises(ValueError):
        store.create("t0001", "b", "5_deep_dives", TaskOrigin.DEEP_DIVE)


def test_knowledge_retrieval_and_context_block(tmp_path: Path):
    kb = KnowledgeBase(tmp_path / "kb")
    kb.add("t0001", "retron RTs act in phage defense",
           "Retron RTs commonly act in phage defense systems with an ncRNA upstream.")
    kb.add("t0002", "CRISPR arrays make crRNAs",
           "CRISPR arrays are transcribed into crRNA guides from repeat-spacer units.")
    hits = kb.relevant("does the retron have an ncRNA upstream?", limit=1)
    assert len(hits) == 1 and "t0001" in hits[0][0].name
    block = kb.context_block("crRNA guides from arrays")
    assert "CRISPR arrays" in block and "relevance" in block
    assert kb.context_block("completely unrelated quantum coffee") == ""
