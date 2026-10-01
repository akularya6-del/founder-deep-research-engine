# Ranking Engine

## Purpose

Convert verified scores into a ranked candidate queue while preserving portfolio value.

## Inputs

Scores, category targets, diversity matrix, reserve pool, and replacement rules.

## Outputs

Ranked final set, reserve set, marginal-value calculations, substitution comparisons, and portfolio warnings.

## Responsibilities

Apply the founder ranking formula, podcast fit threshold, media penalty, confidence multiplier, category constraints, geographic diversity, and redundancy limits.

## Success criteria

The top set passes minimum thresholds and each top-25 candidate has two substitutes or a documented scarcity rationale.

## Failure modes

Quota relabeling, duplicate business models, celebrity concentration, score ties without evidence, or portfolio overfitting.

## Retry logic

Replace failed candidates from the reserve pool, recompute marginal values, and rerun QA. Never lower thresholds silently.

## Dependencies

Scoring, Portfolio, QA, State Manager.

