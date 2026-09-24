---
book: "Large Language Models in Finance — Miquel Noguer i Alonso"
genre: "Nonfiction"
bookline: "Miquel Noguer i Alonso, 2026 (Packt) — A hands-on guide to LLM architectures, agents, RAG, governance, and evaluation in finance."
---

--- card
id: 13
title: "Prediction is not agency"
field_order: ["book", "title", "steal", "why", "uw", "type", "intents", "source_locator", "related_ids", "source_url", "ripped_at", "id"]
type: "argument"
intents: ["change someone's mind", "notice what others miss"]
source_locator: "Ch. 14, §14.1"
related_ids: [14]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

Prediction and agency should not be conflated. A credit model can estimate the probability that a borrower breaches a covenant. An agentic credit workflow must additionally determine which documents are authoritative, retrieve the relevant covenant language, reconcile contradictory data, simulate possible interventions, check approval limits, request human authorization when required, execute an admissible action, and preserve an audit trail. Increasing the parameter count of the predictor does not, by itself, supply persistent memory, permissions, transaction semantics, or institutional accountability.

## Why it matters

A bigger model buys none of the institutional machinery an agent needs — memory, permissions, transaction semantics, accountability. So 'we upgraded the model' is never an answer to 'who authorized this action,' and agents must be judged on the actions they induce, not the accuracy of their outputs.

## Use when

Use when a team proposes a stronger model as the fix for an agent that lacks memory, permissioning, or an audit trail.

--- card
id: 14
title: "Grow the action set on evidence, not fluency"
field_order: ["book", "title", "steal", "why", "uw", "type", "intents", "source_locator", "related_ids", "source_url", "ripped_at", "id"]
type: "concept"
intents: ["change someone's mind", "a system feels stuck"]
source_locator: "Ch. 14, §14.9"
related_ids: [13]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

The technically and institutionally mature objective is bounded autonomy : the agent can plan, retrieve, calculate, and propose actions inside a formally defined action set, while external shields enforce limits and humans retain authority over material decisions.

## Why it matters

Fluency is the trait everyone watches improve, but it says nothing about whether an agent should be allowed to move money. The book's growth rule: the action set expands only after evidence of reliability, never because the model got more fluent — permissions follow demonstrated trustworthiness, not convincing prose.

## Use when

Use when deciding what an AI agent is permitted to do in production: which actions stay read-only, which need review gates, which are off-limits.

--- card
id: 15
title: "Audit the action, not the rhetoric"
field_order: ["book", "title", "steal", "why", "uw", "type", "intents", "source_locator", "related_ids", "source_url", "ripped_at", "id"]
type: "passage"
intents: ["change someone's mind", "notice what others miss"]
source_locator: "Ch. 14, §14.2.2"
related_ids: [14]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

This principle prevents a common category error. A model that says it will respect a mandate has not yet respected the mandate. A model that produces a prudent explanation has not yet produced an admissible order. A model that refuses a risky request in a benchmark has not thereby proved that a future tool call cannot violate an entitlement or capital limit. The audit object is the action process together with the evidence and controls surrounding it, not the rhetorical quality of the model’s answer.

## Why it matters

Benchmarks test words; real violations happen in tool calls, entitlements, and capital limits. A fluent refusal in a demo proves nothing about the next tool call, so the audit target has to be the action pipeline and its controls — never the explanation quality.

## Use when

Use when a vendor demo, benchmark score, or red-team chat log is being offered as proof that an agent is safe to deploy.

--- card
id: 16
title: "Numbers need a citation, not a story"
field_order: ["book", "title", "steal", "why", "uw", "type", "intents", "source_locator", "related_ids", "source_url", "ripped_at", "id"]
type: "passage"
intents: ["make an idea concrete", "a better question"]
source_locator: "Ch. 13, §13.4.10"
related_ids: [19]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

Production systems should separate language generation from numerical computation. Let the LLM propose hypotheses, retrieve context, or explain model outputs, but let audited numerical code compute returns, volatilities, correlations, drawdowns, and portfolio weights. A forecast report should include confidence intervals, calibration diagnostics, and explicit uncertainty. If the model cannot cite the data and computation behind a number, the number should not enter the investment process.

## Why it matters

Fluency around a number feels like evidence for it, but small numerical errors drive large position changes. The fix is architectural — audited code computes, the model explains — not a better prompt.

## Use when

Use when an LLM-generated forecast, ratio, or expected return is about to enter a report, model, or trade.

--- card
id: 17
title: "Collusion without a conversation"
field_order: ["book", "title", "steal", "why", "uw", "type", "intents", "source_locator", "related_ids", "source_url", "ripped_at", "id"]
type: "mechanism"
intents: ["notice what others miss", "a strange example"]
source_locator: "Ch. 14, §14.4.2"
related_ids: []
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

