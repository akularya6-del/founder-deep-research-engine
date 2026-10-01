# State Manager

## Purpose

Persist run state, checkpoints, memory, task statuses, and resumable progress.

## Inputs

State schema, transition policy, artifacts, controller events, and prior checkpoint.

## Outputs

Current state, checkpoint snapshots, recovery plan, and resume manifest.

## State principles

Updates are append-only events plus a materialized current state. Every task has status, attempts, timestamps, dependencies, inputs, outputs, and idempotency key. Completed work is never repeated unless invalidated by a dependency change.

## Checkpoint trigger

Persist at initialization, after each stage, after each batch, before risky operations, on budget alerts, on error, and before final export.

## Resume logic

Load the latest valid checkpoint, verify artifact hashes, replay events after the checkpoint, mark interrupted tasks as RETRYABLE, and resume at the earliest incomplete dependency.

## Failure modes

Corrupt checkpoint, incompatible schema version, missing artifact, split-brain status, or stale lock.

## Retry logic

Select the latest valid checkpoint, quarantine corrupt artifacts, and create a recovery event. Never overwrite the only checkpoint.

