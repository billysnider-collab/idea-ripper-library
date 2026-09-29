---
book: "Algorithms Every Programmer Should Know — Aniket Wattamwar"
genre: "Nonfiction"
bookline: "Manning MEAP early access (6 of 14 chapters): algorithms as plain-language thinking tools for matching, searching, and deciding."
---

--- card
id: 858
title: "Everything you optimize costs you something else"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "concept"
---
## Steal

Before you chase "better," name what you are giving up to get it. Speed costs money. Thoroughness costs time. Reach costs attention. Optimize the thing you can least afford to lose, and accept the trade you did not choose.

## Why it matters

There is no universal best; every optimization sacrifices a constraint, so the real question is which cost you can afford.

## Use when

You are deciding between two "better" options and keep assuming one is best in every way, or someone promises a solution with no downside.

--- card
id: 859
title: "Design for the worst day, not the average one"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "concept"
---
## Steal

When you plan a system, a launch, or a budget, design for the worst realistic case, because that is exactly where things break. The average case is the pleasant lie; the edge case is where the damage lives.

## Why it matters

Failure happens at the edges, not the average, so the worst case is the honest metric.

## Use when

You are sizing a plan, a budget, or a capacity and someone says "on average it will be fine."

--- card
id: 860
title: "Get a working answer before you get a clever one"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

Do the crude version first, the one that just works, then improve it once you can see the real bottleneck. Optimizing before you have a working baseline means you are polishing a guess.

## Why it matters

Start with the dumb, obvious solution, then refine it; optimizing too early is a trap.

## Use when

You are stuck planning the perfect approach, or someone wants to optimize a process that does not work yet.

--- card
id: 861
title: "Your process is only as fast as what you built it on"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "concept"
---
## Steal

Before you improve a process, check the structure underneath it. If you are storing or organizing things the wrong way, no amount of hard work inside the process will fix it. Fix the container, then the process.

## Why it matters

An algorithm is only as fast as the structure it runs on; the wrong container makes even a good process slow.

## Use when

A process stays slow no matter how hard people work it, and every fix only shaves the surface.

--- card
id: 862
title: "The one who asks first gets the better outcome"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

If you want the better outcome in a two-sided arrangement, hiring, partnerships, admissions, dating, be the side that proposes. The accepting side can only say yes or no to what shows up; the proposing side controls the options it presents.

## Why it matters

In any two-sided match, the side that proposes gets its best stable result; the side that waits and accepts gets the leftover.

## Use when

You are setting up or entering a two-sided market or negotiation and want to know which side the rules favor.

--- card
id: 863
title: "Subtract the unavoidable cost; what is left is the decision"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

When comparing options, first subtract the cost you will pay no matter what. What is left is the actual difference you are deciding about. The unavoidable part is not the decision; the remainder is.

## Why it matters

Strip out the minimum every option already carries, and the zeros that remain reveal the cheapest assignment.

## Use when

A decision feels overwhelming because the numbers are large, but most of the cost is identical across options.

--- card
id: 864
title: "Do not fix one part by breaking the whole"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "concept"
---
## Steal

When you optimize, check the whole board, not just the square in front of you. A change that makes one person, team, or route better often makes the total worse. Optimize globally, then let the local wins follow.

## Why it matters

The greedy mistake is optimizing one item locally and making the overall system worse.

## Use when

A team is optimizing its own piece while the total keeps getting worse, or you are tempted to grab the obvious quick win.

--- card
id: 865
title: "Screen with a cheap test, verify only the near-misses"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

When you have to check many things against many things, use a fast, cheap screen to rule out almost everything, then spend real effort only on the few that pass. Fingerprint first, inspect second.

## Why it matters

Compare a quick fingerprint first; run the full, expensive check only when the fingerprint matches.

## Use when

You are searching or matching across a large set and the full check is slow or expensive.

--- card
id: 866
title: "Do not recompute from scratch; update the part that changed"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

When a small piece of the picture changes, do not rebuild the whole picture. Subtract what left and add what arrived. Most 'rework' is really 'recompute everything,' and it is almost always avoidable.

## Why it matters

Slide the window and adjust only what entered and left, instead of redoing the whole calculation.

## Use when

You are recalculating a total, a forecast, or a status every time one thing changes.

--- card
id: 867
title: "When you fail partway, the failure tells you where to resume"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "concept"
---
## Steal

When something fails partway through, do not restart from zero. The point where it broke tells you exactly how far you had gotten and where to resume. Failures carry information; the wasteful move is discarding it.

## Why it matters

A mismatch is not a failure but a source of information; do not throw away the progress you already made.

## Use when

A plan, a sale, or a project fails partway and the instinct is to scrap everything and start over.

--- card
id: 868
title: "Look at the one thing that rules out the most, first"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

Before you inspect something fully, check the single most informative fact first, the one that, if wrong, rules the whole thing out. When that fact clears, skip. The more specific your target, the faster you can eliminate.

## Why it matters

If the thing you are looking at cannot possibly be part of the answer, skip past it entirely.

## Use when

You are narrowing a large field and cannot afford to examine everything in full.

--- card
id: 869
title: "Pick your search style: go deep on one path, or wide across all"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

When exploring options, know which you need: depth (commit to one path, follow it to the end, backtrack only if it dies) or breadth (survey all options at this level before going deeper). Depth risks missing alternatives; breadth risks never finishing any.

## Why it matters

Depth-first plunges down one path to the bottom; breadth-first surveys everything at this level before descending.

## Use when

You are exploring a decision tree, a market, or a problem space and keep oscillating between chasing one idea and surveying everything.
