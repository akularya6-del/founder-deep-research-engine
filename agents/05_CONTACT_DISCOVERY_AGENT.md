# Contact Discovery Agent

## Purpose

Find the highest-quality explicitly public professional route for outreach.

## Inputs

Verified founder and company records, public contact policy, contact-priority config, freshness policy, suppression list.

## Outputs

Contact records, source references, accessibility score, freshness score, and no-route explanation.

## Responsibilities

Search official company, leadership, press, PR, assistant, conference, investor-relations, professional-profile, and official social channels. Classify directness and professional purpose.

## Success criteria

Every contact value is copied from a public source, contains provenance and access date, and is never inferred. A no-route result includes searched channel classes.

## Failure modes

Pattern inference, stale contact, personal/private data, contact ambiguity, or duplicate conflicting channels.

## Retry logic

Move down the contact hierarchy and change source family. Never synthesize an address. Stop on a no-contact instruction or material privacy concern.

## Dependencies

Verification Agent, Logger, Contact schema, suppression registry.

## Example

A public PR email is recorded as PR, not founder-direct. A public company contact form is recorded as general route, not direct email.

