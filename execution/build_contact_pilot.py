#!/usr/bin/env python3
"""Build a small, source-backed contact pilot from retrieved official pages.

The records are intentionally explicit: this script does not invent contacts or
derive email patterns. It selects only values already present in stored source
artifacts and fails closed if a required excerpt is missing.
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from engine.integrity_gate import assert_candidate, assert_no_synthetic_text, assert_public_contact


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources" / "retrieved"
OUT_DIR = ROOT / "results" / "pilot10"


PEOPLE = [
    {"founder_id": "F-PILOT-001", "company_id": "C-UFLEX", "person": "Ashok Chaturvedi", "company": "UFlex Limited", "role": "Chairman & Managing Director", "industry": "Packaging / Manufacturing", "identity_url": "https://www.uflexltd.com/pdf/contact-details-of-kmps.pdf", "contact_url": "https://www.uflexltd.com/pdf/contact-details-of-kmps.pdf", "contact_type": "company_general", "contact": "secretarial@uflexltd.com", "purpose": "Company secretarial / listed-company disclosure route"},
    {"founder_id": "F-PILOT-002", "company_id": "C-BIOCON", "person": "Kiran Mazumdar Shaw", "company": "Biocon Limited", "role": "Executive Chairperson", "industry": "Pharma / Biotechnology", "identity_url": "https://www.biocon.com/docs/Initmation_Change_in_policy_signed-20230214.pdf", "contact_url": "https://www.biocon.com/docs/Initmation_Change_in_policy_signed-20230214.pdf", "contact_type": "founder_direct", "contact": "kiran.mazumdar@biocon.com", "purpose": "Public company leadership contact in official filing"},
    {"founder_id": "F-PILOT-003", "company_id": "C-SUNPHARMA", "person": "Dilip Shanghvi", "company": "Sun Pharmaceutical Industries Limited", "role": "Founder and Executive Chairman", "industry": "Pharma", "identity_url": "https://sunpharma.com/board-of-directors/", "contact_url": "https://archives.nseindia.com/corporate/SUNPHARMA_20042021111153_Sunpharma.pdf", "contact_type": "founder_direct", "contact": "dilip.shanghvi@sunpharma.com", "purpose": "Public contact in exchange filing"},
    {"founder_id": "F-PILOT-004", "company_id": "C-BAJAJ-AUTO", "person": "Rajiv Bajaj", "company": "Bajaj Auto Limited", "role": "Managing Director", "industry": "Manufacturing / Mobility", "identity_url": "https://www.bajajauto.com/investors/investor-services", "contact_url": "https://www.bajajauto.com/investors/investor-services", "contact_type": "investor_relations", "contact": "ppgokhale@bajajauto.co.in", "purpose": "Official Regulation 30(5) company contact route"},
    {"founder_id": "F-PILOT-005", "company_id": "C-HIMADRI", "person": "Anurag Choudhary", "company": "Himadri Speciality Chemical Limited", "role": "Founder, CMD & CEO", "industry": "Specialty Chemicals / New Energy Materials", "identity_url": "https://www.himadri.com/anurag-choudhary.php", "contact_url": "https://www.himadri.com/pdf/annual-report-31-03-2022-2022.pdf", "contact_type": "investor_relations", "contact": "investors@himadri.com", "purpose": "Official founder-linked business responsibility / investor route"},
    {"founder_id": "F-PILOT-006", "company_id": "C-UNI-AUTOMATION", "person": "V. K. Mahajan", "company": "Uni Automation India Pvt. Ltd.", "role": "Founder & Managing Director", "industry": "Industrial Automation", "identity_url": "https://uniautomation.com/our-leadership.php", "contact_url": "https://defence.h5mag.com/global_defence_technology_jun20/uni-automation", "contact_type": "company_general", "contact": "sales@uniautomation.com", "purpose": "Published sales route for the company"},
    {"founder_id": "F-PILOT-007", "company_id": "C-CHEMBOND", "person": "Nirmal V. Shah", "company": "Chembond Chemicals Limited", "role": "Chairman and Managing Director", "industry": "Chemicals", "identity_url": "https://www.chembondindia.com/wp-content/uploads/2025/07/Information-Memorandum.pdf", "contact_url": "https://www.chembondindia.com/wp-content/uploads/2025/07/Information-Memorandum.pdf", "contact_type": "company_general", "contact": "cs@chembondindia.com", "purpose": "Official company secretary route in listing memorandum"},
    {"founder_id": "F-PILOT-008", "company_id": "C-ERNST", "person": "Nikhil Aggarwal", "company": "Ernst Pharmacia", "role": "CEO & Founder", "industry": "Pharma", "identity_url": "https://ernstpharmacia.com/our-founder/", "contact_url": "https://ernstpharmacia.com/contact-us/", "contact_type": "company_general", "contact": "network@ernstpharmacia.com", "purpose": "Official company network / business contact route"},
    {"founder_id": "F-PILOT-009", "company_id": "C-QCI", "person": "Mukesh Shah", "company": "Quality Speciality Chemicals Pvt. Ltd.", "role": "Founder", "identity_terms": ["Mukesh Shah", "Founded by"], "industry": "Specialty Chemicals", "identity_url": "https://qciindia.com/about-us/", "contact_url": "https://www.tofler.in/quality-speciality-chemicals-llp/company/AAC-5837", "contact_type": "company_general", "contact": "mukesh@qci.in", "purpose": "Named business email in public company directory"},
    {"founder_id": "F-PILOT-010", "company_id": "C-FINEOTEX", "person": "Surendrakumar Tibrewala", "company": "Fineotex Chemical Limited", "role": "Founder / Chairman & Managing Director", "identity_terms": ["Founded in 1979 by Mr. Surendra Tibrewala"], "industry": "Specialty Chemicals / Manufacturing", "identity_url": "https://fineotex.com/about-us/", "contact_url": "https://www.moneycontrol.com/company-facts/fineotexchem/management/FC02", "contact_type": "investor_relations", "contact": "investor.relations@fineotex.com", "purpose": "Public investor-relations route tied to company leadership"},
]


def load_sources() -> dict[str, dict]:
    by_url: dict[str, dict] = {}
    for path in SOURCE_DIR.glob("SRC-*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        url = data.get("url")
        text = data.get("text", "")
        if not url or not text or text.startswith("%PDF"):
            continue
        previous = by_url.get(url)
        if previous is None or path.stat().st_mtime > previous["_mtime"]:
            data["_mtime"] = path.stat().st_mtime
            by_url[url] = data
    return by_url


def excerpt(text: str, terms: list[str], radius: int = 300) -> str:
    positions = []
    for term in terms:
        pattern = r"\s+".join(re.escape(token) for token in term.split())
        match = re.search(pattern, text, flags=re.IGNORECASE)
        positions.append(match.start() if match else -1)
    if any(pos < 0 for pos in positions):
        raise RuntimeError(f"Required evidence terms missing: {terms}")
    start = max(0, min(positions) - radius)
    end = min(len(text), max(positions) + len(max(terms, key=len)) + radius)
    return text[start:end].strip()


def main() -> None:
    sources = load_sources()
    candidates, contacts, claims = [], [], []
    for item in PEOPLE:
        identity = sources.get(item["identity_url"])
        contact_source = sources.get(item["contact_url"])
        if not identity or not contact_source:
            raise RuntimeError(f"Missing retrieved source for {item['person']}")
        identity_excerpt = excerpt(identity["text"], item.get("identity_terms", [item["person"], item["role"]]))
        contact_excerpt = excerpt(contact_source["text"], [item["contact"]])
        for value in (identity_excerpt, contact_excerpt):
            assert_no_synthetic_text(value)
        contact = {
            "contact_id": f"CT-{item['founder_id']}", "entity_id": item["founder_id"], "type": item["contact_type"],
            "value": item["contact"], "source_id": contact_source["source_id"], "public_purpose": True,
            "inferred": False, "freshness": "recent", "suppressed": False,
            "source_url": item["contact_url"], "purpose": item["purpose"], "exact_excerpt": contact_excerpt,
        }
        assert_public_contact(contact, contact_source["text"])
        candidate = {
            "founder_id": item["founder_id"], "company_id": item["company_id"], "name": item["person"],
            "company": item["company"], "role": item["role"], "industry": item["industry"], "status": "verified",
            "evidence_grade": "A", "contact_status": "public_route_verified",
        }
        candidate_claims = [
            {"claim_id": f"CL-{item['founder_id']}-IDENTITY", "entity_ids": [item["founder_id"], item["company_id"]], "claim_type": "identity_role", "claim": f"{item['person']} is listed as {item['role']} at {item['company']}.", "directness": "direct", "source_ids": [identity["source_id"]], "exact_excerpt": identity_excerpt},
            {"claim_id": f"CL-{item['founder_id']}-CONTACT", "entity_ids": [item["founder_id"], item["company_id"]], "claim_type": "public_contact", "claim": f"The official public contact route is {item['contact']}.", "directness": "direct", "source_ids": [contact_source["source_id"]], "exact_excerpt": contact_excerpt},
        ]
        assert_candidate(candidate, candidate_claims, {identity["source_id"]: identity, contact_source["source_id"]: contact_source}, [contact])
        candidates.append(candidate); contacts.append(contact); claims.extend(candidate_claims)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    (OUT_DIR / "founders.json").write_text(json.dumps({"generated_at": now, "status": "verified_pilot", "founders": candidates}, indent=2), encoding="utf-8")
    (OUT_DIR / "contacts.json").write_text(json.dumps({"generated_at": now, "status": "verified_pilot", "contacts": contacts}, indent=2), encoding="utf-8")
    (OUT_DIR / "claims.jsonl").write_text("\n".join(json.dumps(c) for c in claims) + "\n", encoding="utf-8")
    with (OUT_DIR / "contact_pilot.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "company", "role", "industry", "contact", "contact_type", "source_url", "source_id", "evidence_grade"])
        writer.writeheader()
        for item, contact in zip(candidates, contacts):
            writer.writerow({**{key: item[key] for key in ["name", "company", "role", "industry"]}, "contact": contact["value"], "contact_type": contact["type"], "source_url": contact["source_url"], "source_id": contact["source_id"], "evidence_grade": item["evidence_grade"]})
    lines = ["# Verified Contact Pilot (10)", "", f"Generated: {now}", "", "All rows passed the integrity gate. Contacts are public professional routes; none were inferred or pattern-generated.", "", "| # | Person | Company | Role | Public route | Evidence |", "|---:|---|---|---|---|---|"]
    for idx, (item, contact) in enumerate(zip(candidates, contacts), 1):
        lines.append(f"| {idx} | {item['name']} | {item['company']} | {item['role']} | `{contact['value']}` ({contact['type']}) | [{contact['source_id']}]({contact['source_url']}) |")
    lines += ["", "## Operating note", "", "A company-general, secretarial, or investor-relations route is explicitly labeled. The contact route is not represented as a personal inbox unless the cited official source identifies it that way."]
    (OUT_DIR / "pilot10_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "verified_pilot", "founders": len(candidates), "contacts": len(contacts), "output": str(OUT_DIR)}))


if __name__ == "__main__":
    main()
