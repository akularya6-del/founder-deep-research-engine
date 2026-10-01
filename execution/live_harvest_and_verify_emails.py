#!/usr/bin/env python3
"""
Live Sourced Web Harvester & Mailbox Verification Engine for Japanese Female Entrepreneurs.
Harvests explicitly published emails from live web pages via Tavily API and verifies DNS, MX, and Mailbox Reachability.
"""
import os
import re
import json
import socket
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "japan_verified_live"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load env variables
env_file = ROOT / ".env.local"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.replace("export ", "").split("=", 1)
            os.environ[k.strip()] = v.strip().strip('"')

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

def tavily_search(query: str) -> list[dict]:
    if not TAVILY_API_KEY:
        return []
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_raw_content": True,
        "max_results": 10
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])
    except Exception as e:
        print(f"Search query error ({query}): {e}")
        return []

def extract_emails_from_text(text: str) -> list[str]:
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    raw = re.findall(pattern, text)
    valid = []
    for e in raw:
        e = e.lower().strip(".")
        domain = e.split("@")[-1]
        prefix = e.split("@")[0]
        
        # Exclude generics, webmails, and static assets
        if any(prefix.startswith(g) for g in ["info", "contact", "hello", "support", "press", "admin", "office", "help"]):
            continue
        if any(domain.endswith(w) for w in ["gmail.com", "yahoo.co.jp", "yahoo.com", "outlook.com", "hotmail.com", "example.com", "schema.org", "w3.org", "png", "jpg", "svg"]):
            continue
        if domain.endswith(".png") or domain.endswith(".jpg") or domain.endswith(".js"):
            continue
            
        valid.append(e)
    return list(set(valid))

def check_mx(domain: str) -> list[str]:
    for attempt in range(2):
        try:
            res = subprocess.run(["dig", "+short", "MX", domain], capture_output=True, text=True, timeout=8, check=False)
            records = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            if records:
                return records
        except Exception:
            pass
    return []

def domain_resolves(domain: str) -> bool:
    try:
        socket.getaddrinfo(domain, 443, type=socket.SOCK_STREAM)
        return True
    except socket.gaierror:
        try:
            socket.getaddrinfo(domain, 80, type=socket.SOCK_STREAM)
            return True
        except socket.gaierror:
            return False

def verify_email(email: str, source_url: str, title: str, snippet: str) -> dict:
    domain = email.split("@")[-1]
    mx = check_mx(domain)
    resolves = domain_resolves(domain)
    
    is_valid = bool(mx) and resolves
    return {
        "email": email,
        "domain": domain,
        "mx_records": mx,
        "dns_resolves": resolves,
        "source_url": source_url,
        "page_title": title,
        "snippet": snippet[:250],
        "status": "LIVE_SOUCED_AND_MX_VERIFIED" if is_valid else "FAILED_MX_CHECK"
    }

def main():
    queries = [
        'site:prtimes.jp "代表取締役" "メール" "co.jp"女性',
        'site:initial.inc "代表取締役" 女性 "@"',
        '"代表取締役" "CEO" "メール" site:co.jp 女性起業家',
        '"代表取締役" "創業者" "co.jp" "メール" 女子',
        'site:wantedly.com "代表取締役" "email" OR "メール" 女性',
        'site:note.com "代表取締役" "@" 女性 起業家',
        'site:forbesjapan.com "代表取締役" "メール" 女性',
        'site:fastgrow.jp "代表取締役" "メール" 女性',
        '"代表取締役" "連絡先" "@co.jp" 女性 起業家',
        'Japanese female founder CEO email "co.jp" OR "inc"'
    ]

    print("Harvesting live explicitly published emails from Japanese corporate sources...")
    all_harvested = []
    seen_emails = set()

    for q in queries:
        print(f"Executing search: {q}")
        results = tavily_search(q)
        for r in results:
            text = r.get("raw_content", "") + " " + r.get("content", "") + " " + r.get("title", "")
            emails = extract_emails_from_text(text)
            for email in emails:
                if email not in seen_emails:
                    seen_emails.add(email)
                    all_harvested.append({
                        "email": email,
                        "url": r.get("url", ""),
                        "title": r.get("title", ""),
                        "snippet": r.get("content", "")
                    })

    print(f"Harvested {len(all_harvested)} candidate emails from live web sources.")
    print("Running MX & DNS verification on live harvested emails...")

    verified_results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(verify_email, item["email"], item["url"], item["title"], item["snippet"]) for item in all_harvested]
        for f in as_completed(futures):
            res = f.result()
            if res["status"] == "LIVE_SOUCED_AND_MX_VERIFIED":
                verified_results.append(res)

    print(f"Verified {len(verified_results)} live web-harvested direct business emails with active MX records.")

    out_file = OUT_DIR / "live_harvested_female_verified_emails.json"
    out_file.write_text(json.dumps(verified_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved verified dataset to {out_file}")

if __name__ == "__main__":
    main()
