# Search Query Engine

## Purpose

Generate, mutate, prioritize, and retire search queries using measurable yield.

## Inputs

Sector, geography, evidence goal, source constraints, query history, and budget.

## Outputs

Ordered query queue, mutations, query telemetry, saturation decisions, and discovered vocabulary.

## Mutation operators

- Synonym substitution.
- Role-title substitution.
- Process substitution.
- Evidence-term substitution.
- Geography and local-language substitution.
- Site restriction.
- Date window.
- Entity pivot.
- Upstream/downstream adjacency.
- Negative-noise filter.
- Question form.
- Source-family pivot.

## Prioritization

Priority equals expected qualified-candidate yield multiplied by source diversity and evidence value, divided by estimated cost. Penalize duplicate-heavy queries and saturated branches.

## Saturation rule

A branch is saturated after three consecutive mutations yield no new qualified entity, novelty falls below threshold, or all results belong to one source family. Reopen only when new vocabulary or geography appears.

## Success criteria

Every query has a parent query, mutation type, budget cost, result count, qualified yield, duplicate rate, and next action.

## Failure modes

Runaway recursion, query loops, noisy results, hidden valid candidates from over-filtering, or language drift.

## Retry logic

Revert the latest mutation, change source family, remove one exclusion, or pivot entity direction. Never loop on an identical query hash.

