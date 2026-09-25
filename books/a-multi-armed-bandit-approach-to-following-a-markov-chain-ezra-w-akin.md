---
book: "A multi-armed bandit approach to following a Markov Chain — Ezra W. Akin"
genre: "Thesis"
bookline: "Masters thesis — Naval Postgraduate School, 2017. Full text: https://archive.org/details/amultiarmedbandi1094555572"
---

--- card
id: 550
title: "A multi-armed bandit approach to following a Markov Chain"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

The "follow the target" problem — many possible locations, far fewer sensors, only intermittent observation — can be solved as a multi-armed bandit over a discrete-time Markov chain: at each time step, allocate the sensor to the state with the highest probability of containing the target.

## Why it matters

It's the mathematics of ISR triage — how to allocate scarce eyes when continuous coverage is impossible.

## Use when

When you can't watch everything, the optimal move is a computed bet on where to look next — allocate to the highest-probability state, not the widest coverage.
