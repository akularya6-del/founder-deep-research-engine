from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from engine.evidence_store import EvidenceStore
from engine.integrity_gate import IntegrityFailure
from engine.real_retrieval import RetrievalConfigurationError, fetch_source, provider_from_environment


def main() -> int:
    parser = argparse.ArgumentParser(description="Live retrieval entry point; refuses synthetic fallback.")
    parser.add_argument("--query", action="append", help="Search query. Repeat for multiple queries.")
    parser.add_argument("--fetch", action="append", help="Explicit public URL to fetch. Repeat for multiple URLs.")
    parser.add_argument("--provider", choices=["tavily", "firecrawl", "searxng"], help="Search provider.")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    store = EvidenceStore(root)
    queries = args.query or []
    urls = args.fetch or []

    if not queries and not urls:
        parser.error("Provide --query and/or --fetch. No automatic synthetic data is permitted.")

    try:
        provider = provider_from_environment(args.provider) if queries else None
        if provider:
            for query in queries:
                results = provider.search(query, limit=args.limit)
                store.save_search_results(results)
                print(json.dumps({"query": query, "results": len(results), "provider": provider.name}))
                for result in results:
                    try:
                        artifact = fetch_source(result.url, provider=provider.name)
                        store.save_source(artifact)
                    except Exception as exc:
                        print(json.dumps({"url": result.url, "status": "fetch_failed", "error": str(exc)}))
        for url in urls:
            try:
                artifact = fetch_source(url)
                store.save_source(artifact)
                print(json.dumps({"url": url, "source_id": artifact.source_id, "status": "stored"}))
            except Exception as exc:
                # A bad URL must not discard successfully retrieved artifacts.
                print(json.dumps({"url": url, "status": "fetch_failed", "error": str(exc)}))
    except RetrievalConfigurationError as exc:
        print(f"CONFIGURATION_ERROR: {exc}")
        return 2
    except IntegrityFailure as exc:
        print(f"INTEGRITY_FAILURE: {exc}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
