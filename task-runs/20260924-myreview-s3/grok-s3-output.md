我先核对仓库 HEAD 是否就是 `5bd846e`，并读 `REVIEW.md` 和论文常数账本，再按执行证据审这轮修复。HEAD 已钉在 `5bd846e`。接下来跑 `make check`，并对照论文账本读这轮修复的核心 diff。`make check` 已通过（ruff 干净，163 passed）。接下来对照测试断言和论文措辞核对跳过拷贝、中位数和 stall 路径。Memory flush started.
Memory flush completed.
账本和 diff 对上了。接下来用可复现命令核对几处可疑行为：状态比较、`tasks_total`、跳过拷贝，以及 revision 完成检查是否真被测到。`make check` 通过：ruff 干净，pytest **163 passed**（10.59s）。HEAD 为 `5bd846e`（`fix/s2-review-round`）。按执行复现，这轮有 6 个会在指定输入下走错的问题，结论是 **FIX-FIRST**。

`make check` 尾部：

```
ruff check src tests pipeline benchmark
All checks passed!
python3 -m pytest
........................................................................ [ 44%]
........................................................................ [ 88%]
...................                                                      [100%]
163 passed in 10.59s
```

## findings

1. `src/artharness/orchestrator.py:163` · **major** · confidence **0.97**
   `run()` 把 `tasks_total` 设成 `len(list_tasks()) + len(queue)`。`run_stage_chain` 每建一个任务都会同时写入 store 和 queue。种子任务 `["do a thing"]` 时，跑之前 store=1、queue=`['t0001']`；`run()` 结束后 `tasks_total=2`，`completed=1`，store 里仍是 1 个任务（status `curated`）。119 个任务的账会按这个公式翻倍。

2. `src/artharness/orchestrator.py:270` · **major** · confidence **0.97**
   `file_report` 用 `rec.status < TaskStatus.CURATED` 做门。`TaskStatus` 是 `StrEnum`，比较的是字符串而不是声明顺序。实测：`open`/`executed`/`revising`/`stalled` 都 **不**小于 `"curated"`，`accepted`/`completed` 才小于。未调度的 `OPEN` 任务调用 `file_report` 直接写出 `report.md`，状态变成 `completed`。`EXECUTED`（还没过 curator）同样归档。已经 `accepted`、只差 curator 的任务反而抛 `ValueError`。

3. `src/artharness/orchestrator.py:235` · **major** · confidence **0.95**
   修订轮的完成检查失败后执行 `continue`，回到监督者循环，而不是停在检查上。输入：第一轮 worker 写出 `summary.md`，监督者第一次 `revise`，第二次修订会话删掉 summary，监督者第二次 `accept`（`max_revisions=max_gate_failures=10`）。结果：`gate_failures=1`、`revisions=1`、status 已写成 `accepted`，随后 `roles.curator` 读 `summary.md`（`roles.py:105`）抛 `FileNotFoundError`，战役中断。

4. `src/artharness/orchestrator.py:216` · **major** · confidence **0.90**
   论文默认上限都是 10。第一轮有 summary，之后每次修订都不写 summary，监督者一直 `revise`。`revisions` 在调用 worker 之前就加一，所以第 10 次 `revise` 在完成检查之前走 `_stall(..., "revisions")`。实测 stall 参数是 `('revisions', 10, 9)`：`gate_failures` 停在 9，`orchestrator.py:232` 的 `"completion checks"` 分支不会走到。

5. `tests/test_s2_review_fixes.py:179` · **major** · confidence **0.96**
   `EmptyRevision` 在 `ScriptedBackend.run` 之前删 `summary.md`。`runner/base.py:92-94` 发现文件不存在会立刻再写 `"# summary (scripted)\n"`。按测试自身的配置（`max_gate_failures=2`，`max_revisions=10`）跑完：status `stalled`，`revisions=10`，`gate_failures=0`，`summary.md` 仍在，`worker_calls=10`，存在 `verdict-r1.md`…`verdict-r10.md`。断言只看 `STALLED`，修订上限本身就会给出这个状态，完成检查路径没有被测到。

6. `src/artharness/arrays.py:338` · **major** · confidence **0.82**
   第一条间距只按 `[60, 600]` 收录，不能记成一次 skip。论文允许单次跳过拷贝。`_chains([0, 200, 600])`（skip 在第二段）得到 `[[0, 200, 600]]`。同样是周期 200、只跳过一个拷贝，但 skip 在第一段时 `_chains([0, 400, 600])` 得到 `[]`，三条拷贝的链被丢掉。`_chains([0, 400, 600, 800, 1000])` 的最长链是 `[400, 600, 800, 1000]`，开头那条拷贝被丢掉。

## checked_does_not_hold

- 第二次 skip 被拒绝。`_chains([0, 200, 400, 800, 1200])` 的长度集合是 `[4, 3]`，最长链 `[0, 200, 400, 800]`，没有长度为 5 的链。`test_chains_reject_a_second_skipped_copy` 的期望与这次输出一致。
- 单次中间 skip 成立。`_chains([0, 200, 400, 800, 1000])` 含长度为 5 的链。
- 真中位数相对 30% 容差成立。间距 200 与 350，中位数 275，偏差 75，`0.3*275=82.5`，两条都通过。`_regular_runs([0, 200, 550])` 返回 `[[0, 200, 550]]`。
- 容差窗口。`_regular_runs([0, 200, 400, 700, 900, 1100])` 返回 `[[0, 200, 400]]`，长度为 3。
- soundness 自动判负的算术成立，而且规则在起作用。`wa = 4.15`，`wb = 4.25`，`wb>wa`。`run_tournament` 的 `ranking=['a','b']`，`wins={'a': 2, 'b': 0}`。

VERDICT: FIX-FIRST

GATE_COMPLETE
