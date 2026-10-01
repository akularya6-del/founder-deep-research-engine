# Scoring Engine

## Purpose

Calculate evidence-aware scores with stable definitions and revision history.

## Inputs

Verified candidate, evidence confidence, sector weights, portfolio context, media exposure, and scoring config.

## Outputs

Dimension scores, rationales, confidence multiplier, penalties, score history, and model version.

## Responsibilities

Score business quality, educational value, operational depth, hidden-gem value, accessibility, network value, storytelling, reply probability, podcast fit, and portfolio fit. Apply hard disqualifiers before arithmetic.

## Success criteria

Every score has a rationale; every high or low score has evidence; score totals are reproducible; and changes are append-only.

## Failure modes

Overlapping dimensions, fame bias, funding bias, missing confidence, sector mismatch, or unbounded score inflation.

## Retry logic

Re-run from canonical evidence after fixing schema or entity errors. Do not manually edit a final score without a revision record.

## Dependencies

Evidence engine, Portfolio Engine, QA, scoring-config.yaml.

