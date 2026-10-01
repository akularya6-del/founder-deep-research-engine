#!/usr/bin/env python3
"""Apply the final no-bluff acceptance filter to multi-source candidates."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "verified100" / "contact_candidates.json"
OUT = ROOT / "results" / "verified100" / "final_strict_contacts.json"
REJECTED = ROOT / "results" / "verified100" / "rejected_contacts.json"

BAD_HOSTS = {"contactout", "rocketreach", "signalhire", "growjo", "adapt", "people", "zoominfo", "apollo", "lusha", "crunchbase"}
NON_PRIMARY_HOSTS = {"linkedin.com", "yahoo.com", "youtube.com", "facebook.com", "instagram.com", "x.com", "twitter.com", "naukri.com", "indeed.com", "glassdoor.com"}
GENERIC_LOCAL = {"info", "contact", "hello", "admin", "support", "office", "press", "media", "sales", "network", "investors", "investor.relations", "secretarial", "cs", "corporate", "hi", "ad", "connect", "emailyogi", "firstname", "lastname", "firstname.lastname", "name", "careers", "investor", "prealert", "ask", "rkscomplianceteam"}
BROKER_HOSTS = {"salezshark", "tracxn", "clay", "founderthesis", "adtechtoday", "ibef", "wikipedia"}
ACADEMIC_DOMAINS = {"mit.edu", "uconn.edu", "cam.ac.uk", "ucla.edu", "yahoo.co.in", "gmail.com", "hotmail.com", "outlook.com"}


def host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def is_primary_source(url: str) -> bool:
    h = host(url)
    return bool(h) and not any(bad in h for bad in BAD_HOSTS) and not any(h == x or h.endswith("." + x) for x in NON_PRIMARY_HOSTS)


def accept(item: dict) -> tuple[bool, list[str]]:
    reasons = []
    email = item.get("email", "").lower()
    local, _, domain = email.partition("@")
    hosts = {host(url) for url in item.get("source_urls", [])}
    families = set(item.get("families", []))
    if not re.fullmatch(r"[^\s@*]+@[^\s@*]+\.[^\s@*]+", email): reasons.append("invalid_or_masked_email")
    if local in GENERIC_LOCAL: reasons.append("generic_role_inbox")
    if domain in {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"} and not any(is_primary_source(url) for url in item.get("source_urls", [])): reasons.append("personal_email_from_non_primary_directory")
    if any(domain == academic or domain.endswith("." + academic) for academic in ACADEMIC_DOMAINS if academic not in {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}): reasons.append("academic_or_non_business_address")
    if any(any(bad in h for bad in BAD_HOSTS | BROKER_HOSTS) for h in hosts): reasons.append("third_party_contact_database_or_unrelated_directory")
    if any("/goto?" in url for url in item.get("source_urls", [])): reasons.append("redirect_url_not_source")
    if not any(is_primary_source(url) for url in item.get("source_urls", [])): reasons.append("no_primary_source")
    if not item.get("multi_source"): reasons.append("not_two_source")
    if not item.get("name_email_proximity"):
        reasons.append("name_not_proximate_to_email")
    name = str(item.get("candidate_name") or "").lower()
    excerpts = " ".join(item.get("excerpts", [])).lower()
    if name and name not in excerpts:
        reasons.append("full_name_not_in_email_evidence")
    name_tokens = [t for t in re.findall(r"[a-z0-9]+", name) if len(t) >= 3]
    if not name_tokens or not any(t in local for t in name_tokens):
        reasons.append("email_local_part_not_person_linked")
    if not item.get("excerpts") or not any(email in excerpt.lower() for excerpt in item.get("excerpts", [])):
        reasons.append("email_not_present_in_evidence_excerpt")
    return not reasons, reasons


def main() -> None:
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    accepted, rejected = [], []
    for item in data.get("contacts", []):
        ok, reasons = accept(item)
        if ok:
            accepted.append({**item, "status": "strict_public_contact_verified", "mailbox_status": "domain_accepts_mail_mailbox_unconfirmed"})
        else:
            rejected.append({**item, "status": "rejected", "rejection_reasons": reasons})
    OUT.write_text(json.dumps({"status": "strict_final", "verified_count": len(accepted), "mailboxes_confirmed": 0, "contacts": accepted}, indent=2, ensure_ascii=False), encoding="utf-8")
    REJECTED.write_text(json.dumps({"status": "rejected_by_final_gate", "rejected_count": len(rejected), "contacts": rejected}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "strict_final", "verified_count": len(accepted), "rejected_count": len(rejected), "mailboxes_confirmed": 0}))


if __name__ == "__main__":
    main()
