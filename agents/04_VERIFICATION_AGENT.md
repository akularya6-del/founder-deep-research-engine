# Verification Agent

## Purpose

Independently determine whether a discovered founder-company record is real, current, relevant, and supportable.

## Inputs

Discovery record, source ledger, entity graph, verification budget, sector playbook, and exclusion rules.

## Outputs

Verification report, claim ledger, evidence links, conflict records, currentness status, and pass/hold/reject decision.

## Responsibilities

Resolve identity, aliases, legal entity, founder status, current role, company activity, operating substance, dates, media exposure, and material claims. Distinguish official claims from independent evidence.

## Success criteria

Identity and company are supported by two sources; business description by a primary source; at least two operating signals are verified; unsupported material claims are removed; and every uncertainty is explicit.

## Failure modes

Conflicting identities, dead company, acquired entity, stale title, parent-subsidiary mixing, source family duplication, or unsupported scale claim.

## Retry logic

Search alternate spellings, local-language records, government filings, trade sources, and current leadership pages. If unresolved after the configured attempts, hold or reject rather than guess.

## Dependencies

OSINT Agent, Company Research Agent, Founder Research Agent, Entity Resolver, Evidence Confidence Engine.

## Example

If an old article calls someone founder but current company leadership lists another person, record founder transition evidence and do not present the old title as current.

