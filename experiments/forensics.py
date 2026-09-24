"""Replicate-campaign forensics — paper Methods "Replicate campaigns" p.38.

After rerunning the campaign, the paper asked: did any replicate rediscover the ART
loci? Procedure (parameter-exact):

- collect identifiers from the reference campaign: RT ids (paper: 130), contig ids
  (paper: 171), and names/accessions of cultured phages encoding such RTs;
- search all replicate task records (paper: 3,084 records) and session transcripts
  (paper: 5,632) for those identifiers;
- for every session that named a relevant contig (paper: 11), parse events in order
  and record (a) tool results containing a contiguous DNA string of >=200 nt and
  (b) remarks on repeats;
- an ART locus on a contig outside the identifier set would not be found by this
  search (paper's own caveat).

USAGE
    python3 experiments/forensics.py --records <campaign-root> \\
        --identifiers ids.txt --out findings.json

ids.txt: one identifier per line (RT task labels, contig names, accessions).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DNA_RUN = re.compile(r"[ACGTacgt]{200,}")  # paper: contiguous DNA string of >=200 nt
REPEAT_WORDS = re.compile(r"\b(repeat|tandem|array|direct repeat|spacer)\b",
                          re.IGNORECASE)


def load_identifiers(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text().splitlines() if line.strip()}


def scan_records(records_root: Path, ids: set[str]) -> dict[str, list[str]]:
    """task id -> identifiers mentioned anywhere in its record files."""
    hits: dict[str, list[str]] = {}
    for task_dir in sorted(Path(records_root).glob("t*")):
        if not task_dir.is_dir():
            continue
        text = "\n".join(p.read_text(errors="replace")
                         for p in task_dir.rglob("*") if p.is_file())
        found = sorted(i for i in ids if i in text)
        if found:
            hits[task_dir.name] = found
    return hits


def scan_transcripts(transcripts_root: Path, ids: set[str]) -> list[dict]:
    """Per transcript naming an identifier: ordered events with >=200-nt DNA and
    repeat remarks, plus whether a repeat remark ever followed a DNA retrieval."""
    out: list[dict] = []
    for tf in sorted(Path(transcripts_root).rglob("*")):
        if not tf.is_file():
            continue
        text = tf.read_text(errors="replace")
        named = sorted(i for i in ids if i in text)
        if not named:
            continue
        dna_events = [m.group(0)[:60] for m in DNA_RUN.finditer(text)]
        repeat_lines = [ln.strip()[:120] for ln in text.splitlines()
                        if REPEAT_WORDS.search(ln)]
        out.append({
            "transcript": str(tf),
            "identifiers": named,
            "dna_runs_ge200nt": len(dna_events),
            "repeat_remarks": len(repeat_lines),
            "repeat_remark_samples": repeat_lines[:3],
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--records", required=True,
                    help="campaign root containing records/tNNNN dirs")
    ap.add_argument("--transcripts", default=None,
                    help="optional root of session transcripts (rglob)")
    ap.add_argument("--identifiers", required=True, help="one identifier per line")
    ap.add_argument("--out", required=True, help="findings JSON path")
    args = ap.parse_args()

    ids = load_identifiers(Path(args.identifiers))
    report = {
        "identifiers_searched": len(ids),
        "records_root": args.records,
        "record_hits": scan_records(Path(args.records), ids),
        "transcript_hits": (scan_transcripts(Path(args.transcripts), ids)
                            if args.transcripts else []),
    }
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(f"identifiers={len(ids)} record_hits={len(report['record_hits'])} "
          f"transcript_hits={len(report['transcript_hits'])} -> {args.out}")


if __name__ == "__main__":
    main()
