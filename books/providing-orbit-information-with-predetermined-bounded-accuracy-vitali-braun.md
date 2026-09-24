---
book: "Providing orbit information with predetermined bounded accuracy — Vitali Braun"
genre: "Thesis"
bookline: "PhD thesis — Technische Universität Braunschweig, 2016. Full text: https://archive.org/details/oapen-20.500.12657-56791"
---

--- card
id: 415
title: "Providing orbit information with predetermined bounded accuracy"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

Instead of handing satellite operators raw time-tagged position tables (forcing every operator to extrapolate on his own), orbit data can be delivered as Chebyshev polynomial coefficients that directly encode the state vector and covariance matrix over a time span — derived from a reference orbit by a least-squares fit with a modified geopotential, producing orbit information of predetermined, bounded accuracy for any Earth orbit.

## Why it matters

Collision-avoidance warnings are only as good as the orbit data every party shares — this is the plumbing that lets thousands of operators agree on where every object is, at the accuracy each is entitled to, without each re-running the math.

## Use when

Don't ship raw data and make every consumer do the hard math — ship the answer at the accuracy each consumer is entitled to.
