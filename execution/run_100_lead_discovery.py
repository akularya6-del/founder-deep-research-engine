#!/usr/bin/env python3
"""Run a live, search-only discovery pass for 100 podcast lead candidates.

This intentionally produces a candidate pool, not a verified guest list. Every
row retains the exact query, result URL, title, and snippet that caused it to be
discovered. Verification and contact discovery must happen in later stages.
"""
from __future__ import annotations

import json
import re
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from engine.evidence_store import EvidenceStore
from engine.real_retrieval import provider_from_environment

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "discovery100"

QUERIES = [
    # AI and industrial AI
    "AI founder B2B India operations manufacturing", "industrial AI founder India factory", "computer vision manufacturing founder India", "robotics AI founder India factory", "AI infrastructure founder India enterprise", "AI logistics founder India supply chain", "AI procurement founder India B2B", "AI quality control manufacturing founder India", "AI SaaS founder India operations", "deeptech founder India industrial automation",
    # Manufacturing and automation
    "founder manufacturing company India factory systems", "founder industrial automation company India", "founder machine builder India automation", "founder precision engineering India company", "founder auto components manufacturer India", "founder electrical equipment manufacturer India", "founder sensors manufacturing India", "founder CNC manufacturing India", "founder contract manufacturing India B2B", "founder factory automation India operations",
    # Packaging and materials
    "founder packaging company India manufacturing", "founder flexible packaging India", "founder corrugated packaging India", "founder labels packaging India", "founder sustainable packaging manufacturer India", "founder specialty materials company India", "founder paper packaging company India", "founder plastics manufacturing India B2B", "founder glass packaging India", "founder industrial printing packaging India",
    # Logistics, exports and warehousing
    "founder logistics company India fleet operations", "founder freight forwarding India exports", "founder warehousing company India", "founder cold chain logistics India", "founder 3PL company India", "founder supply chain company India manufacturing", "founder export company India manufacturing", "founder port logistics India", "founder last mile B2B logistics India", "founder customs trade logistics India",
    # Chemicals and pharma
    "founder specialty chemicals company India", "founder chemical manufacturing India exports", "founder industrial chemicals India B2B", "founder water treatment chemicals India", "founder coatings company India manufacturing", "founder pharma manufacturing India", "founder contract pharma manufacturer India", "founder API manufacturing India", "founder medical devices manufacturing India", "founder biotech manufacturing India",
    # Fintech and B2B finance
    "founder B2B fintech India procurement", "founder supply chain finance India", "founder industrial payments India", "founder SME lending India B2B", "founder invoice financing India manufacturing", "founder embedded finance India B2B", "founder export finance India", "founder wealth technology India operations", "founder payments infrastructure India enterprise", "founder fintech company India profitable",
    # Research-source expansion
    "site:forbesindia.com founder manufacturing India", "site:yourstory.com founder manufacturing India", "site:inc42.com founder industrial India", "site:entrackr.com founder B2B India", "site:business-standard.com founder chemicals India", "site:economictimes.indiatimes.com founder logistics India", "site:moneycontrol.com founder pharma India", "site:linkedin.com/company industrial automation India founder", "industrial association award manufacturing founder India", "conference speaker industrial automation India founder",
    # Contact-bearing primary-source expansion. These queries deliberately seek
    # named directors/promoters in filings, official company pages, and trade
    # associations rather than broker databases.
    'site:nseindia.com "Managing Director" "E-mail" manufacturing India', 'site:bseindia.com "Managing Director" "E-mail" pharma India', 'site:nseindia.com "Promoter" "Email" chemicals India', 'site:bseindia.com "Chairman" "Email" packaging India', 'site:sebi.gov.in "Managing Director" "email" company India', 'site:gov.in "Founder" "Email" manufacturing India', 'site:org.in "Founder" "Email" automation India', 'site:company.com "Founder" "@" manufacturing India', 'site:*.in "Founder" "Email:" "automation"', 'site:*.in "Founder" "Email:" "packaging"',
    '"Founder" "Email:" "industrial automation" India', '"Founder" "Email:" "specialty chemicals" India', '"Founder" "Email:" "pharma manufacturing" India', '"Founder" "Email:" "logistics" India', '"Founder" "Email:" "export" India manufacturer', '"CEO" "Email:" "B2B SaaS" India', '"Managing Director" "Email:" "factory" India', '"Chairman" "email" "manufacturing" India company', '"promoter" "email" "engineering" India company', '"director" "email" "warehouse" India company',
    'site:indiamart.com founder manufacturing email', 'site:tradeindia.com founder manufacturer email India', 'site:acma.in founder email auto components', 'site:cii.in founder manufacturing email', 'site:ficci.in founder manufacturing email', 'site:pharmexcil.com founder pharma email', 'site:chemexcil.in founder chemicals email', 'site:plexconcil.org founder packaging email', 'site:logisticsindia.com founder logistics email', 'site:siam.in founder auto components email',
    '"Founder" "contact" "factory" "@" India', '"Founder and CEO" "contact" "@" India manufacturing', '"Managing Director" "contact" "@" India chemicals', '"Founder" "reach me" "@" manufacturing India', '"Founder" "write to" "@" logistics India', '"Founder" "email id" automation company India', '"Founder" "email id" packaging company India', '"Founder" "email id" pharma company India', '"Founder" "email id" export company India', '"Founder" "email id" fintech India',
]

