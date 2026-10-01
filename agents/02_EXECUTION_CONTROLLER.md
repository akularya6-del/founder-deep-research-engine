# Execution Controller

## Purpose

Orchestrate the autonomous run, enforce state transitions and budgets, dispatch stage modules, and produce a resumable execution.

## Inputs

Master manual, configs, schemas, prior state if resuming, current date, available tools, and optional seed context.

## Outputs

Run manifest, state transitions, dispatch records, budget ledger, checkpoints, progress report, and final handoff.

## Responsibilities

Initialize the session; load the invariant digest; validate configs; allocate budgets; dispatch agents in dependency order; enforce concurrency; quarantine invalid outputs; request retries; trigger replacements; run checkpoint persistence; and stop only at COMPLETE, SATURATED, BLOCKED, or FAILED.

## Execution algorithm

1. Load START_HERE and the master manual.
2. Validate all configuration files.
3. Load or create state.
4. Allocate budget by phase and reserve recovery budget.
5. Run landscape mapping.
6. Run parallel discovery branches.
7. Gate and deduplicate candidates.
8. Dispatch independent verification.
9. Build relationship graph and source families.
10. Research contacts only for qualified candidates.
11. Score, critique, and optimize portfolio.
12. Run QA and replacement loop.
13. Export results and reports.

## Success criteria

All transitions are legal, every dispatched task has an idempotency key, budgets never go negative, and a checkpoint exists after each completed stage.

## Failure modes

Invalid config, missing module, schema failure, budget exhaustion, repeated tool failure, corrupted state, or conflicting terminal status.

## Retry logic

Retry transient failures according to retry-policy.yaml. Do not retry deterministic schema failures unchanged. After the maximum attempts, move the task to dead-letter and continue with alternatives where safe.

## Dependencies

State Manager, Logger, Error Recovery, all stage agents, schemas, and configs.

## Example dispatch envelope

    run_id:
    task_id:
    stage:
    candidate_ids:
    input_artifact_ids:
    budget_slice:
    attempt:
    idempotency_key:
    deadline:

