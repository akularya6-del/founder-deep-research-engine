# Quality Assurance

## Purpose

Block unreliable, incomplete, inconsistent, or unsafe output before release.

## Inputs

All records, schemas, source ledger, score history, portfolio, contacts, logs, and configs.

## Outputs

Validation report, defect list, red-team report, completion decision, and release manifest.

## Checks

Schema validity; duplicate identity; source coverage; source-family independence; claim lineage; currentness; contact legality; score rationale; media saturation; category mix; portfolio concentration; unresolved conflicts; and export completeness.

## Blocking defects

Fabricated or inferred contact; unsupported material claim; unresolved identity collision; dead company presented as current; missing primary source; schema failure; or undisclosed exception.

## Success criteria

Zero blocking defects, all high-severity defects resolved or explicitly quarantined, and completion criteria pass.

## Failure modes

False negative, stale source, validator disagreement, or partial export.

## Retry logic

Route defects to the originating agent with a defect ID. Re-run only affected checks, then run a final full pass.

