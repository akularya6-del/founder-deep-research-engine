#!/usr/bin/env python3
"""Attach an independent identity source to contact-source candidates."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LEADS = ROOT / "results" / "discovery100" / "leads100.json"
STATE = ROOT / "results" / "verified100" / "state.json"
OUT = ROOT / "results" / "verified100" / "contact_candidates.json"


def family(url: str) -> str:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    return host.split(".")[-2] if "." in host else host


def main() -> None:
    leads = {x["lead_id"]: x for x in json.loads(LEADS.read_text(encoding="utf-8"))["leads"]}
    state = json.loads(STATE.read_text(encoding="utf-8"))
    for lid, item in state.get("processed", {}).items():
        lead = leads.get(lid)
        if not lead or not item.get("contacts"):
            continue
        identity_url = lead.get("source_url", "")
        identity_text = " ".join([str(lead.get("source_title", "")), str(lead.get("snippet", ""))])
        name = str(item.get("candidate_name") or "").lower()
        identity_ok = bool(name and name in identity_text.lower())
        if not identity_ok:
            continue
        for contact in item["contacts"]:
            urls = set(contact.get("source_urls", []))
            families = set(contact.get("families", []))
            urls.add(identity_url)
            families.add(family(identity_url))
            contact["identity_source_url"] = identity_url
            contact["identity_source_id"] = "discovery_result"
            contact["identity_excerpt"] = " ".join(identity_text.split())[:1000]
            contact["identity_source_name_match"] = True
            contact["source_urls"] = sorted(urls)
            contact["families"] = sorted(families)
            contact["multi_source"] = len(families) >= 2
            if contact["multi_source"]:
                contact["status"] = "two_source_identity_and_contact_verified"
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    final = []
    for item in state.get("processed", {}).values():
        for contact in item.get("contacts", []):
            if contact.get("multi_source"):
                final.append({"lead_id": item["lead_id"], "candidate_name": item.get("candidate_name"), **contact})
    OUT.write_text(json.dumps({"status": "two_source_identity_and_contact_candidates", "count": len(final), "mailboxes_confirmed": 0, "contacts": final}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "two_source_identity_and_contact_candidates", "contacts": len(final), "mailboxes_confirmed": 0, "output": str(OUT)}))


if __name__ == "__main__":
    main()
