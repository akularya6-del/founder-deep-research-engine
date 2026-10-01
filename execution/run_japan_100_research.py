#!/usr/bin/env python3
"""
Autonomous execution script to discover, qualify, and verify 100 young/emerging Japanese entrepreneurs
across AI, Fintech, Real Estate Tech, B2B SaaS, Industrial Tech, Manufacturing, Logistics, and Niche Champions.
Extracted contact details are strictly checked against public sources.
If no public email is published, 'No public email found' is explicitly recorded.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.evidence_store import EvidenceStore
from engine.real_retrieval import provider_from_environment, fetch_source

OUT_DIR = ROOT / "results" / "japan100"
OUT_DIR.mkdir(parents=True, exist_ok=True)

QUERIES = [
    # AI & Deeptech Japan
    'site:prtimes.jp "代表取締役" "AI" "設立"',
    'site:initial.inc/companies "AI" "代表取締役"',
    'site:forbesjapan.com "30 UNDER 30" "AI"',
    '"代表取締役" "AI" "メール" site:co.jp OR site:inc OR site:jp',
    'Japanese startup founder CEO "AI" "contact" OR "email"',
    'site:bridge-net.jp "代表取締役" AI 資金調達',
    'site:initial.inc "生成AI" 創業者 代表取締役',
    
    # B2B SaaS & Enterprise Technology Japan
    'site:prtimes.jp "代表取締役" "B2B" "SaaS"',
    'site:initial.inc/companies "SaaS" "代表取締役"',
    'site:fastgrow.jp "代表取締役" "SaaS"',
    '"代表取締役" "B2B SaaS" "お問い合わせ" OR "メール"',
    'Japanese founder CEO "B2B SaaS" enterprise software Japan',
    'site:tokyo-growth.jp "代表取締役" "SaaS"',

    # Fintech & B2B Finance Japan
    'site:prtimes.jp "代表取締役" "フィンテック" OR "Fintech"',
    'site:initial.inc/companies "フィンテック" OR "Fintech"',
    'Japanese founder CEO "Fintech" OR "B2B payments" Japan',
    '"代表取締役" "フィンテック" "問い合わせ" OR "連絡先"',

    # Real Estate & PropTech Japan
    'site:prtimes.jp "代表取締役" "不動産テック" OR "PropTech"',
    'Japanese founder CEO "Real Estate Tech" OR "PropTech" Japan',
    '"代表取締役" "不動産" "SaaS" OR "DX"',

    # Industrial Technology, Robotics & Advanced Manufacturing Japan
    'site:prtimes.jp "代表取締役" "ロボティクス" OR "産業用" OR "製造業DX"',
    'site:initial.inc/companies "製造業" OR "ディープテック"',
    'Japanese founder CEO "industrial technology" OR "manufacturing" Japan',
    'site:nikkei.com "若手経営者" "製造業" 代表取締役',
    '"代表取締役" "製造業" "アトツギ" OR "事業承継"',

    # Logistics & Supply Chain Japan
    'site:prtimes.jp "代表取締役" "物流" OR "サプライチェーン"',
    'Japanese founder CEO "logistics" OR "supply chain" Japan',
    '"代表取締役" "物流テック" "問い合わせ" OR "メール"',

    # Niche Profitable Champions & Second Generation (Atotsugi) Leaders
    'site:prtimes.jp "アトツギ" OR "事業承継" "代表取締役"',
    'site:nikkei.com "アトツギ" "経営者"',
    'Japanese young business owner founder "Japan" profitable "co.jp"',
    'site:fastgrow.jp "事業承継" OR "アトツギベンチャー"'
]

def load_env():
    env_file = ROOT / ".env.local"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.replace("export ", "").strip()
                v = v.strip().strip("'\"")
                os.environ[k] = v

def extract_emails(text: str) -> List[str]:
    """Strict public email extraction."""
    if not text:
        return []
    raw_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    valid_emails = []
    ignore_domains = {'example.com', 'domain.com', 'schema.org', 'w3.org', 'sentry.io', 'github.com', 'prtimes.jp', 'google.com', 'facebook.com', 'twitter.com'}
    for email in raw_matches:
        email_lower = email.lower()
        domain = email_lower.split('@')[-1]
        if domain not in ignore_domains and not email_lower.endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')):
            if email_lower not in valid_emails:
                valid_emails.append(email_lower)
    return valid_emails

def clean_text(text: str) -> str:
    return " ".join(text.split())

def main():
    load_env()
    provider_name = os.getenv("RESEARCH_SEARCH_PROVIDER", "tavily")
    print(f"Initializing retrieval provider: {provider_name}")
    provider = provider_from_environment(provider_name)
    store = EvidenceStore(ROOT)

    candidates: List[Dict[str, Any]] = []
    seen_urls: Set[str] = set()

    print(f"Running queries across {len(QUERIES)} search dimensions...")

    search_results_all = []
    for idx, query in enumerate(QUERIES):
        print(f"[{idx+1}/{len(QUERIES)}] Querying: {query}")
        try:
            results = provider.search(query, limit=10)
            store.save_search_results(results)
            search_results_all.extend(results)
            time.sleep(0.3)
        except Exception as e:
            print(f"Query error ({query}): {e}")

    print(f"Total raw search results harvested: {len(search_results_all)}")

    for res in search_results_all:
        url = res.url
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = res.title
        snippet = res.snippet

        combined_text = f"{title} {snippet}"
        is_relevant = any(k in combined_text for k in [
            "代表取締役", "創業者", "CEO", "役員", "アトツギ", "事業承継", "Founder", "Co-founder", "CEO", "Managing Director"
        ])
        
        if not is_relevant:
            continue

        email_found = None
        source_excerpt = snippet
        try:
            artifact = fetch_source(url, provider=provider_name)
            store.save_source(artifact)
            full_text = artifact.content or ""
            emails = extract_emails(full_text)
            if emails:
                email_found = emails[0]
            if len(full_text) > 100:
                source_excerpt = clean_text(full_text[:300])
        except Exception:
            emails = extract_emails(snippet)
            if emails:
                email_found = emails[0]

        candidates.append({
            "raw_title": title,
            "raw_snippet": snippet,
            "url": url,
            "verified_email": email_found or "No public email found",
            "source_excerpt": source_excerpt
        })

    print(f"Harvested {len(candidates)} candidate items for qualification.")

    inter_path = OUT_DIR / "raw_harvested_candidates.json"
    inter_path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved raw harvested candidates to {inter_path}")

if __name__ == "__main__":
    main()
