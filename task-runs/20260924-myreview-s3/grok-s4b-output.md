S4 第二轮只核 commit `a151775`。我先钉住 HEAD，再对照你上次的两条发现看修复和测试是否真的拦住了原来的失败。Memory flush started.
Memory flush completed.
导入路径指向 `/tmp/artharness-fresh`，不是当前工作区。我先确认 `make check` 实际跑的是哪一份代码，再做探针。源码和 HEAD 一致。接下来跑 `make check`，并在同一棵树上重放原来的两条探针。Memory flush started.
Memory flush completed.
**VERDICT: SHIP。** `a151775` 盖住了上一轮两条发现。固定代码上两条原探针干净通过，两条新测试在各自的产品回退上都失败，`make check` 为 169 passed。这一笔提交里没有新的可复现缺陷。

`git rev-parse HEAD` → `a151775660aaf66d5b86bfd39b7f508d3329035d`。`src/` 与 `tests/` 相对该提交无差异。pytest 实际导入的是工作区 `src/artharness/`（`pyproject.toml` 的 `pythonpath = ["src"]`），不是已安装的 `/tmp/artharness-fresh`。

`make check`：ruff `All checks passed!`，pytest `169 passed in 10.63s`。

## 两条原发现

| # | 状态 | 固定代码上的探针 | 回归效力 |
|---|---|---|---|
| 1 失败的 completion check 仍把 follow-up 送进 triage | RESOLVED | `tasks=1 follow_ups=0 rejected_at_triage=0 stalled=1`，唯一任务 `t0001` `stalled`，`gate_failures=2` | 只把 `orchestrator.py` 换回父提交后，同一测试 `assert 30 == 1`。同一探针：`tasks=30 follow_ups=29 rejected_at_triage=31 stalled=30`，30 个任务全部 `stalled` 且 `gate_failures=2` |
| 2 `_chains` 的第一段间隔跨过已检测到的拷贝 | RESOLVED | 见下方链输出。两条探针的最长链分别是 4 和 3，链内开区间里没有其它检测点 | 只把 `arrays.py` 换回父提交后，`test_chains_never_step_over_detected_copies` 失败：`([0, 400, 600, 800], [0, 180, 200, 400, 600, 800])` |

失败 pass 的 follow-up 被挪到 `summary.md` 存在性检查之后（`orchestrator.py:200-202`）。检查失败时 `continue`，不会调用 `propose_followup`。

另外两条对照，确认合法 pass 仍会立项：

- 种子第一次失败、第二次写出 summary 并提案：`tasks=2 follow_ups=1`，`t0001` curated（`gate_failures=1`），`t0002` 是 follow-up 且 curated。失败的那一次没有立项。
- summary 一直保留、只提案一次：`tasks=2 follow_ups=1`，种子 `gate_failures=0`。

链的种子改为只取连续检测（`arrays.py:363-364`）。固定代码：

```
[0, 180, 200, 400, 600, 800]
  max_len=4 longest=[200, 400, 600, 800]
  [200, 400, 600, 800] between=[]
  [400, 600, 800] between=[]
[0, 200, 250, 400, 600, 800]
  max_len=3 longest=[400, 600, 800]
  [400, 600, 800] between=[]
[0, 400, 600] → [0, 400, 600]
[0, 400, 600, 800, 1000] → 最长 5：[0, 400, 600, 800, 1000]
[0, 200, 400, 800, 1200] → 最长 4：[0, 200, 400, 800]（没有长度 5）
[0, 200, 400, 800, 1000] → 最长 5
```

父提交的 `_chains` 在同样两个输入上仍是原来的错误链：最长分别是 `[0, 200, 400, 600, 800]`（180 夹在第一段里）和 `[0, 400, 600, 800]`（200 与 250 都在第一段里）。50 nt 网格上 4004 个严格递增输入，固定代码的链在相邻成员之间都不含其它检测点（failures=0）。

两次回退都是工作区之外的副本，只替换对应产品文件为 `a151775^` 的 blob。换回 orchestrator 时链测试通过；换回 arrays 时 follow-up 测试通过。

## a151775 里的新问题

没有。失败 pass 不再立项，带 summary 的 pass 仍立项；两条探针上的跨检测点链已经消失，S3 的首间隔 skip 和二次 skip 拒绝还在。

GATE_COMPLETE
