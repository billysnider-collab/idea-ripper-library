---
book: "Spaced seeds improve k-mer-based metagenomic classification — Karel Brinda"
genre: "Thesis"
bookline: "preprint thesis — arXiv preprint, 2015. Full text: https://archive.org/details/arxiv-1502.06256"
---

--- card
id: 1412
title: "Spaced seeds improve k-mer-based metagenomic classification"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

In metagenomic read classification, spaced seeds (k-mers with wildcard positions) beat traditional contiguous k-mers — but with an explicit operating envelope: the advantage holds below ~0.9 sequence identity; for very high-quality alignments (identity ~0.95+) contiguous k-mers with hit-number scoring win. Jaccard-index scoring amplifies the spaced-seed advantage for small-weight seeds.

## Why it matters

A crisp method claim with an explicit operating envelope — metagenomics pipelines (and any fuzzy-matching problem) should switch estimators by identity range rather than picking one winner.

## Use when

Every method has an operating envelope — spaced seeds win at low identity, contiguous k-mers at high identity; the honest answer is a switch, not a champion.
