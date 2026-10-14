---
book: "Probabilistic Modelling of Morphologically Rich Languages — Jan A. Botha"
genre: "Thesis"
bookline: "PhD thesis — University of Oxford, 2015. Full text: https://archive.org/details/arxiv-1508.04271"
---

--- card
id: 1434
title: "Probabilistic Modelling of Morphologically Rich Languages"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

Treating words as opaque symbols is the wrong assumption for morphologically complex languages. Encoding morphology into three model types — a Bayesian compound-decomposition n-gram model, a distributed model learning vector representations of morphemes, and an unsupervised model that discovers even discontiguous (Semitic-style) morphemes — improves model performance and beats the data sparsity that morphological processes create, with benefits for machine translation.

## Why it matters

A 2015 Oxford thesis that prefigures the subword-tokenization era (BPE, SentencePiece) — it argued a decade early that models must learn word-internal structure to handle morphologically rich languages.

## Use when

Don't model the surface — learn the substructure; the regularities that fix sparsity live inside the unit everyone treats as atomic.
