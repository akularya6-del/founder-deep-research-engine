# Error Recovery

## Purpose

Classify failures, apply safe retries, quarantine bad work, and preserve forward progress.

## Error classes

- Transient: timeout, rate limit, temporary outage.
- Deterministic: schema violation, invalid config, malformed output.
- Data: entity conflict, stale source, missing evidence.
- Policy: privacy violation, inferred contact, disallowed access.
- Resource: token, query, time, or tool budget exhaustion.
- System: state corruption, missing module, logger failure.

## Recovery algorithm

1. Classify the error.
2. Record it with a stable error key.
3. Check idempotency.
4. Apply retry policy if eligible.
5. Change the failing dimension, not merely repeat.
6. Quarantine invalid output.
7. Notify controller of impact.
8. Continue with alternatives if safe.
9. Escalate to BLOCKED only when meaningful progress is impossible.

## Success criteria

No unsafe action is retried, no deterministic error loops, and every failed task has a final disposition.

## Dead-letter policy

After maximum attempts, place the task in dead-letter with error, inputs, attempted mutations, and recommended next action. The portfolio may use another candidate.

