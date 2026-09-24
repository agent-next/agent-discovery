我先按独立评审来做：定位 `agent-discovery` 的 `devin/build-modules` 相对 `main` 的完整 diff，并对照论文笔记核对常数与状态机，不改任何文件。当前工作区是 `art-harness`，评审目标是 `agent-discovery` 的分支。我先确认仓库位置和 `devin/build-modules` 相对 `main` 的范围。Memory flush started.
Memory flush completed.
论文常数账本已对上。接下来核对流水线脚本、benchmark 和测试是否与账本一致，并检查状态机里已看到的几处可疑分支。Memory flush started.
Memory flush completed.
Memory flush started.
Memory flush completed.
Memory flush started.
对照 `docs/paper-notes.md` 和论文 PDF（`/tmp/art-paper/art-paper.pdf`，Methods pp.29–33）审了 `origin/main..devin/build-modules`（`41e2f44..25937a6`，50 文件，+5357）。`orchestrator.py`、`tournament.py`、`accounting.py` 相对 main 没有改动，仍按你点名的状态机看过。

1. **major** — `pipeline/census/05_sample_neighborhoods.py:50`  
   `NOVEL_CLADES = 29` 把页Memory flush completed.
码当成了类群数。PDF 写的是 novel 每个类群 60 条、共 **16** 个类群；60×16 加上其余配额正好是 7,308，代码里的 8,088「GAP」是这个误读造成的。账本 `docs/paper-notes.md对照 `origin/main..devin/build-modules`（`41e2f44..25937a6`，50 个文件）和论文 PDF（`/tmp/art-paper/art-paper.pdf`）审完。`tournament.py` 的 342 场有序对局、权重 0.35/0.30/0.25/0.10 和 soundness ≤ 2 自动判负与 Methods p.30 一致。文献单测走注入的假 transport（`tests/test_literature.py:57`，`live=False`）。这 9 个提交说明里没有 AI 署名，diff 里也没有密钥。

1. **major** — `pipeline/census/05_sample_neighborhoods.py:50`  
   `NOVEL_CLADES = 29` 把页码当成了支系数。PDF p.29–30 写的是 novel 每个支系 60 条、共 **16** 个支系；60×16 加上其余配额正好是报告的 7,308，60×29 得到脚本自己标成 GAP 的 8,088。同一句被抄进 `docs/paper-notes.md:87`。

2. **major** — `pipeline/census/02_filter.py:143`  
   `is_weak_hit` 把 bitscore < 25、coverage < 0.35、没有 YxDD 当成三个独立丢弃条件。PDF p.29 的弱命中是这三项同时成立（模块文档字符串第 6 行也写了 and）。`tests/test_pipeline_logic.py:93` 把这个 OR 行为锁进了测试。

3. **major** — `pipeline/census/02_filter.py:133`  
   profile coverage 用的是序列 envelope（domtbl 列 19/20）长度除以 qlen。HMMER 里 profile 覆盖度是 hmm from/to（列 15/16）占模型长度的比例；envelope 是序列坐标，两者不相等时 0.75 阈值会留错或丢掉候选。

4. **major** — `pipeline/db/build_subset.sh:152`  
   `diamond cluster` 使用了 `--coverage 80 --cov-mode 5`（50% 那步是 `--cov-mode 0`）。DIAMOND 聚类文档里的覆盖度参数是 `--member-cover` 和 `--mutual-cover`，没有 `--cov-mode`。90%/70% 的 “shorter sequence” 和 50% 的 mutual coverage 因此不会按论文执行。

5. **major** — `src/artharness/arrays.py:344`  
   定界保留的是信息量得分最高的链。PDF p.32 规定先保留间距近乎恒定的**最长**链，再对那一条打分。

6. **major** — `src/artharness/arrays.py:337`  
   200 次（以及 2,000 次复查）block shuffle 仍用真实窗口里抽出的 10-nt seed 去搜打乱序列。论文要求的是每个 shuffle 自己的最佳链（该区间内每个重复出现的 10-nt word）。固定 seed 的零分布几乎打不出链，显著性检验会放过不该留的阵列。

7. **major** — `src/artharness/arrays.py:169`  
   文档写明 upstream 的下游端才是 RT，扫描窗口却取 `upstream[:3000]`（定界同样取前缀，第 331 行）。紧邻起始密码子的 3,000 / 6,000 nt 在序列末端；上游长于这个上限时，扫到的是远离 RT 的那一段。

8. **major** — `src/artharness/orchestrator.py:184`（main 上已有，本分支未改）  
   只有 `verdict == "revise"` 会进入修订/停滞；任何其他值，包括 `None`，都写成 accept。`ClaudeCodeBackend.run`（`src/artharness/runner/base.py:131`）不解析模型输出的 `VERDICT`，现场 supervisor 的 revise 和 “十次修订后停滞” 都不会发生。

9. **minor** — `src/artharness/arrays.py:275`  
   共识块在第二处低于 80% 的列上关闭时，区间端点写成 `i + 1`，把本应结束区块的那一列算进了 repeat。

10. **minor** — `src/artharness/arrays.py:164`  
   k-mer 扫描只有 “14-nt、≤2 mismatch、必须胜过 shuffle” 这一条。PDF p.32 还有第二条：精确 12-nt word 出现三次（含那个未胜过 shuffle 的 R=3 位点，以及系统发育 tip）。

11. **minor** — `pipeline/census/02_filter.py:41`、`pipeline/census/04_classify.py:37`  
   各类最短长度全部是 225，tier-1 bitscore 下限全部是 100。注释标了 GAP，但它们是默认阈值；论文的类特异长度在 225–346，类特异 bitscore floor 未用占位值代替。

12. **minor** — `tests/test_pipeline_flags.py:153`  
   覆盖度测试只要求脚本正文里出现 `--coverage 80`。非法的 DIAMOND 参数因此显示为通过；其余单测大多在卡真实边界（0.75、10 bit、配额、342 场），不是同义反复。

13. **minor** — `src/artharness/orchestrator.py:246`（main 上已有）  
   curator 会话记进 ledger 时 duration 和 token 都是 0，不用 backend 返回的 `SessionResult`。`accounting.py` 的加总公式本身与 p.30 一致（不含 cache read）。

14. **minor** — `docs/paper-notes.md:65`  
   账本写 “98 HMMs”，同一句的 6+45+1 等于 52。PDF p.29 是 52；`pipeline/census/01_hmmsearch.sh:43` 的 52 与论文一致，不要改成 98。

15. **nit** — `src/artharness/arrays.py:484`  
   `cross_scan` 的文档写结果已对称化；命中只写入被扫描位点那一侧，反向边要等对方窗口也超过阈值才会出现。

VERDICT: REQUEST_CHANGES
