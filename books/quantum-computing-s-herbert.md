---
book: "Quantum Computing — S. Herbert"
genre: "Nonfiction"
bookline: "Foundations of qubits — superposition, entanglement, measurement, no free signaling."
---

--- card
id: 98
title: "Measure and the slit chooses"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

The qubit can then optionally be measured, in which case either of the states |0⟩ and |1⟩ is observed, as the measurement apparatus detects through which slit the photon passes.

## Why it matters

Measurement is apparatus choosing a slit story — not a gentle peek.

## Use when

When "observe" is used as if it were free.

--- card
id: 99
title: "Unmeasured qubit keeps interference"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

If a measurement is not taken, the qubit will be in a superposition of |0⟩ and |1⟩, and its onward evolution can involve the interference of these two components.

## Why it matters

Superposition is useful only while uncollapsed — interference is the payload.

## Use when

When explaining why you cannot peek mid-algorithm without killing the advantage.

--- card
id: 100
title: "n-qubit state as 2^n complex unit vector"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "definition"
---
## Steal

Together, postulates 1 and 4 state that an n-qubit quantum state is represented by a 2^n-element complex unit vector.

## Why it matters

Dimension explodes as 2^n — the cost of the state space is the feature.

## Use when

When classical intuition expects linear growth in bits.

--- card
id: 101
title: "Unitary as Bloch-sphere map"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "mechanism"
---
## Steal

As a single-qubit unitary maps a single-qubit state to another single-qubit state, a unitary transformation is itself an operation that maps all of the points on the surface of the Bloch sphere to other points on the surface of the Bloch sphere.

## Why it matters

Gates are rigid rotations of the sphere — no leaking off the surface.

## Use when

When visualizing quantum ops as geometry, not algebra.

--- card
id: 102
title: "Collapse kills superluminal signaling fantasy"
field_order: ["title", "book", "type", "steal", "why", "uw", "id"]
type: "argument"
---
## Steal

Whereas if Alice has measured her qubit, then Bob's qubit has collapsed – it is either in state 0, or state 1 (each with probability 1/2).

## Why it matters

Entanglement plus local measurement does not give Bob Alice's message — only shared randomness after collapse.

## Use when

When someone claims spooky action equals a phone.
