"""Contract tests for the Thinking Atlas static publisher."""
import json
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_site
import validate_site


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_site.publish(build_site.DEFAULT_BASE)
        cls.categories,cls.posts=build_site.read_manifest()

    def test_complete_migration(self):
        self.assertEqual(14,len(self.posts))
        self.assertEqual(7,len(self.categories))
        self.assertEqual(14,len({p["slug"] for p in self.posts}))

    def test_sources_and_research_states(self):
        for post in self.posts:
            folder=ROOT/"posts"/post["category"]/post["slug"]
            self.assertTrue((folder/"index.html").is_file())
            self.assertTrue((folder/"source.md").is_file())
            self.assertTrue((folder/"evidence.json").is_file())
            e=json.loads((folder/"evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(post["research_status"],e["research_status"])

    def test_manifest_generated_routes(self):
        self.assertTrue((ROOT/"_site/index.html").exists())
        self.assertTrue((ROOT/"_site/topics/index.html").exists())
        for cat in self.categories:
            self.assertTrue((ROOT/"_site/categories"/cat["slug"]/"index.html").exists())

    def test_rss_and_sitemap(self):
        root=ET.parse(ROOT/"_site/feed.xml").getroot()
        entries=root.findall("./channel/item")
        self.assertEqual(14,len(entries))
        self.assertEqual(14,len({n.findtext("guid") for n in entries}))
        maproot=ET.parse(ROOT/"_site/sitemap.xml").getroot()
        self.assertGreaterEqual(len(list(maproot)),len(self.posts)+len(self.categories))

    def test_no_source_leak(self):
        self.assertEqual([],[str(p) for p in (ROOT/"_site").rglob("*.md")])
        self.assertEqual([],[str(p) for p in (ROOT/"_site").rglob("evidence.json")])

    def test_deep_link_and_svg_validation(self):
        cats,posts,errors=validate_site.validate_sources()
        errors+=validate_site.validate_built(posts,cats)
        self.assertEqual([],errors)


if __name__=="__main__":
    unittest.main()
