---
book: "Empirical analysis of using erasure coding in outsourcing data storage with provable security — Abdallah Bakir"
genre: "Thesis"
bookline: "Masters thesis — Naval Postgraduate School, 2016. Full text: https://archive.org/details/empiricalnalysis1094549341"
---

--- card
id: 398
title: "Empirical analysis of using erasure coding in outsourcing data storage with provable security"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

Proof of retrievability (POR) and proof of data possession (PDP) are cryptographic auditing tools that give probabilistic guarantees a server or cloud is actually storing your data — without downloading the whole file — and can recover the original data under certain limits; maximum distance separable (MDS) codes, specifically Reed-Solomon and Cauchy Reed-Solomon, are the recoverability engine, and the thesis surveys them and implements both into a prototype POR library built on the liberasurecode library.

## Why it matters

Every "is my cloud copy intact?" guarantee rests on this primitive — verifying petabytes without re-downloading them is what makes outsourced storage auditable instead of faith-based.

## Use when

You don't need to hold the whole thing to prove it's intact — probabilistic proof beats full inspection; audit at the cheapest level that still binds.