Agents optimized independently can learn strategies that soften competition or align behavior through the environment. In finance, analogous mechanisms could appear in pricing, liquidity provision, collateral terms, or execution. Monitoring must therefore examine outcome patterns and incentives, not only source-code similarity or explicit messages.

## Why it matters

Coordination needs neither communication nor shared code — independent learners can discover mutually accommodating behavior through the market itself. That makes code audits and chat-log reviews structurally blind to the risk; only outcome patterns reveal it.

## Use when

Use when assessing competition or systemic risk from multiple independently deployed trading or pricing agents.

--- card
id: 18
title: "Governance makes good uses repeatable"
field_order: ["book", "title", "steal", "why", "uw", "type", "intents", "source_locator", "related_ids", "source_url", "ripped_at", "id"]
type: "definition"
intents: ["change someone's mind"]
source_locator: "Ch. 11, §11.1"
related_ids: [15]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

The central purpose of governance is not to prevent the use of LLMs. It is to make valuable uses repeatable while keeping failure within tolerable bounds.

## Why it matters

This reframes governance from veto to engineering discipline: repeatability of the wins, boundedness of the losses. It is the definition you hand to a business line that reads every control proposal as innovation-blocking.

## Use when

Use when a governance or model-risk proposal is being dismissed as bureaucracy that slows the business down.

--- card
id: 19
title: "Freeze everything at the forecast origin"
field_order: ["book", "title", "steal", "why", "uw", "type", "intents", "source_locator", "related_ids", "source_url", "ripped_at", "id"]
type: "mechanism"
intents: ["make an idea concrete", "a better question"]
source_locator: "Ch. 13, §13.8"
related_ids: [16]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

A valid evaluation must freeze not only the price history but also the prompt, retrieval store, tools, memory, model version, and researcher workflow at each forecast origin.

## Why it matters

Backtests leak through channels most quants never freeze: the prompt, the retrieval index, the agent's memory, even the researcher's own iteration over prompt variants. Freezing prices alone leaves the impressive-but-invalid result intact.

## Use when

Use when reviewing or designing a backtest of an LLM-based forecasting or trading system.

--- card
id: 20
title: "The pipeline, not the point solution"
field_order: ["title", "type", "steal", "why", "uw", "intents", "source_locator", "book", "related_ids", "source_url", "ripped_at", "id"]
type: "argument"
intents: ["change someone's mind", "a system feels stuck"]
source_locator: "Preface"
related_ids: [21]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

Large Language Models in finance are best understood as part of a pipeline rather than as a point solution. Raw documents, time series, and market feeds are curated, normalized, and embedded; retrieval layers keep knowledge current; generation is constrained by financial identities, accounting rules, and risk limits; policies are aligned and evaluated; and decisions are executed within a framework of governance and oversight.

## Why it matters

Upgrading the model is the least interesting move in the stack: if retrieval is stale, numbers are uncited, and decisions are ungated, a better generator just produces better-looking failures faster. Budget and scrutiny should flow to the pipeline joints, not the model checkpoint.

## Use when

When a team frames an LLM project as 'pick the best model,' reframe the plan around the pipeline: curation, retrieval, constraint, alignment, governance.

--- card
id: 21
title: "Four layers have to agree"
field_order: ["title", "type", "steal", "why", "uw", "intents", "source_locator", "book", "related_ids", "source_url", "ripped_at", "id"]
type: "concept"
intents: ["a system feels stuck", "make an idea concrete"]
source_locator: "Ch. 11, §11.4"
related_ids: [20]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

The architecture has four layers, illustrated in Figure 11.1 . Evidence and assurance flow upward from infrastructure and behavior to risk and accountability, while policy, limits, permissions, and escalation rules flow downward. The layers are interdependent rather than sequential maturity levels.

## Why it matters

Controls fail at layer boundaries, not inside layers: a calibrated model fed stale data, or fresh data flowing through unpermissioned tools, breaks the system even though each layer 'works.' The four layers are the checklist for where to look when something goes wrong.

## Use when

When designing or auditing a financial LLM system, verify all four layers agree — infrastructure, behavior, risk, accountability — instead of certifying the model alone.

--- card
id: 22
title: "A fine-tuning run is defined by its contract"
field_order: ["title", "type", "steal", "why", "uw", "intents", "source_locator", "book", "related_ids", "source_url", "ripped_at", "id"]
type: "definition"
intents: ["make an idea concrete", "a better question"]
source_locator: "Ch. 3, §3.1"
related_ids: [19, 23]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

a financial fine-tuning experiment is not defined by a model name and a training set. It is defined by a decision date, a permissible information set, a task loss, a calibration protocol, and an approval boundary.

## Why it matters

Model name plus training set is how demos are described; decision date plus information set plus loss plus calibration plus approval boundary is how production systems are defended. Without the contract, a fine-tune can't be reproduced, audited, or blamed — it can only be admired.

## Use when

Before greenlighting any fine-tuning run, demand the contract: what data as of when, what loss, what calibration check, who approved it.

