# Autonomy Systems Specification

This appendix makes the V2 additions explicit. It is subordinate to the master manual and governs execution mechanics, not mission intent.

## Research Budget Allocation

Allocate the run budget before any search. Reserve recovery capacity. The controller may reallocate only through a logged budget-change event containing original allocation, requested change, expected information gain, opportunity cost, and approver.

Budget dimensions:

- Tokens: model-context and generation allowance.
- Queries: unique search attempts after mutation hashing.
- Sources: pages or records reviewed deeply.
- Tool calls: browser, search, extraction, and validation operations.
- Time: wall-clock limit.
- Candidates: maximum deep-research dossiers.
- Recovery: reserved capacity for retries, replacements, and QA.

## Token Budget Allocation

Keep an invariant digest loaded in every task. Load the full manual only in controller context. Load one agent module, one sector playbook, one candidate chunk, and the relevant schemas in task context.

Suggested token shares:

- Controller and invariant digest: 8%.
- Landscape: 8%.
- Discovery: 30%.
- Verification: 25%.
- Relationships: 8%.
- Contacts: 8%.
- Scoring and portfolio: 8%.
- QA and export: 5%.
- Recovery reserve: 8%.

When token burn reaches 80% of a stage budget, summarize completed branches, reduce low-yield branches, and protect verification and QA budgets.

## Search Budget Allocation

Allocate queries by portfolio gap, not evenly by industry. A query branch may receive more budget when its recent qualified yield and source diversity exceed the portfolio median. It must receive less when duplicate rate, source-family concentration, or unverified yield is high.

Do not count a query retry as new coverage unless the mutation changes a search dimension.

## Execution Budget

The controller checks budget before dispatch. A task may not start if its estimated cost exceeds remaining stage budget plus recovery reserve. The task must return actual consumption, not only estimates.

## Reasoning Budget

Reasoning effort is assigned by risk:

- Low: discovery lead with one relevance signal.
- Medium: qualification and relationship extraction.
- High: entity conflict, financial number, ownership, currentness, contact, or final score.
- Critical: privacy, acquisition, founder transition, or release decision.

High and critical tasks require explicit alternatives considered and a confidence rationale.

## Progress Tracking

Maintain a live funnel:

- Queries attempted.
- New entities.
- Candidate leads.
- Qualified candidates.
- Verified candidates.
- Public contact routes.
- Scored candidates.
- Final candidates.
- Reserve candidates.
- Rejected candidates by reason.
- Unresolved candidates.

Report burn rate, yield per query, yield per source family, verification pass rate, and portfolio gap at every checkpoint.

## Checkpoint System

A checkpoint is a durable snapshot of state plus artifact hashes, budget ledger, schema version, configuration hashes, and the last completed task boundary. Checkpoints are immutable. The controller writes a new checkpoint rather than overwriting the previous one.

Mandatory triggers: INIT, end of batch, state transition, budget alert, error, before replacement, before export, and after export.

## Agent Memory

Memory is divided into:

- Invariant memory: mission, prohibitions, schemas, state, and thresholds.
- Run memory: decisions, source families, query performance, and portfolio gaps.
- Candidate memory: dossier, claims, conflicts, and contact findings.
- Negative memory: rejected entities, exhausted branches, suppressed contacts, and failed hypotheses.

Every memory item has ID, scope, timestamp, source or event, confidence, expiry, and invalidation rule.

## State Management

State is a materialized view over append-only events. A task has queued, running, succeeded, retryable, dead-letter, blocked, or cancelled status. A transition is legal only if permitted by state-machine.yaml and its preconditions pass.

State must distinguish completed work from valid work. When a dependency changes, downstream tasks become stale and must be recomputed.

## Research Resume Logic

On resume:

1. Identify the latest valid checkpoint.
2. Verify checkpoint and artifact hashes.
3. Replay subsequent events.
4. Detect tasks interrupted while running.
5. Mark them retryable only if idempotency permits.
6. Reconstruct current budgets.
7. Resume from the earliest incomplete dependency.
8. Write a resume event and checkpoint.

