from __future__ import annotations

import json
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from engine.integrity_gate import IntegrityFailure, assert_public_contact
from engine.real_retrieval import fetch_source


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def mx_records(domain: str) -> list[str]:
    """Return MX records without sending mail or probing a mailbox."""
    try:
        result = subprocess.run(["dig", "+short", "MX", domain], capture_output=True, text=True, timeout=8, check=False)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        return []


def domain_resolves(domain: str) -> bool:
    try:
        socket.getaddrinfo(domain, 443, type=socket.SOCK_STREAM)
        return True
    except socket.gaierror:
        return False


def recheck_contact(contact: dict, source: dict | None, root: Path, refetch: bool = True) -> dict:
    value = str(contact.get("value", "")).strip()
    result = {
        "contact_id": contact.get("contact_id"), "entity_id": contact.get("entity_id"), "value": value,
        "checked_at": datetime.now(timezone.utc).isoformat(), "source_id": contact.get("source_id"),
        "source_url": contact.get("source_url"), "checks": {}, "status": "failed",
        "mailbox_status": "not_tested", "notes": [],
    }
    result["checks"]["syntax"] = bool(EMAIL_RE.match(value))
    if not result["checks"]["syntax"]:
        result["notes"].append("Email value is not syntactically valid.")
        return result
    domain = value.rsplit("@", 1)[1].lower()
    source_host = (urlparse(str(contact.get("source_url", ""))).hostname or "").lower()
    result["domain"] = domain
    result["checks"]["domain_resolves"] = domain_resolves(domain)
    result["checks"]["mx_present"] = bool(mx_records(domain))
    result["checks"]["source_domain_related"] = domain == source_host or domain.endswith("." + source_host) or source_host.endswith("." + domain)
    if not result["checks"]["source_domain_related"]:
        result["notes"].append("Contact domain differs from the cited source hostname; review manually.")

    if source:
        source_text = source.get("text", "")
        result["checks"]["stored_source_present"] = bool(source_text)
        result["checks"]["exact_value_in_stored_source"] = value in source_text
        try:
            assert_public_contact(contact, source_text)
            result["checks"]["integrity_gate"] = True
        except IntegrityFailure as exc:
            result["checks"]["integrity_gate"] = False
            result["notes"].append(str(exc))
    else:
        result["checks"]["stored_source_present"] = False
        result["checks"]["exact_value_in_stored_source"] = False
        result["checks"]["integrity_gate"] = False

    if refetch and contact.get("source_url"):
        try:
            fresh = fetch_source(contact["source_url"])
            result["checks"]["live_source_reachable"] = fresh.http_status == 200
            result["checks"]["exact_value_in_live_source"] = value in fresh.text
            result["live_source_id"] = fresh.source_id
            result["live_content_hash"] = fresh.content_hash
        except Exception as exc:
            result["checks"]["live_source_reachable"] = False
            result["checks"]["exact_value_in_live_source"] = False
            result["notes"].append(f"Live source refetch failed: {exc}")
    else:
        result["checks"]["live_source_reachable"] = None
        result["checks"]["exact_value_in_live_source"] = None

    checks = result["checks"]
    if all(checks.get(key) is True for key in ("syntax", "domain_resolves", "mx_present", "exact_value_in_stored_source", "integrity_gate")):
        result["status"] = "public_route_verified"
        result["mailbox_status"] = "domain_accepts_mail; mailbox_unconfirmed"
    return result
