# Spreadsheet and Export Specification

## Purpose

Define stable exports for researchers, producers, and downstream systems.

## Required exports

- founders.csv: one row per final or reserve founder.
- companies.csv: one row per company entity.
- evidence.csv: one row per claim-source edge.
- contacts.csv: one row per public contact route.
- scores.csv: append-only score revisions.
- portfolio.csv: final portfolio membership and rationale.
- unresolved.csv: unresolved conflicts, missing data, and blocked tasks.
- manifest.json: run, schema, version, hash, and completion metadata.

## Rules

Use stable IDs, ISO dates, explicit nulls, controlled enums, no merged cells, and source IDs instead of copied long URLs in every field. Preserve the full source ledger separately.

## Success criteria

Every row validates, joins through IDs, and can reconstruct the candidate dossier without hidden spreadsheet context.

