# Real Retrieval Layer

The active package now includes a real retrieval layer. It has no synthetic fallback.

## Configure one search provider

Use exactly one:

    export RESEARCH_SEARCH_PROVIDER=tavily
    export TAVILY_API_KEY=...

or:

    export RESEARCH_SEARCH_PROVIDER=firecrawl
    export FIRECRAWL_API_KEY=...

or self-hosted SearXNG:

    export RESEARCH_SEARCH_PROVIDER=searxng
    export SEARXNG_ENDPOINT=http://127.0.0.1:8080

## Run a real retrieval smoke test

    python3 run_real_research.py --fetch https://example.com

This stores a source artifact under sources/retrieved and appends retrieval evidence to logs/retrieval_events.jsonl.

## Run live search and fetch

    python3 run_real_research.py --query "specialty packaging founder India export" --limit 5

A live search requires a configured provider. If none is configured, the program exits with a configuration error and creates no fake output.

## Important boundary

This layer retrieves and stores real evidence. It does not claim a founder is verified merely because a page was fetched. Candidate verification must create claim records with exact excerpts, independent source families, entity resolution, and public contact evidence before the final QA gate can release a candidate.

## Contact recheck layer

Generic inboxes such as `info@`, `contact@`, `hello@`, `admin@`, `support@`, `office@`, `press@`, and `media@` are rejected as primary outreach contacts. The recheck engine re-fetches the cited source, checks exact-value persistence, validates email syntax, confirms the domain resolves, confirms MX records exist, and records whether the source remains reachable.

`public_route_verified` means that the route is source-backed and its domain accepts mail. It does not claim that a specific mailbox is active. No mailbox probing or email sending is performed.

Run it with:

    PYTHONPATH=. .live-venv/bin/python execution/recheck_contacts.py

The result is written to `results/pilot10/contact_recheck.json`.
