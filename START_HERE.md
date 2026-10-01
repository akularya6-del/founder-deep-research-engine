# START HERE

## What this package is

This is the Version 2 execution package for autonomous founder research. The original deep-research-operating-manual.md remains the human-readable Version 1 source. This package adds machine-oriented contracts and execution controls.

## Installation

Copy the research-system directory into the Antigravity workspace. No external dependency is required for the documented operating model. If the agent supports JSON Schema validation, enable it. If not, perform the checks as structured self-validation and log that limitation.

## Load order

1. START_HERE.md.
2. RUN_RESEARCH.md.
3. manual/01_MASTER_MANUAL.md.
4. configs/*.yaml.
5. schemas/*.json.
6. relevant agent module.
7. relevant industry playbook.
8. prompts for the current stage.

Do not load every source or every query into context at once. Use the Context Window Strategy in RUN_RESEARCH.md.

## Execution order

INIT -> LANDSCAPE -> DISCOVERY -> QUALIFICATION -> VERIFICATION -> RELATIONSHIPS -> CONTACTS -> SCORING -> PORTFOLIO -> QA -> EXPORT.

## Resume

Load the latest valid checkpoint from state/checkpoints, verify artifact hashes, replay events after the checkpoint, mark interrupted tasks RETRYABLE, and continue from the earliest incomplete dependency.

## Checkpoints

Persist at initialization, after every batch, before final export, and after every error. Never overwrite the only checkpoint.

## Recovery

Classify errors, apply retry-policy.yaml, mutate the failing search dimension, quarantine invalid output, and continue with an alternate candidate when safe. Policy violations are never retried.

## Verification

Release only when schemas, claim lineage, contact legality, entity resolution, portfolio rules, and QA thresholds pass.

## Expected runtime and usage

The default budget is defined in configs/execution-budget.yaml. Actual runtime depends on source access, tool latency, language coverage, and the number of candidate branches. The controller must report actual usage rather than promise a fixed runtime.

## Known limitations

Public evidence can be stale or incomplete. Revenue and ownership may remain undisclosed. Search coverage may be language-biased. The system must report these limitations and never repair them with guesses.

## Live retrieval requirement

The active retrieval layer is in engine/real_retrieval.py, engine/evidence_store.py, and engine/integrity_gate.py. Configure Tavily, Firecrawl, or a self-hosted SearXNG endpoint before live search. If no provider is configured, the runner must stop with a configuration error. This is intentional: there is no synthetic fallback.

Run a retrieval smoke test with run_real_research.py --fetch https://example.com, then inspect sources/retrieved and logs/retrieval_events.jsonl. Do not mark a founder verified until retrieved source artifacts, exact excerpts, independent source families, and explicit contact evidence exist.
