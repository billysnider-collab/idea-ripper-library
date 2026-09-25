---
book: "A parallel quantum computer simulator — James E. Fischer"
genre: "Thesis"
bookline: "Masters thesis — Naval Postgraduate School, 2016. Full text: https://archive.org/details/aparallelquantum1094550540"
---

--- card
id: 552
title: "A parallel quantum computer simulator"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

A matrix-free sequential quantum computer simulator vastly improves time and memory performance on a single processor; distributing the algorithm with MPI across parallel processors lets it simulate quantum systems too large to fit in any single machine's memory.

## Why it matters

Before large-scale quantum hardware exists, simulation is how quantum algorithms get developed — and the binding constraint is memory, not just speed.

## Use when

When the problem won't fit in memory, change the math before buying a bigger machine.
