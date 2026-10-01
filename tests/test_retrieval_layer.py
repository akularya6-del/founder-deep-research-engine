from __future__ import annotations

import json
import threading
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from engine.evidence_store import EvidenceStore
from engine.integrity_gate import IntegrityFailure, assert_public_contact
from engine.real_retrieval import fetch_source


class FakeResponse:
    status = 200

    class Headers:
        def get(self, name, default=None):
            return "text/html; charset=utf-8" if name == "Content-Type" else default

    headers = Headers()

    def read(self, _limit=None):
        return b"<html><head><title>Factory Profile</title></head><body><p>Acme operates a plant in Pune.</p><p>Press contact: media@example.test</p></body></html>"

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class RetrievalLayerTests(unittest.TestCase):
    def test_fetch_hash_and_store_claim_lineage(self):
        url = "https://example.test/profile"
        with patch("engine.real_retrieval.urlopen", return_value=FakeResponse()):
            with TemporaryDirectory() as tmp:
                artifact = fetch_source(url)
                self.assertEqual(artifact.http_status, 200)
                self.assertIn("Acme operates", artifact.text)
                store = EvidenceStore(tmp)
                store.save_source(artifact)
                store.save_claim({
                    "claim_id": "CLM-1",
                    "claim": "Acme operates a plant in Pune.",
                    "source_ids": [artifact.source_id],
                    "entity_ids": ["C-1"],
                    "exact_excerpt": "Acme operates a plant in Pune.",
                    "directness": "direct",
                })
                self.assertTrue(store.has_source(artifact.source_id))

    def test_pattern_contact_is_rejected(self):
        with self.assertRaises(IntegrityFailure):
            assert_public_contact({
                "value": "press@example.com",
                "inferred": False,
                "public_purpose": True,
            }, "Contact: press@example.com")
        with self.assertRaises(IntegrityFailure):
            assert_public_contact({
                "value": "hello@example.com",
                "inferred": False,
                "public_purpose": True,
            }, "No email is published here.")

    def test_missing_excerpt_is_rejected(self):
        with TemporaryDirectory() as tmp:
            store = EvidenceStore(tmp)
            with self.assertRaises(ValueError):
                store.save_claim({
                    "claim_id": "CLM-2",
                    "claim": "Unsupported",
                    "source_ids": [],
                    "entity_ids": ["C-1"],
                    "exact_excerpt": "not present",
                })


if __name__ == "__main__":
    unittest.main()
