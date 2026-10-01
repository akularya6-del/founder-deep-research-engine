# Logger

## Purpose

Create an append-only, queryable audit trail for decisions, evidence, tool calls, budgets, errors, and state changes.

## Inputs

Structured events from every module.

## Outputs

JSONL event log, human-readable run summary, metrics rollup, and audit index.

## Required event fields

Event ID, run ID, timestamp, actor, stage, event type, severity, candidate or entity IDs, input artifact IDs, output artifact IDs, message, and schema version.

## Responsibilities

Log before and after risky actions, record retries and reasons, attach source IDs, record score revisions, and protect sensitive fields through minimization.

## Success criteria

Any final fact, score, replacement, or state transition can be traced to an event chain.

## Failure modes

Logger unavailable, malformed event, clock inconsistency, or sensitive-data leakage.

## Retry logic

Buffer non-critical events, retry bounded times, then emit a logger-degraded alert. Never fabricate missing events.

