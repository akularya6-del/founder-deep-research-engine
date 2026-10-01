from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SYNTHETIC_MARKERS = (
    "press-release-2026",
    "SRC-SEC-",
    "press@",
    "office@",
    "ir@",
    "synthetic fallback",
    "generated candidate",
    "generated claim",
    "fabricated run",
)

GENERIC_CONTACT_PREFIXES = (
    "info@", "contact@", "hello@", "admin@", "support@", "office@", "press@", "media@",
)


class IntegrityFailure(RuntimeError):
    pass


def assert_no_synthetic_text(value: str) -> None:
    lowered = value.lower()
    if any(marker.lower() in lowered for marker in SYNTHETIC_MARKERS):
        raise IntegrityFailure("Synthetic/generated marker detected in active research artifact.")


def assert_public_contact(contact: dict[str, Any], source_text: str) -> None:
    if contact.get("inferred") is not False:
        raise IntegrityFailure("Contact is not explicitly marked inferred=false.")
    if contact.get("public_purpose") is not True:
        raise IntegrityFailure("Contact is not explicitly marked for professional public use.")
    value = str(contact.get("value", "")).strip()
    if not value or value not in source_text:
        raise IntegrityFailure("Contact value does not appear verbatim in its cited source.")
    if value.lower().startswith(GENERIC_CONTACT_PREFIXES):
        raise IntegrityFailure("Generic inbox is not an acceptable primary outreach contact.")


def assert_claim(claim: dict[str, Any], source_lookup: dict[str, dict[str, Any]]) -> None:
    if claim.get("directness") == "inferred":
        raise IntegrityFailure("Inferred claim cannot be verified.")
    if not claim.get("exact_excerpt"):
        raise IntegrityFailure("Claim has no exact source excerpt.")
    for source_id in claim.get("source_ids", []):
        source = source_lookup.get(source_id)
        if not source:
            raise IntegrityFailure(f"Claim references missing source: {source_id}")
        if claim["exact_excerpt"] not in source.get("text", ""):
            raise IntegrityFailure(f"Claim excerpt missing from source: {source_id}")
        assert_no_synthetic_text(json.dumps(source))


def assert_candidate(candidate: dict[str, Any], claims: list[dict[str, Any]], source_lookup: dict[str, dict[str, Any]], contacts: list[dict[str, Any]]) -> None:
    if candidate.get("status") != "verified":
        raise IntegrityFailure("Candidate is not in verified status.")
    candidate_claims = [claim for claim in claims if candidate["founder_id"] in claim.get("entity_ids", []) or candidate.get("company_id") in claim.get("entity_ids", [])]
    if len(candidate_claims) < 2:
        raise IntegrityFailure("Verified candidate needs at least two claim records.")
    for claim in candidate_claims:
        assert_claim(claim, source_lookup)
    for contact in contacts:
        if contact.get("entity_id") == candidate["founder_id"]:
            source = source_lookup.get(contact.get("source_id"))
            if not source:
                raise IntegrityFailure("Contact references missing source.")
            assert_public_contact(contact, source.get("text", ""))