Never assume that a process termination means a task failed; inspect output artifacts first.

## Failure Recovery

Recovery is a controlled change of strategy. A failed source request should change source family, date, language, or entity direction. A failed identity match should change alias or legal-entity search. A failed contact route should move down the approved contact hierarchy.

Policy failures are not retried. Data uncertainty becomes hold status. Resource exhaustion triggers reallocation or saturation analysis.

## Retry Algorithms

Retry only when the error class is eligible. Use bounded exponential backoff with jitter for transient errors. On every retry, mutate at least one relevant input or use an alternate source path. Hash the task inputs to prevent duplicate retry loops.

Pseudo-algorithm:

    classify(error)
    if policy_violation: dead_letter
    if attempts >= max_attempts: dead_letter
    if same_input_hash as previous_attempt: mutate_or_stop
    persist retry event
    wait according to policy
    dispatch with new attempt key

## Recursive Search Expansion

Expansion is breadth-first until useful vocabulary is found, then depth-first around high-value entities. Each branch has a parent query, mutation path, entity outputs, yield, and saturation score.

A branch expands through sector, role, process, evidence, geography, source, and entity pivots. Stop recursion when novelty and qualified yield remain below thresholds for three mutations.

## Automatic Candidate Replacement

If a final candidate fails QA:

1. Mark candidate quarantined.
2. Identify the failed constraint.
3. Search the verified reserve for candidates satisfying that constraint.
4. Rank replacements by marginal portfolio value.
5. Verify the replacement has no blocking defects.
6. Re-run portfolio and QA.
7. Record before/after membership.

Never replace a candidate solely because a more famous name appears.

## Duplicate Detection

Use normalized name, company, domain, legal entity, founder-company pair, and source-family signals. Fuzzy matches are leads for review, not automatic merges. Duplicate detection must handle punctuation, transliteration, corporate suffixes, initials, and alternate spellings.

## Evidence Confidence Engine

Evidence confidence combines directness, source tier, independence, recency, entity certainty, definition clarity, and corroboration. A direct government filing for the exact entity receives more confidence than a database estimate. Confidence is claim-specific, not candidate-wide.

A final candidate may have high identity confidence and low revenue confidence. Keep dimensions separate.

## Search Saturation Detection

Saturation is demonstrated, not declared. Required signals:

- At least three mutation classes attempted.
- At least two source families attempted.
- At least two geographic or language variants attempted where relevant.
- Adjacent upstream and downstream categories attempted.
- Marginal qualified yield below configured threshold.
- New results are mostly duplicates, weak entities, or disallowed profiles.

The saturation report must list branches, attempts, yields, gaps, and recommended future vocabulary.

## Source Family Detection

Assign a family ID when pages share publisher control, press-release text, company-controlled copy, or a copied biography. Use text similarity, URL ownership, publication timing, and named-source attribution. Independent source count is computed over family IDs, not URL count.

## Entity Resolution

Resolve person, company, product, facility, patent, association, and relationship entities. Store canonical ID, aliases, legal names, domains, geographies, dates, and resolution confidence. Do not merge entities when only names match.

## Alias Detection

Generate alias candidates from transliteration, abbreviations, corporate suffixes, maiden names only when publicly documented, alternate scripts, founder initials, and historic names. Require evidence before promoting an alias to canonical.

## Company Merge Detection

Check for merger, consolidation, holding-company formation, subsidiary creation, reverse merger, and rebranding. A company name change is not automatically a new entity. Preserve old and new names with effective dates and source edges.

## Acquisition Detection

Search official announcements, filings, investor pages, regulator records, and current leadership. Record acquirer, target, transaction date, status, surviving entity, brand status, and founder role after acquisition.

## Founder Transition Detection

Model founder status over time: founder, co-founder, successor, executive, chair, advisor, exited, or unknown. Use dated evidence. Do not describe a former founder as current operator without a current source.

