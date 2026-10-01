# Version 2.0 Master Manual

## Authority

This file is the execution-grade supplement to deep-research-operating-manual.md Version 1. Version 1 supplies mission philosophy, sector intent, and baseline scoring. This file supplies operational precedence when the two differ.

## Operating doctrine

1. Protect truth before completeness.
2. Preserve provenance at every transformation.
3. Prefer a smaller verified set over a full set with unsupported records.
4. Spend resources where expected information gain is highest.
5. Treat every result as provisional until it passes the relevant gate.
6. Never infer private contact data.
7. Keep discovery broad and verification adversarial.
8. Make every action resumable and idempotent.

## System lifecycle

The run proceeds through INIT, LANDSCAPE, DISCOVERY, QUALIFICATION, VERIFICATION, RELATIONSHIPS, CONTACTS, SCORING, PORTFOLIO, QA, EXPORT, and COMPLETE. It may enter PAUSED, RETRYABLE_ERROR, BLOCKED, or FAILED. Only the controller may transition terminal states.

## Required artifacts

Every run creates a session record, budget ledger, query log, candidate ledger, source ledger, evidence graph, relationship graph, score history, checkpoint sequence, error log, QA report, portfolio report, and export manifest.

## Budget policy

The controller allocates budgets before discovery. No stage may borrow silently. A stage may request a reallocation with a written expected-value rationale. The controller approves or rejects the request and records the decision.

## Stage gates

- Discovery gate: candidate identity plus relevance signal.
- Qualification gate: mission fit, business reality, and no hard disqualifier.
- Verification gate: identity, company, role, operational evidence, and claim lineage.
- Contact gate: explicit public channel or documented inaccessible result.
- Score gate: rubric complete, confidence applied, and critique complete.
- Portfolio gate: mix, diversity, and replacement rules pass.
- Release gate: schema validation, source coverage, unresolved-risk report, and final checklist pass.

## Evidence invariant

No final sentence may contain a material fact unless it points to one or more evidence IDs. No evidence ID may point to a source outside the source ledger. No source may be treated as independent if it belongs to a known source family.

## Autonomous execution contract

The agent must not ask a clarification question for a preference that can be resolved by the configs or manual. It may pause only for safety, missing authorization, unavailable required input, or an unresolved identity that creates material risk. All routine uncertainty becomes a recorded status, not a question.

## Completion definition

Complete means 100 verified founders exist and all release gates pass, or saturation is demonstrated through the saturation algorithm and the final report states the shortfall, coverage, and next-best actions. A quota must never be met by lowering evidence standards silently.

