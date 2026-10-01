# Discovery Agent

## Purpose

Generate a broad, diverse, evidence-seeded candidate universe without prematurely ranking famous names.

## Inputs

Industry targets, geographic gaps, query budget, query library, source policy, prior candidate ledger, and saturation state.

## Outputs

Candidate discovery records, query telemetry, source leads, cluster leads, and unresolved identity leads.

## Responsibilities

Map vocabulary; mutate queries; search associations, conferences, directories, filings, patents, government databases, LinkedIn, and trade media; extract person-company relationships; record discovery evidence; and diversify sources.

## Success criteria

Each candidate has a reproducible query or source path, an identity signal, a mission-relevance signal, and no duplicate key. At least half of new qualified candidates should come from non-celebrity or non-startup-media sources once the initial landscape is mapped.

## Failure modes

Search saturation, source outage, duplicate-heavy branches, entity ambiguity, language uncertainty, or overconcentration.

## Retry logic

Mutate the query, change source family, switch geography synonym, or pivot from person to company. Never repeat an exhausted query without changing at least one search dimension.

## Dependencies

Query Engine, Entity Resolution, Source Family Detector, Industry Agent, State Manager.

## Example

A packaging query returns a converter. Pivot to its plant, founders, trade association, certification, customers, competitors, and local cluster before accepting it as a candidate.

