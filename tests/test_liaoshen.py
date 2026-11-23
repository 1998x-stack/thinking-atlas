"""Liaoshen case study contracts: evidence IDs, URLs and the published article."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "posts" / "history" / "liaoshen-strategic-decisions"

class LiaoshenEvidenceTests(unittest.TestCase):
    def test_article_evidence_cross_references(self):
        evidence = json.loads((FOLDER / "evidence.json").read_text(encoding="utf-8"))
        html = (FOLDER / "index.html").read_text(encoding="utf-8")
        sources = {item["id"]: item for item in evidence["sources"]}
        self.assertGreaterEqual(len(sources), 10)
        self.assertIn("部分核验", html)
        for item in evidence["verified_claims"]:
            for sid in item["source_ids"]:
                self.assertIn(sid, sources)
        for sid, source in sources.items():
            self.assertIn(source["url"], html)
        self.assertIn("UNVERIFIED", {x["status"] for x in evidence["verified_claims"]})
        self.assertIn("SUPPORTED", {x["status"] for x in evidence["verified_claims"]})

    def test_source_bundle_integrity(self):
        manifest = json.loads((ROOT / "content" / "posts.json").read_text(encoding="utf-8"))
        post = next(p for p in manifest if p["slug"] == "liaoshen-strategic-decisions")
        self.assertEqual(post["research_status"], "partial")
        self.assertEqual(post["category"], "history")
        for filename in ["index.html", "source.md", "evidence.json", "assets/mechanism.svg", "assets/decision-matrix.svg", "assets/article.css"]:
            self.assertTrue((FOLDER / filename).is_file())

if __name__ == "__main__":
    unittest.main()