--- card
id: 23
title: "RAG's two controls"
field_order: ["title", "type", "steal", "why", "uw", "intents", "source_locator", "book", "related_ids", "source_url", "ripped_at", "id"]
type: "mechanism"
intents: ["notice what others miss", "a system feels stuck"]
source_locator: "Ch. 4, §4.2"
related_ids: [19, 22]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

Two things distinguish it from a generic one, and both are controls rather than models. The availability filter D ≤ t admits only documents that existed at the decision time t , which is what stops a backtest from reading tomorrow’s filing. The claim-level verifier checks each material claim A i against its retrieved evidence bundle E i before the answer is released, which is what stops a fluent answer from being an unsupported one.

## Why it matters

A RAG system fails in exactly two places that matter: letting the future leak in (the availability filter) and letting fluent prose out without evidence (the claim verifier). Everything else — embeddings, chunking, reranking — is optimization inside those two guardrails.

## Use when

When evaluating a RAG build, check the two controls first: does retrieval enforce the decision-time cutoff, and does anything verify claims against evidence before release?

--- card
id: 24
title: "MCP is a protocol, not a governance framework"
field_order: ["title", "type", "steal", "why", "uw", "intents", "source_locator", "book", "related_ids", "source_url", "ripped_at", "id"]
type: "argument"
intents: ["change someone's mind", "notice what others miss"]
source_locator: "Ch. 6, §6.1"
related_ids: [18]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

MCP is an interoperability protocol, not a complete governance framework. A regulated institution must therefore place a separate financial control envelope around MCP-based tool use. This envelope includes identity, least-privilege authorization, typed tool contracts, point-in-time evidence checks, deterministic numerical recomputation, approval gates, idempotent execution, and tamper-evident audit records.

## Why it matters

A protocol standardizes how tools talk; it says nothing about who may call them, with what authority, or what happens when they lie. Treating MCP as governance is like treating TCP as a firewall — the envelope has to be built separately, or every connected tool inherits the model's authority by default.

## Use when

When wiring MCP tools into a regulated workflow, build the control envelope first: identity, least-privilege auth, typed contracts, approval gates, audit records.

--- card
id: 25
title: "Every artifact carries its provenance"
field_order: ["title", "type", "steal", "why", "uw", "intents", "source_locator", "book", "related_ids", "source_url", "ripped_at", "id"]
type: "mechanism"
intents: ["notice what others miss", "make an idea concrete"]
source_locator: "Ch. 8, §8.1"
related_ids: [16]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

a sentence that reaches the memo without one is not a stylistic lapse but a broken audit trail.

## Why it matters

The chain breaks at table extraction — where a structured number gets flattened into prose and loses its row, column, and timestamp. Once that happens the memo looks rigorous and is unauditable; the fix is provenance at the artifact level, not prettier writing.

## Use when

When a generated memo contains numbers, trace each one back to its source artifact before trusting it — a number without lineage is decoration.

--- card
id: 26
title: "One scalar reward can't hold compliance"
field_order: ["title", "type", "steal", "why", "uw", "intents", "source_locator", "book", "related_ids", "source_url", "ripped_at", "id"]
type: "argument"
intents: ["change someone's mind", "a better question"]
source_locator: "Ch. 3, §3.7.5"
related_ids: [18]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

Capturing all of these dimensions in a single scalar reward is challenging; in practice, institutions often train separate reward models for different preference dimensions and combine their signals.

## Why it matters

A single scalar forces rigor, calibration, tone, compliance, and readability to trade off against each other inside one number — so the model learns whichever dimension is easiest to game. Separate reward models per dimension keep the trade-offs visible and auditable.

## Use when

When reviewing an RLHF setup for a compliance-sensitive task, ask how many reward dimensions are trained separately — one scalar for everything is a red flag.

--- card
id: 27
title: "Performance is not a single-number property"
field_order: ["title", "type", "steal", "why", "uw", "intents", "source_locator", "book", "related_ids", "source_url", "ripped_at", "id"]
type: "argument"
intents: ["change someone's mind", "a strange example"]
source_locator: "Preface"
related_ids: [16]
source_url: "https://www.kobo.com/ww/en/ebook/large-language-models-in-finance-1"
ripped_at: "2026-09-23"
---
## Steal

For generative systems, quality is vector-valued. A financial LLM is not judged only by a semantic metric such as ROUGE, BLEU, cosine similarity, or pairwise preference. It is judged by a tuple: (3) covering task usefulness, evidence faithfulness, numerical consistency, calibration, policy compliance, latency, and cost.

## Why it matters

A model that tops the semantic-similarity leaderboard can still hallucinate numbers, leak the future, and cost a fortune to run. Judging by one metric optimizes for the metric; judging by the tuple forces the trade-offs into the open.

## Use when

When comparing models or vendors, demand the full tuple — usefulness, faithfulness, numerical consistency, calibration, compliance, latency, cost — not a single score.
