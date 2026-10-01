# Version 1 Audit Report

## Scope

Audited deep-research-operating-manual.md as Version 1. The audit evaluates whether a coding agent could execute the mission autonomously, recover from interruption, validate its own work, and export reliable results.

## Severity model

- Critical: execution can produce unsafe, invalid, or unverifiable output.
- High: execution may complete but quality, coverage, or reproducibility is materially compromised.
- Medium: causes inefficiency, inconsistent decisions, or difficult maintenance.
- Low: usability, polish, or future extensibility issue.

## Critical findings

### C-01: No executable state machine

Version 1 describes phases but does not define durable states, legal transitions, terminal states, or recovery semantics. A coding agent cannot safely resume after interruption.

Remedy: state-machine.yaml, State Manager module, checkpoint schema, transition guard, and resume protocol.

### C-02: No machine-valid record contracts

The spreadsheet schema is descriptive and does not validate data types, enumerations, source references, or entity relationships.

Remedy: JSON Schemas for founder, company, evidence, source, contact, interview, score, portfolio, session, state, and checkpoint.

### C-03: No lineage-preserving evidence graph

Version 1 stores sources and claims conceptually but does not require claim-to-source-to-entity lineage. This permits entity mixing, duplicate sources, and unsupported narratives.

Remedy: evidence graph identifiers, source-family detection, entity resolution, alias detection, and claim validation.

### C-04: Contact rules are safe but not executable

The manual prohibits inference but lacks a deterministic contact-source classifier, freshness policy, escalation path, suppression list, and no-contact state.

Remedy: Contact Discovery Agent, contact-priority.yaml, contact schema, suppression logic, and outreach audit log.

### C-05: No bounded autonomy contract

Version 1 does not define what the agent may do independently, when it must stop, how it handles tool failure, or how it avoids unnecessary clarification questions.

Remedy: RUN_RESEARCH.md, execution budget, retry policy, stop conditions, and escalation-free assumptions.

## High findings

### H-01: Budgeting is absent

There are no token, query, tool-call, time, source, or candidate budgets. The agent can spend all resources on early candidates.

Remedy: explicit budget ledger with per-stage allocation and burn-rate alerts.

### H-02: Search expansion is not adaptive enough

The query model is good conceptually but does not specify mutation operators, saturation detection, novelty thresholds, or branch pruning.

Remedy: Query Engine with recursive expansion, mutation classes, source-family diversity, and saturation signals.

### H-03: Discovery and verification separation is aspirational

Roles are named but no independent evidence threshold or handoff contract prevents self-certification.

Remedy: stage contracts, immutable discovery records, verifier rejection rules, and red-team pass.

### H-04: Entity resolution is under-specified

The manual mentions exact entities but lacks name normalization, aliases, subsidiaries, mergers, acquisitions, founder transitions, or dormant-company logic.

Remedy: Entity Resolver and relationship graph.

### H-05: Portfolio optimization is manual

The 100-person mix is a target but there is no formal optimization, coverage heatmap, replacement rule, or marginal-value calculation.

Remedy: Portfolio Engine, portfolio-rules.yaml, diversity matrix, and automatic replacement.

### H-06: Financial analysis lacks timeline reconstruction

Funding and valuation guidance exists but cannot reconstruct rounds, ownership changes, acquisition events, or entity scope.

Remedy: timeline models, source precedence, and chronology validation.

### H-07: Quality assurance is a checklist, not a gate

QA has no blocking thresholds, defect taxonomy, automatic tests, or release artifact.

Remedy: QA module, quality-thresholds.yaml, validation report, and completion criteria.

### H-08: No progress visibility

There is no run dashboard, stage metrics, candidate funnel, coverage heatmap, or reason-coded discard log.

Remedy: progress tracker, metrics schema, and reports.

### H-09: No retry or failure taxonomy

Error recovery is narrative. It lacks retry count, backoff, alternate source strategy, dead-letter handling, and idempotency.

Remedy: retry-policy.yaml and Error Recovery module.

### H-10: Context-window risk is unmanaged

A 21,548-word manual plus source material can exceed context or cause the agent to lose invariant rules.

Remedy: context manifest, chunking, priority loading, rolling summaries, and invariant digest.

## Medium findings

### M-01: Duplication and ambiguity in scoring terms

Accessibility, contact quality, and reply probability overlap. Media saturation appears as a penalty but is not calibrated against educational value.

Remedy: canonical feature definitions and weighted scoring config.

### M-02: Search query library is broad but not performance-tracked

The query bank provides volume but no yield, freshness, source-type, or false-positive metrics.

Remedy: query telemetry and mutation engine.

### M-03: Industry playbooks are uneven

Some sectors have questions and red flags but not source inventories, metrics, vocabulary, or verification pathways.

Remedy: separate playbook contract for every industry.

### M-04: No explicit acquisition or dead-company detection

A company can be acquired, renamed, dissolved, merged, or inactive while appearing current in old pages.

Remedy: company lifecycle resolver and currentness checks.

### M-05: No relationship graph

Supplier, customer, partner, competitor, investor, and association relationships are not represented as first-class records.

Remedy: graph construction with relationship confidence and source edges.

### M-06: No automatic candidate replacement

When a final candidate fails QA, there is no deterministic replacement queue or portfolio rebalancing process.

Remedy: replacement algorithm and reserve pool.

### M-07: No self-critique protocol

Red-team questions are useful but no self-critique pass is required before ranking lock.

Remedy: mandatory critique artifact and score recalibration.

### M-08: No audit trail for score edits

The manual does not require immutable score history, actor, reason, or before/after values.

Remedy: append-only logger and score revision record.

### M-09: No privacy retention policy

Public information may still be sensitive. Retention, redaction, and deletion semantics are absent.

Remedy: data minimization, retention policy, and suppression state.

### M-10: No deterministic export contract

The final spreadsheet, report, source pack, and unresolved-items report are not specified as a release bundle.

Remedy: final validation and export manifest.

## Low findings

### L-01: Table of contents is not generated or validated.

### L-02: Versioning and change control are implied but not operationalized.

### L-03: Examples are useful but not executable fixtures.

### L-04: No distinction between source availability and source reliability in metrics.

### L-05: No explicit localization fallback when translation is uncertain.

## Duplicated or overlapping logic

- Accessibility is represented in contact hierarchy, accessibility score, and reply probability.
- Hidden-gem logic appears in discovery, ranking, and portfolio guidance without one canonical definition.
- Verification checklists recur in several chapters without a single gate implementation.
- Media saturation is both an exclusion rule and a numeric penalty without precedence.
- Contact freshness and source recency are described separately but need a common time policy.

## Architectural conclusion

Version 1 is an excellent human operating manual but not a production execution system. Version 2 must preserve its evidence-first philosophy while adding contracts, state, budgets, telemetry, recovery, lineage, and release gates. The files in this package implement that layer rather than rewriting the original.

## Audit acceptance criteria

The V2 package passes this audit when:

- Every stage has inputs, outputs, success criteria, failure modes, retries, dependencies, and examples.
- Every persisted object validates against JSON Schema.
- Every candidate has claim, source, and entity lineage.
- The run can resume from a checkpoint without repeating completed work.
- Budgets and retry policies are enforced.
- Portfolio, contact, quality, and completion gates are machine-checkable.
- Final export includes audit and unresolved-risk reports.

