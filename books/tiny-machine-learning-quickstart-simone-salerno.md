---
book: "Tiny Machine Learning QuickStart — Simone Salerno"
genre: "Nonfiction"
bookline: "ML that fits on tiny devices — constraints as the design surface."
---

--- card
id: 80
title: "AI on the smallest, most constrained devices"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "definition"
---
## Steal

This convergence has given birth to Tiny Machine Learning (often shortened as TinyML®, trademark of the EdgeAI foundation)—a field that brings the power of artificial intelligence to the smallest and most resource-constrained computing devices.

## Why it matters

The field is defined by scarcity, not by model cleverness alone.

## Use when

Use when "edge AI" is used as a buzzword without naming the constraint.

--- card
id: 81
title: "Fit inside memory, power, and energy budgets"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

Unlike cloud-based machine learning systems with virtually unlimited resources, TinyML development requires careful optimization to fit within tight memory constraints, limited processing power, and strict energy budgets.

## Why it matters

Cloud habits (scale out) are the wrong reflex; the work is fit-to-budget.

## Use when

Use when a team ports a cloud model and is shocked it will not fit.

--- card
id: 82
title: "Embedded hardware = limited CPU, program space, RAM"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "evidence"
---
## Steal

Due to size, efficiency, power, and cost constraints, embedded hardware is characterized by limited resources (CPU, program space, and RAM).

## Why it matters

The envelope is the forcing function: fixed mass, fixed power, fixed link budget means every subsystem trades against every other — constraint is what turns a wish list into a design.

## Use when

Use when someone argues "just use a bigger chip" as if cost and power were free.

--- card
id: 83
title: "Train heavy, deploy light"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

We can exploit this asymmetry by training our models on resource-heavy hardware, such as a desktop PC, and then converting them into a lightweight format that fits the constraints of our embedded hardware.

## Why it matters

Asymmetry is the method: expensive training, cheap inference.

## Use when

Use when training and deployment are treated as the same machine problem.

--- card
id: 84
title: "Growth of models vs embedded limits"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

Historically, the power of machine learning algorithms has increased over time, largely due to the growth in the size and complexity of the models.

## Why it matters

Progress-by-scale collides with devices that cannot scale.

## Use when

Use when a roadmap assumes bigger models are always better.
