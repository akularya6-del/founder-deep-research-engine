<div align="center">

# founder-deep-research-engine

**Deterministic, source-grounded deep research and market entity resolution engine with pluggable search providers (Tavily, Firecrawl, SearXNG).**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Search Providers](https://img.shields.io/badge/Providers-Tavily_|_Firecrawl_|_SearXNG-blue?style=flat-square)
![Verification](https://img.shields.io/badge/Verification-Anti--Hallucination_Audit-success?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

</div>

---

## 📌 Overview

**founder-deep-research-engine** is an autonomous market research framework that retrieves, resolves, and verifies corporate entity and leadership data from live web sources. 

Unlike naive LLM web scrapers that hallucinate contacts or summarize unverified snippets, this engine enforces strict multi-source cross-examination:
- Every entity claim requires exact source text excerpts with verified URL timestamps.
- Generic mailboxes (`info@`, `admin@`, `support@`) are automatically flagged and discarded.
- Domain resolutions, DNS MX record validations, and live HTTP reachability checks are performed systematically.

---

## ✨ Features

- **Multi-Provider Web Retrieval**: Modular adapters for Tavily, Firecrawl, and self-hosted SearXNG with zero synthetic fallbacks.
- **Evidence Schema Validation**: Strict Pydantic schemas validating entity identity, verified citations, and resolution paths.
- **Automated Contact Verification Layer**: Verifies syntax, DNS MX records, and public route persistence without invasive mailbox probing.
- **Configurable Industry Playbooks**: Domain-specific query generation templates and entity-matching logic.

---

## 🏗️ Architecture

```
research-system/
├── engine/             # Core retrieval state machine and query planner
├── execution/          # Contact recheckers, domain validators, and QA gates
├── configs/            # Provider and environment definitions
├── schemas/            # Pydantic schemas for claims, sources, and entities
├── industry-playbooks/ # Niche-specific research templates
└── run_real_research.py # Main CLI runner
```

---

## 🚀 Getting Started

### 1. Installation

```bash
git clone https://github.com/akularya6-del/founder-deep-research-engine.git
cd founder-deep-research-engine

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-live.txt
```

### 2. Configure a Provider

Choose and export your preferred search provider:

```bash
# Option A: Tavily
export RESEARCH_SEARCH_PROVIDER=tavily
export TAVILY_API_KEY="your-key-here"

# Option B: Firecrawl
export RESEARCH_SEARCH_PROVIDER=firecrawl
export FIRECRAWL_API_KEY="your-key-here"

# Option C: Self-hosted SearXNG
export RESEARCH_SEARCH_PROVIDER=searxng
export SEARXNG_ENDPOINT="http://127.0.0.1:8080"
```

### 3. Run a Research Query

```bash
python3 run_real_research.py --query "specialty packaging founders India" --limit 5
```

---

## 📄 License

This repository is licensed under the [MIT License](LICENSE).
