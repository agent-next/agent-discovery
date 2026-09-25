S4 只复核修复提交 `77ed5d4` 是否真正盖住你列的六条 S3 发现。我先对一下 HEAD、读 my-review 的 delta 步骤，再按条用执行结果核对。Memory flush started.
Memory flush completed.
`make check` 已通过（ruff 干净，167 passed）。接下来按六条发现做执行探针，并在临时副本里回退产品改动，确认测试真有回归效力。Memory flush started.
**VERDICT: FIX-FIRST。** 六条 S3 发现在 `77ed5d4` 上均已按执行结果关闭，但这笔修复自己引入了两条新的 major。

开闸时 `git rev-parse HEAD` 为 `77ed5d4585011a21d63cfe984d40fbaa111b5f76`。闸门结束时分支头是后到的文档提交 `244ec35`（只改 `REVIEW.md`，+17 行）。`orchestrator.py`、`arrays.py`、`test_s2_review_fixes.py` 的 blob 与 `77ed5d4` 相同。`make check` 在 `77ed5d4` 上跑过：ruff `All checks passed!`，pytest `167 passed in 10.74s`。

## 六条原发现

| # | 状态 | 修复是否成立 | 回归效力（怎么证明的） |
|---|---|---|---|
| 1 tasks_total | RESOLVED | 3 个任务：跑前 store=3、queue=3、和为 6；跑后 `tasks_total=3`，`completed=3`，queue=0 | 临时副本只把计数改回 `len(store)+len(queue)` 并放回循环前。`test_tasks_total_counts_each_task_once` 失败：`assert 6 == 3` |
| 2 file_report | RESOLVED | `status is not CURATED` 才拒绝。直接对九个状态调用：只有 `curated` 写出 `report.md`；`executed` 抛出 `ValueError(... status executed ... curator step must complete first)` | 临时副本只把判断改回 `status < CURATED`。`test_file_report_refuses_pre_curation_states` 失败：`Failed: DID NOT RAISE ValueError`。该测试打的是从未派发的 OPEN `t0001`；`executed` 的拒绝是上面的直接调用 |
| 3 失败的修订检查重派 worker | RESOLVED | 角色序列：`worker#1 → supervisor#1 → worker#2（删掉 summary）→ worker#3 → supervisor#2 → curator`。两次失败检查之间没有 supervisor。结束时 `curated`，`gate_failures=1`，`completed=1` | 临时副本换回父提交的 `_dispatch`。`test_empty_revision_recovers_via_redispatch_not_curator_crash` 失败：`FileNotFoundError`，路径是 `records/t0001/summary.md` |
| 4 修订之后能走进 completion-check stall | RESOLVED | `EmptyRevision`，`max_gate_failures=2`：`gf` 记录为 0→1→2，然后 `STALLED after completion checks`。最终 `gate_failures=2`，`revisions=1`，`stalled=1`。序列在第一次 revise 之后是 `worker#2 → worker#3`，中间没有 supervisor | 父提交的 dispatch 上同一测试失败：`revisions` 为 2，断言 `2 == 1`。状态同样是 STALLED，卡住模式是靠计数器分开的 |
| 5 先写再删，检查才有威力 | RESOLVED | 删除发生在 `ScriptedBackend.run` 之后：`summary_before_unlink=True`，`summary_after=False`，`gf` 从 0 走到 2 | 同一后端改成先删再调用 writer：writer 把 `summary.md` 写回来，`gf` 停在 0，`revisions=10`，stall 原因变成 revisions。把测试里的 `EmptyRevision` 改成这个顺序后，断言失败：`assert 0 == 2` |
| 6 第一段间隔可以是 skip | RESOLVED | `_chains([0,400,600])` → 唯一链 `[0,400,600]`（3）。`[0,400,600,800,1000]` Memory flush completed.
的最长链是 5：`[0,400,600,800,1000]`。`[0,200,400,800,1200]` 的长度集合是 `{3,4}`，最长 `[0,200,400,800]`，没有 5-链 | 父提交的 `_chains`：`[0,400,600]` 得到 0 条链；五点序列最长是 4：`[400,600,800,1000]`。`test_chains_allow_skip_as_first_gap` 在父实现上 `assert False`。二次 skip 测试在父实现上仍然通过 |

## 77ed5d4 里的新问题

**1. major，置信度 0.93。** `src/artharness/orchestrator.py:183`

失败的 completion check 仍会先收下 worker 的 follow-up。`propose_followup` 写在 `summary.md` 存在性判断之前；默认 triage 是全部放行。

探针：worker 每次都提出一条 follow-up，并在返回前删掉 `summary.md`；`max_gate_failures=2`，`max_tasks_total=30`。一次 seed 跑完：`tasks=30`，`follow_ups=29`，`rejected_at_triage=31`，30 个任务全部 `stalled` 且 `gate_failures=2`。同一探针打在父提交的 dispatch 上：`tasks=1`，`follow_ups=0`（那里的 `tasks_total=2` 是旧的 store+queue 双计，不是新开的任务）。

**2. major，置信度 0.88。** `src/artharness/arrays.py:359`

`for j in range(i + 1, len(positions))` 会把第一个间隔配到后面任意一个拷贝上，中间已经检测到的拷贝既不进链，也不计入那一次允许的 skip。`delimit_array` 按链长取最大（`arrays.py:405`）。

`[0, 180, 200, 400, 600, 800]`（180 落在间距窗 `[60, 600]` 内）：新代码最长链是 `[0, 200, 400, 600, 800]`，180 夹在第一段间隔里。父提交最长链是 `[200, 400, 600, 800]`。`[0, 200, 250, 400, 600, 800]`：新代码最长链 `[0, 400, 600, 800]`，200 和 250 都在第一段间隔内，而且这条链走的是普通间隔，不是 skip。父提交最长链是 `[400, 600, 800]`。

要求的三组输入（3-链、5-链、二次 skip 没有 5-链）不受这两个例子影响。

GATE_COMPLETE
