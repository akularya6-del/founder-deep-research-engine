from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .real_retrieval import SearchResult, SourceArtifact, as_json


class EvidenceStore:
    """Filesystem evidence store. It never invents a source or contact."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.sources_dir = self.root / "sources" / "retrieved"
        self.events_path = self.root / "logs" / "retrieval_events.jsonl"
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        self.events_path.parent.mkdir(parents=True, exist_ok=True)

    def _event(self, event: dict[str, Any]) -> None:
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def save_search_results(self, results: list[SearchResult]) -> None:
        for result in results:
            self._event({"event_type": "SEARCH_RESULT", "provider": result.provider, **as_json(result)})

    def save_source(self, artifact: SourceArtifact) -> Path:
        destination = self.sources_dir / f"{artifact.source_id}.json"
        destination.write_text(json.dumps(as_json(artifact), ensure_ascii=False, indent=2), encoding="utf-8")
        self._event({
            "event_type": "SOURCE_RETRIEVED",
            "source_id": artifact.source_id,
            "url": artifact.url,
            "retrieved_at": artifact.retrieved_at,
            "content_hash": artifact.content_hash,
            "provider": artifact.provider,
            "http_status": artifact.http_status,
        })
        return destination

    def has_source(self, source_id: str) -> bool:
        return (self.sources_dir / f"{source_id}.json").exists()

    def load_source(self, source_id: str) -> dict[str, Any]:
        path = self.sources_dir / f"{source_id}.json"
        if not path.exists():
            raise FileNotFoundError(source_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def save_claim(self, claim: dict[str, Any]) -> None:
        required = {"claim_id", "claim", "source_ids", "entity_ids", "exact_excerpt"}
        missing = required - claim.keys()
        if missing:
            raise ValueError(f"Claim missing required fields: {sorted(missing)}")
        if not isinstance(claim["source_ids"], list) or not claim["source_ids"]:
            raise ValueError("Claim must reference at least one retrieved source.")
        if claim.get("directness") == "inferred":
            raise ValueError("Inferred claims cannot enter the evidence store.")
        for source_id in claim["source_ids"]:
            source = self.load_source(source_id)
            excerpt = claim["exact_excerpt"]
            if excerpt not in source["text"]:
                raise ValueError(f"Claim excerpt is not present in source artifact {source_id}")
        path = self.root / "results" / "evidence" / "claims.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(claim, ensure_ascii=False) + "\n")
        self._event({"event_type": "CLAIM_SAVED", "claim_id": claim["claim_id"], "source_ids": claim["source_ids"]})
