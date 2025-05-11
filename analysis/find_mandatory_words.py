#!/usr/bin/env python3
"""
Find “mandatory” words in a dictionary‑definition graph and show why.

Example run command

```
python3 analysis/find_mandatory_words.py \
  --incoming_path data/graph/incoming_adj_list.json \
  --glosses_path  data/intermediates/glosses.json \
  --output_path   data/analysis/mandatory_words_with_glosses.csv
```
A head‑word W is mandatory if **at least one** of these holds
------------------------------------------------------------
1. It has **no predecessors** – i.e. nobody defines it
   (`len(incoming_adj[W]) == 0`).         Reason tag:  "no_predecessors"

2. It appears in **its own** gloss
   (`W in incoming_adj[W]`).              Reason tag:  "self_loop"
   The script now records all glosses where the match occurs.

CSV columns written
-------------------
word,reasons,example_glosses
where `reasons`           = semicolon‑separated tags
      `example_glosses`   = pipe‑separated gloss strings (may be empty)
"""

import argparse
import csv
import json
import os
import re
from typing import Dict, List

# ── helpers ──────────────────────────────────────────────────────────────────

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_mandatory(
    in_adj: Dict[str, List[str]],
    glosses: Dict[str, List[str]],
) -> Dict[str, Dict[str, List[str] | List[str]]]:
    """
    Returns mapping
       word -> {"reasons": [...], "glosses": [...]}
    """
    mandatory: Dict[str, Dict[str, List[str] | List[str]]] = {}

    for word, preds in in_adj.items():
        reasons: List[str] = []
        example_glosses: List[str] = []

        # Rule 1 — no predecessors
        if len(preds) == 0:
            reasons.append("no_predecessors")

        # Rule 2 — self loop
        if word in preds:
            reasons.append("self_loop")
            # collect glosses containing the word (case‑insensitive, whole‑word)
            gloss_list = glosses.get(word, [])
            word_re = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
            example_glosses = [g for g in gloss_list if word_re.search(g)]

        if reasons:
            mandatory[word] = {"reasons": reasons, "glosses": example_glosses}

    return mandatory

def write_csv(records: Dict[str, Dict[str, List[str] | List[str]]], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "reasons", "example_glosses"])
        for word in sorted(records):
            reasons = ";".join(records[word]["reasons"])               # type: ignore
            glosses = " | ".join(records[word]["glosses"])             # type: ignore
            writer.writerow([word, reasons, glosses])

# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="List mandatory grounding words, reasons, and example glosses"
    )
    parser.add_argument(
        "--incoming_path",
        type=str,
        default="data/graph/incoming_adj_list.json",
        help="Path to the incoming‑adjacency list JSON",
    )
    parser.add_argument(
        "--glosses_path",
        type=str,
        default="data/intermediates/glosses.json",
        help="Path to the word→glosses mapping JSON",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="data/analysis/mandatory_words_with_glosses.csv",
        help="Where to save the CSV (use '-' to print to stdout)",
    )
    args = parser.parse_args()

    in_adj   = load_json(args.incoming_path)
    glosses  = load_json(args.glosses_path)

    mandatory = compute_mandatory(in_adj, glosses)

    if args.output_path == "-":
        for w, info in sorted(mandatory.items()):
            gl = " | ".join(info['glosses'])
            print(f"{w}\t{';'.join(info['reasons'])}\t{gl}")
    else:
        write_csv(mandatory, args.output_path)
        print(f"Found {len(mandatory)} mandatory words.")
        print(f"Saved to {args.output_path}")

if __name__ == "__main__":
    main()