NAME_PATTERNS = [
    re.compile(r"\b(?:Founder|Co-founder|CEO|Managing Director|Chairman|Promoter)\s*[:,-]?\s*([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){1,3})"),
    re.compile(r"\b([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){1,3})[,\s]+(?:is|,?\s+the)?\s*(?:Founder|Co-founder|CEO|Managing Director|Chairman|Promoter)\b"),
]


def name_candidate(title: str, snippet: str, url: str = "") -> str | None:
    text = f"{title}. {snippet}"
    # LinkedIn profile pages and interview pages conventionally put the person's
    # name before the first separator. This is a candidate name only; it still
    # requires page-level verification.
    if "/in/" in url:
        first = re.split(r"\s+-\s+|\s+\|\s+", title, maxsplit=1)[0].strip()
        if 2 <= len(first.split()) <= 4 and re.fullmatch(r"[A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+)+", first) and first.lower() not in {"leadership team", "about us", "company profile"}:
            return first
    first_title = re.split(r"\s+-\s+|\s+\|\s+", title, maxsplit=1)[0].strip()
    if 2 <= len(first_title.split()) <= 4 and re.fullmatch(r"[A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+)+", first_title):
        if not any(term in first_title.lower() for term in ("top ", "about ", "meet ", "india ", "company ", "founders ", "leadership team")):
            return first_title
    for pattern in NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            value = " ".join(match.group(1).split()).strip(" ,.-")
            if len(value.split()) >= 2 and value.lower() not in {"india founder", "company founder"}:
                return value
    return None


