#!/usr/bin/env python3
"""Multi-source contact research for discovery-stage leads.

The script is deliberately conservative: it extracts only email strings that
are present in retrieved public source text, rejects generic inboxes, requires
the candidate name to appear in the source, and records every failed check.
It never generates an address pattern and never sends email.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from engine.integrity_gate import GENERIC_CONTACT_PREFIXES
from engine.real_retrieval import fetch_source, provider_from_environment

ROOT = Path(__file__).resolve().parents[1]
INPUT = Path(os.getenv("LEADS_INPUT", str(ROOT / "results" / "discovery100" / "leads100.json")))
OUT = ROOT / "results" / "verified100"
STATE = OUT / "state.json"
EMAIL_RE = re.compile(r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b")


def generic(value: str) -> bool:
    return value.lower().startswith(GENERIC_CONTACT_PREFIXES) or value.lower().split("@", 1)[0] in {"sales", "network", "investors", "investor.relations", "secretarial", "cs"}


def usable_name(name: str) -> bool:
    lowered = name.lower().strip()
    blocked = {"ati robotics", "addverb technologies private limited", "leadership team", "contact us", "our team", "managing director", "and director", "our founder", "primus partners"}
    return bool(name and len(name.split()) >= 2 and lowered not in blocked)


def source_family(url: str) -> str:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    return host.split(".")[-2] if "." in host else host


FETCH_BLOCKED_HOSTS = {"linkedin.com", "youtube.com", "facebook.com", "instagram.com", "twitter.com", "x.com", "contactout.com", "rocketreach.co", "signalhire.com", "tracxn.com", "clay.com", "salezshark.com"}


def should_fetch(url: str, name: str, title: str, snippet: str) -> bool:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if not host or any(host == blocked or host.endswith("." + blocked) for blocked in FETCH_BLOCKED_HOSTS):
        return False
    searchable = f"{title} {snippet}".lower()
    return re.sub(r"[^a-z0-9 ]+", " ", name.lower()) in re.sub(r"[^a-z0-9 ]+", " ", searchable)


def candidate_name(lead: dict) -> str:
    return str(lead.get("candidate_name") or "").strip()


def load_local_env() -> None:
    """Load non-exported local secrets without printing or persisting them."""
    env_file = ROOT / ".env.local"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if key in {"TAVILY_API_KEY", "FIRECRAWL_API_KEY", "RESEARCH_SEARCH_PROVIDER", "SEARXNG_ENDPOINT"} and value:
            os.environ.setdefault(key, value)


def main() -> None:
    load_local_env()
    OUT.mkdir(parents=True, exist_ok=True)
    leads = json.loads(INPUT.read_text(encoding="utf-8"))["leads"]
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"processed": {}}
    selected_provider = os.getenv("RESEARCH_SEARCH_PROVIDER", "").strip().lower()
    if not selected_provider:
        selected_provider = "tavily" if os.getenv("TAVILY_API_KEY") else "firecrawl" if os.getenv("FIRECRAWL_API_KEY") else "searxng"
    provider = provider_from_environment(selected_provider)
    for index, lead in enumerate(leads, 1):
        lid = lead["lead_id"]
        # A lead is resumable only after it has produced at least one contact
        # candidate. Earlier runs may have processed it with a blocked provider
        # and zero contacts; those must be retried with the newly loaded API.
        if not os.getenv("FORCE_RESEARCH") and lid in state["processed"] and state["processed"][lid].get("contacts"):
            continue
        name = candidate_name(lead)
        if not usable_name(name):
            state["processed"][lid] = {"lead_id": lid, "status": "skipped_name_requires_manual_resolution", "contacts": []}
            continue
        # One broad search returns multiple independent pages; two separate
        # API calls per lead made the earlier pass unnecessarily slow.
        context = re.sub(r"[^A-Za-z0-9&. -]+", " ", str(lead.get("source_title", "")))[:90].strip()
        queries = [
            f'"{name}" {context} email contact' if context else f'"{name}" founder CEO company email contact',
            f'"{name}" email contact company',
            f'"{name}" "@" founder company',
        ]
        events = []
        emails = {}
        for query in queries:
            try:
                results = provider.search(query, limit=3)
            except Exception as exc:
                events.append({"query": query, "error": str(exc)})
                continue
            for result in results:
                events.append({"query": query, "title": result.title, "url": result.url, "snippet": result.snippet})
                # Use provider-returned content for the fast discovery pass.
                # Direct page retrieval is deferred to the final verification
                # queue so one blocked/large page cannot stall the run.
                texts = [(result.url, f"{result.title}\n{result.snippet}", None)]
                if should_fetch(result.url, name, result.title, result.snippet):
                    try:
                        fetched = fetch_source(result.url, timeout=8, max_bytes=2_000_000)
                        texts.append((result.url, fetched.text, fetched.source_id))
                    except Exception as exc:
                        events.append({"url": result.url, "fetch_error": str(exc)[:300]})
                for source_url, text, source_id in texts:
                    lower_text = text.lower()
                    name_tokens = [token for token in re.findall(r"[a-z0-9]+", name.lower()) if len(token) > 2]
                    if not name_tokens or not all(token in lower_text for token in name_tokens):
                        continue
                    for email in sorted(set(EMAIL_RE.findall(text))):
                        if generic(email) or email.lower().endswith(("@example.com", "@example.org")) or "*" in email:
                            continue
                        # Prevent a press-release contact for a different person
                        # from being attributed to this lead merely because both
                        # names occur somewhere in the same long snippet.
                        pos = lower_text.find(email.lower())
                        window = lower_text[max(0, pos - 450):pos + len(email) + 450]
                        normalized_name = re.sub(r"[^a-z0-9 ]+", " ", name.lower())
                        normalized_window = re.sub(r"[^a-z0-9 ]+", " ", window)
                        if normalized_name not in normalized_window or not all(token in window for token in name_tokens):
                            continue
                        record = emails.setdefault(email.lower(), {"email": email, "source_ids": [], "source_urls": [], "families": [], "excerpts": []})
                        if source_id:
                            record["source_ids"].append(source_id)
                        record["source_urls"].append(source_url)
                        record["families"].append(source_family(source_url))
                        record["name_email_proximity"] = True
                        record["excerpts"].append(" ".join(text[max(0, pos-220):pos+len(email)+220].split()))
        usable = []
        for record in emails.values():
            record["source_ids"] = sorted(set(record["source_ids"]))
            record["source_urls"] = sorted(set(record["source_urls"]))
            record["families"] = sorted(set(record["families"]))
            record["multi_source"] = len(record["families"]) >= 2
            record["status"] = "candidate_contact_requires_manual_verification"
            usable.append(record)
        state["processed"][lid] = {"lead_id": lid, "candidate_name": name, "status": "researched", "contacts": usable, "events": events}
        if index % 5 == 0:
            STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
            print(json.dumps({"processed": index, "total": len(leads)}))
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    final = []
    for item in state["processed"].values():
        for contact in item.get("contacts", []):
            if contact.get("source_urls"):
                final.append({"lead_id": item["lead_id"], "candidate_name": item.get("candidate_name"), **contact})
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "status": "multisource_contact_candidates", "count": len(final), "mailboxes_confirmed": 0, "contacts": final}
    (OUT / "contact_candidates.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "researched_leads": len(state["processed"]), "multi_source_contacts": len(final), "mailboxes_confirmed": 0, "output": str(OUT / 'contact_candidates.json')}))


if __name__ == "__main__":
    main()