## Dead Company Detection

Signals include dissolved status, expired domain, stale website, no recent operating evidence, dormant filings, discontinued products, acquisition without ongoing brand, and no current leadership. One dead signal is not enough; combine multiple signals and report uncertainty.

## Funding Timeline Reconstruction

Create round events with date, round type, amount, currency, investor, entity, source, and confidence. Separate disclosed amount, reported amount, and inferred total. Reject arithmetic that combines incompatible currencies or entities.

## Ownership Timeline Reconstruction

Track founder, promoter, investor, parent, subsidiary, and employee ownership changes by date. Use filings, official announcements, and investor records. Do not infer current ownership from an old funding round.

## Relationship Graph Construction

Represent nodes for people, companies, products, facilities, investors, customers, suppliers, partners, competitors, associations, conferences, patents, and sources. Represent edges with type, direction, date range, confidence, and source IDs.

## Supplier Discovery

Pivot from product inputs, raw materials, machinery, certifications, procurement notices, supplier directories, trade fairs, and customer qualification pages. A supplier relationship requires explicit evidence or a clearly labeled inference; never name a supplier based only on industry convention.

## Customer Discovery

Use customer announcements, case studies, procurement records, product integrations, public tender awards, and named references. Separate confirmed customer, listed customer, channel partner, trial, and logo claim.

## Partner Discovery

Search official partnership announcements, integrations, distributors, association relationships, joint ventures, and conference co-speakers. Capture the relationship’s purpose and effective date.

## Competitor Discovery

Find direct, adjacent, upstream, downstream, geographic, and substitute competitors. Use competitor relationships for discovery and context, not as proof of company quality.

## Conference Discovery Engine

Discover conferences by technical process, product, regulation, geography, and association. Extract organizers, editions, programs, speakers, sponsors, exhibitors, and recordings. Prioritize technical speaker content over sponsor presence.

## Award Discovery Engine

Find awards by regulator, association, export council, quality body, technical publication, and regional authority. Record criteria, judging, entry model, date, category, and whether the award is pay-to-enter.

## Patent Discovery Engine

Search assignee, inventor, applicant, classification, jurisdiction, family, and status. Link patents to entities only after identity resolution. Distinguish application, grant, expired, abandoned, and active status.

## Government Database Discovery Engine

Use official registries, director records, procurement portals, export programs, certification databases, industrial parks, patent offices, and regulators. Record jurisdiction and query date. Government records validate the recorded fact, not the entire narrative.

## Industrial Cluster Expansion Engine

Start with a product or process, identify regional clusters, find associations and parks, extract companies, map founders, then pivot through suppliers, customers, machinery, certifications, and local media. Stop only after cluster yield saturates or portfolio coverage is complete.

## Search Query Generator

Generate queries from sector, role, mechanism, evidence, geography, source, date, and entity dimensions. Every query receives a stable hash and parent ID. Queries must be human-readable and machine-logged.

## Search Query Mutation Engine

Mutation types are synonym, title, process, evidence, source restriction, geography, language, date, entity, adjacency, and negative filter. Mutation selection is based on the failure signal from the parent query. Do not mutate randomly.

## Cross-language Search

Maintain a translation table for sector terms, operating verbs, role titles, corporate suffixes, and evidence nouns. Preserve the original term and translation confidence. If translation is uncertain, search both languages and avoid translating claims without review.

## Japanese Search Workflow

Search English and Japanese names, corporate suffixes, prefectures, technical associations, keiretsu or group references where relevant, trade exhibitions, local industrial media, and representative-director terminology. Verify translated role titles and distinguish brand, subsidiary, holding company, and operating company.

## Relationship Mapping

For every verified candidate, seek at least two useful relationship categories: supplier, customer, partner, competitor, investor, association, conference, patent, or industrial cluster. Relationship mapping is a discovery aid and must not create unsupported claims.

## Hidden Champion Discovery

