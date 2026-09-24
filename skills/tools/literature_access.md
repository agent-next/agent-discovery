# Literature access (Europe PMC)

Connector for literature search and open-access full text. Available at L5 /
with the literature tool enabled (paper: L5 adds literature search and web
access).

## Search syntax

Europe PMC query language — the useful subset:

- `TITLE:"phrase"` / `ABSTRACT:"phrase"` — field-restricted phrase search;
- `AUTH:"surname"` — author search;
- `AND`, `OR`, `NOT` — boolean, uppercase;
- `OPEN_ACCESS:Y` — restrict to full-text-available records;
- `FIRST_PDATE:[YYYY-01-01 TO YYYY-12-31]` — date windows;
- sorting: `sort_cited desc` for most-cited first.

GAP: recommended query patterns — the paper grants literature access but
does not publish the connector's query conventions.

## Full text vs landing pages

- `OPEN_ACCESS:Y` hits have fetchable full text (XML); quote and cite from
  full text only.
- Non-open records give title + abstract only. An abstract can support
  "reported X" but not "showed X by method Y" — do not infer methods or
  numbers you cannot read.
- Never cite a landing page or a search-result snippet as evidence for a
  substantive claim.

## Citation discipline

- Every literature-derived claim carries: author-year, title, and the
  Europe PMC / PubMed id.
- Quote the supporting sentence or figure reference; "see [12]" without a
  locator fails curator review.
- Distinguish "the paper reports" (their result) from "consistent with"
  (your interpretation) in the claim wording.

## Record what was searched

For every session that touches literature, log:

- exact query strings, in the order run,
- result counts and which records were actually read,
- date of search (database contents change).

Negative searches are evidence — `novelty_claims` requires them in the
report. A claim of novelty without a recorded search log is incomplete.
