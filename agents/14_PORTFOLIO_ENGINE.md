# Portfolio Engine

## Purpose

Optimize the final 100 as a diversified set of conversations rather than independent winners.

## Inputs

Ranked candidates, category targets, geography, ownership, company age, exposure, relationship graph, and reserve pool.

## Outputs

Portfolio selection, coverage heatmaps, diversity score, gap report, replacement recommendations, and rationale.

## Responsibilities

Measure category mix, sub-sector coverage, geographic concentration, ownership diversity, operational complexity, media saturation, hidden-gem representation, and network adjacency.

## Selection rule

Maximize total podcast value subject to hard constraints. Use marginal value: the incremental benefit of adding a candidate relative to the best available substitute in the same category.

## Success criteria

No hard constraint fails; every candidate adds distinct value; all gaps are explicit; and replacements are deterministic.

## Failure modes

Category gaming, source concentration, redundant stories, or choosing access over quality.

## Retry logic

Pull from reserve, search the highest-value gap, or document saturation. Recompute the portfolio after every replacement.

## Dependencies

Ranking, Industry, Relationship Graph, QA, state.

