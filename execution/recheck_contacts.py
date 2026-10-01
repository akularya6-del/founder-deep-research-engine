#!/usr/bin/env python3
"""Recheck public contact routes without sending email."""
from __future__ import annotations

import json
from pathlib import Path

from engine.contact_rechecker import recheck_contact

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "pilot10"
SOURCES = ROOT / "sources" / "retrieved"


def source_lookup() -> dict[str, dict]:
    lookup = {}
    for path in SOURCES.glob("SRC-*.json"):
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if source.get("source_id"):
            lookup[source["source_id"]] = source
    return lookup


def main() -> None:
    contacts = json.loads((RESULTS / "contacts.json").read_text(encoding="utf-8"))["contacts"]
    sources = source_lookup()
    checks = [recheck_contact(contact, sources.get(contact.get("source_id")), ROOT) for contact in contacts]
    payload = {"status": "rechecked", "mailbox_testing": "not_performed", "checks": checks}
    (RESULTS / "contact_recheck.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    verified = sum(item["status"] == "public_route_verified" for item in checks)
    print(json.dumps({"status": "rechecked", "contacts": len(checks), "public_routes_verified": verified, "mailboxes_confirmed": 0, "output": str(RESULTS / 'contact_recheck.json')}))


if __name__ == "__main__":
    main()
