#!/usr/bin/env python3
"""
Automated DNS, MX, Syntax, and Reachability Verification Engine for 100 Japanese Entrepreneurs.
"""
import json
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "japan100"

def check_mx(domain: str) -> list[str]:
    try:
        res = subprocess.run(["dig", "+short", "MX", domain], capture_output=True, text=True, timeout=5, check=False)
        return [l.strip() for l in res.stdout.splitlines() if l.strip()]
    except Exception:
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

def verify_single_contact(item: dict) -> dict:
    email = item["verified_direct_email"]
    domain = email.split("@")[-1].lower()
    
    mx = check_mx(domain)
    resolves = domain_resolves(domain)
    
    # Validation checks
    valid_syntax = "@" in email and "." in domain
    no_generic = not any(email.startswith(p) for p in ["info@", "contact@", "hello@", "support@", "press@", "admin@"])
    no_webmail = not any(domain.endswith(d) for d in ["gmail.com", "yahoo.com", "yahoo.co.jp"])

    passed_all = valid_syntax and resolves and bool(mx) and no_generic and no_webmail

    return {
        "candidate_id": item["candidate_id"],
        "name": item["full_name_romaji"],
        "company": item["company_name"],
        "email": email,
        "domain": domain,
        "mx_records": mx,
        "domain_resolves": resolves,
        "syntax_valid": valid_syntax,
        "non_generic": no_generic,
        "non_webmail": no_webmail,
        "verification_status": "VERIFIED_ACTIVE_BUSINESS_ROUTE" if passed_all else "CHECK_REQUIRED"
    }

def main():
    json_path = OUT_DIR / "japan_100_direct_emails.json"
    if not json_path.exists():
        print(f"Error: {json_path} does not exist.")
        sys.exit(1)

    items = json.loads(json_path.read_text(encoding="utf-8"))
    print(f"Running automated MX & DNS resolution verification across all {len(items)} emails...")

    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(verify_single_contact, item) for item in items]
        for f in as_completed(futures):
            results.append(f.result())

    # Sort results
    results.sort(key=lambda x: int(x["candidate_id"].split("-")[-1]))

    verified_count = sum(1 for r in results if r["verification_status"] == "VERIFIED_ACTIVE_BUSINESS_ROUTE")
    print(f"Verification completed: {verified_count}/{len(results)} fully verified with active MX records & domain resolution.")

    # Save detailed verification report
    report_json = OUT_DIR / "japan_100_mx_verification_report.json"
    report_json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved MX & DNS verification report to {report_json}")

if __name__ == "__main__":
    main()
