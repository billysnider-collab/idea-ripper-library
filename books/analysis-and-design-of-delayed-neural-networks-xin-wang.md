---
book: "Analysis and Design of Delayed Neural Networks — Xin Wang"
genre: "Nonfiction"
bookline: "Neural nets where time-delay is the hard problem, not an afterthought."
---

--- card
id: 85
title: "Three kinds of delay"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "definition"
---
## Steal

Delays resulting from the communication mode among neurons are classified as transmission delay, leakage delay, and distributed delay.

## Why it matters

"Delay" is not one bug — it is a taxonomy with different physics.

## Use when

Use when a model lumps all latency into one parameter.

--- card
id: 86
title: "Delay is inevitable — model it"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

Since delay is inevitable, it is necessary to model NNs by functional differential/difference equations, that is, differential/difference equations with delayed states.

## Why it matters

Inevitability forces a different math, not a hope that latency goes away.

## Use when

Use when a design assumes instantaneous communication between nodes.

--- card
id: 87
title: "Transmission delay as communication latency"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "definition"
---
## Steal

In the process of communication among neurons, the latency issue is inevitable, which is identified as transmission delay.

## Why it matters

Latency is renamed as a first-class delay type in the network itself.

## Use when

Use when "network lag" is treated as outside the model.

--- card
id: 88
title: "Leakage delay in the negative feedback"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

In addition, a representative delay that is fundamentally different from both transmission delay and distributed delay often appears in the negative feedbacks (i.e., leakage terms), which is named leakage delay.

## Why it matters

Feedback paths have their own delay mode — distinct from hop-to-hop lag.

## Use when

Use when stability fails and everyone only inspects forward-path latency.

--- card
id: 89
title: "Stability that should survive small undulation"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

However, it is desired that the stability of NNs will not change with small undulation of structure or parameters.

## Why it matters

Robustness is the requirement: small hardware tolerance must not flip stability.

## Use when

Use when a model works in sim and dies on slightly different chips.