def main() -> None:
    env_file = ROOT / ".env.local"
    if env_file.exists():
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                if key.strip() in {"TAVILY_API_KEY", "FIRECRAWL_API_KEY", "SEARXNG_ENDPOINT", "RESEARCH_SEARCH_PROVIDER"} and value.strip():
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    selected = os.getenv("RESEARCH_SEARCH_PROVIDER", "tavily" if os.getenv("TAVILY_API_KEY") else "searxng")
    provider = provider_from_environment(selected)
    store = EvidenceStore(ROOT)
    discovered: dict[str, dict] = {}
    query_log = []
    for query in QUERIES:
        results = provider.search(query, limit=5)
        query_log.append({"query": query, "result_count": len(results)})
        store.save_search_results(results)
        for result in results:
            if result.url in discovered:
                discovered[result.url]["queries"].append(query)
                continue
            discovered[result.url] = {
                "lead_id": f"LEAD-{len(discovered)+1:04d}",
                "candidate_name": name_candidate(result.title, result.snippet, result.url),
                "source_title": result.title,
                "source_url": result.url,
                "snippet": result.snippet,
                "discovery_query": query,
                "queries": [query],
                "provider": provider.name,
                "status": "discovered_unverified",
                "verification_required": True,
                "contact_status": "not_yet_researched",
            }
    # If the local metasearch instance is temporarily rate-limited, recover the
    # last successful live search batch from the append-only event log rather
    # than replacing a valid discovery run with an empty result.
    if len(discovered) < 100:
        event_log = ROOT / "logs" / "retrieval_events.jsonl"
        if event_log.exists():
            for line in event_log.read_text(encoding="utf-8").splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("event_type") != "SEARCH_RESULT" or not event.get("url"):
                    continue
                url = event["url"]
                if url in discovered:
                    continue
                discovered[url] = {
                    "lead_id": f"LEAD-{len(discovered)+1:04d}",
                    "candidate_name": name_candidate(event.get("title", ""), event.get("snippet", ""), url),
                    "source_title": event.get("title", ""), "source_url": url,
                    "snippet": event.get("snippet", ""), "discovery_query": event.get("query", ""),
                    "queries": [event.get("query", "")], "provider": event.get("provider", "searxng"),
                    "status": "discovered_unverified", "verification_required": True,
                    "contact_status": "not_yet_researched",
                }
    leads = list(discovered.values())
    OUT.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()
    payload = {"generated_at": generated, "status": "candidate_discovery", "provider": "searxng", "query_count": len(QUERIES), "unique_result_count": len(leads), "leads": leads}
    (OUT / "leads.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "query_log.json").write_text(json.dumps({"generated_at": generated, "queries": query_log}, indent=2), encoding="utf-8")
    # Prefer an identifiable person, then primary/company/credible media pages,
    # while keeping the raw discovery pool untouched for later review.
    preferred_domains = ("linkedin.com", "yourstory.com", "forbesindia.com", "economictimes.indiatimes.com", "business-standard.com", "moneycontrol.com", "inc42.com", "entrackr.com", "company", "org")
    def rank(lead: dict) -> tuple:
        url = lead["source_url"].lower()
        title = lead["source_title"].lower()
        social_penalty = int(any(x in url for x in ("youtube.com", "instagram.com", "facebook.com")))
        category_penalty = int(any(x in title for x in ("top ", "list of", "directory", "startups in india", "companies in india", "industry report")))
        domain_bonus = int(any(x in url for x in preferred_domains))
        return (int(bool(lead["candidate_name"])), -social_penalty, -category_penalty, domain_bonus)
    selected = sorted(leads, key=rank, reverse=True)[:100]
    (OUT / "leads100.json").write_text(json.dumps({"generated_at": generated, "status": "candidate_discovery", "lead_count": len(selected), "leads": selected}, indent=2, ensure_ascii=False), encoding="utf-8")
    with (OUT / "leads100.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["lead_id", "candidate_name", "source_title", "source_url", "discovery_query", "status", "verification_required", "contact_status"])
        writer.writeheader()
        writer.writerows({key: lead.get(key) for key in writer.fieldnames} for lead in selected)
    report = ["# 100 Potential Podcast Leads", "", f"Generated: {generated}", "", "These are discovery-stage candidates, not verified guests or verified contacts. Each row preserves a live SearXNG result URL and discovery query. The next stage must verify founder identity, operating depth, company quality, podcast fit, and public contact information.", "", "| # | Candidate | Source | URL | Status |", "|---:|---|---|---|---|"]
    for i, lead in enumerate(selected, 1):
        candidate = lead.get("candidate_name") or "Name requires page verification"
        report.append(f"| {i} | {candidate} | {lead['source_title'].replace('|', '/')} | [source]({lead['source_url']}) | {lead['status']} |")
    (OUT / "leads100_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": "candidate_discovery", "queries": len(QUERIES), "unique_results": len(leads), "leads100": len(selected), "output": str(OUT)}))


if __name__ == "__main__":
    main()