Hidden champions are under-covered operators with defensible niche position, credible operations, repeat customers, technical depth, or export presence. Search association offices, regional awards, technical fairs, industrial parks, certifications, and specialist directories.

## Hidden Champion Ranking

Score hidden champion value using low media saturation, niche leadership evidence, operating complexity, transferability, source quality, and access. Obscurity without substance scores zero.

## Founder Similarity Detection

Similarity is used to manage redundancy. Compare sector, operating mechanism, company stage, geography, ownership, customer type, and interview thesis. Similarity should trigger a substitution review, not automatic rejection.

## Portfolio Diversity Optimizer

Optimize total podcast value subject to category mix, exposure, geography, ownership, source, cluster, and story diversity constraints. Use marginal value and preserve verified reserve candidates.

## Coverage Heatmaps

Produce heatmaps for category, sub-sector, geography, company age, ownership, media exposure, physical operations, export activity, contact coverage, and evidence confidence. Empty cells become search priorities.

## Research Metrics

Track discovery yield, qualification rate, verification pass rate, contact coverage, source diversity, query saturation, duplicate rate, average cost per verified candidate, replacement rate, and QA defect rate.

## Quality KPIs

Recommended release KPIs:

- Source coverage at least 95%.
- High-confidence share at least 70%.
- Duplicate rate no more than 2%.
- Blocking defects zero.
- Public contact provenance 100% for contacts supplied.
- Category mix within tolerance or saturation documented.
- Every final candidate has a thesis and three topics.

## Research Completion Criteria

Completion requires 100 verified final founders and release-gate success. Saturation requires the documented branch, source, geography, language, and adjacency tests plus a shortfall explanation. Neither completion state permits invented data.

## Self-Critique Engine

Before portfolio lock, ask what could disprove every top candidate. Check identity, currentness, entity boundaries, source independence, operational depth, media saturation, contact legality, and portfolio redundancy. Every critique must produce pass, defect, or uncertainty.

## Automatic Error Detection

Run checks for broken source IDs, missing entity IDs, unsupported claims, duplicate domains, duplicate founder-company pairs, inferred contacts, stale roles, category mismatch, invalid score ranges, impossible dates, and missing checkpoint artifacts.

## Automatic Error Correction

Only auto-correct deterministic formatting, normalization, duplicate whitespace, known corporate suffixes, and schema-compatible nulls. Do not auto-correct factual claims, contact values, entity merges, or financial numbers. Route those to human-like review logic.

## Confidence Calibration

Compare predicted confidence against later QA findings, source corrections, and outreach outcomes. Maintain calibration buckets. If high-confidence claims fail more often than low-confidence claims, reduce the confidence model or increase verification requirements.

## Research Compression Strategy

Compress completed branches into: conclusion, evidence IDs, rejected hypotheses, query yield, remaining uncertainty, and next action. Do not compress away source IDs, dates, entity boundaries, or uncertainty.

## Long Context Strategy

Use progressive disclosure. Keep invariants, current task, relevant schemas, and current candidate in context. Retrieve other material by ID. Never place the full source corpus into context when a claim-level chunk is sufficient.

## Context Window Management

Track token estimate per task. Reserve room for output and error handling. If a task exceeds its context allowance, split by candidate, claim family, or source group and persist intermediate summaries.

## Chunking Strategy

Chunk by semantic unit: one candidate dossier, one company timeline, one source family, one relationship neighborhood, or one portfolio segment. Each chunk carries its parent IDs and provenance.

## Checkpoint Persistence

Persist state and artifacts atomically where possible. Write a temporary artifact, validate it, hash it, then commit its manifest. Keep at least two valid prior checkpoints.

## Final Validation

Final validation checks schemas, IDs, evidence lineage, source families, currentness, contact legality, scores, portfolio, exports, logs, and resume test. A final report lists passed checks, warnings, defects, and the release decision.

## Operational consequence

These controls convert a research prompt into an autonomous, observable, resumable system. When the system cannot establish a fact, it records uncertainty and reallocates search effort; it does not improvise.

