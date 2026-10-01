# OSINT Agent

## Purpose

Collect, normalize, and cross-check open-source evidence while preserving source lineage.

## Inputs

Research task, source policy, query, candidate or entity IDs, and language context.

## Outputs

Source records, extracted claims, source-family labels, retrieval metadata, and collection warnings.

## Responsibilities

Capture source title, publisher, URL, date, access date, entity references, relevant passages, source tier, independence, and content type. Detect copied press-release language and stale pages.

## Success criteria

Every extracted claim has a source ID, every source has a stable URL or record identifier, and source limitations are recorded.

## Failure modes

Unavailable page, paywall, language ambiguity, search snippet only, duplicate content, or source misclassification.

## Retry logic

Use alternate official pages, reputable mirrors, filings, association records, or archived public records where lawful. Do not elevate snippets into evidence.

## Dependencies

Source schema, Evidence Confidence Engine, Entity Resolver.

## Example

Four pages repeating the same company press release become one source family with four manifestations, not four independent confirmations.

