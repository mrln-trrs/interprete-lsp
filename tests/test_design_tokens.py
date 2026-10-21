import json
from pathlib import Path
import re
import unittest
from scripts import check_contrast, export_tokens

ROOT = Path(__file__).resolve().parents[1]


class TestDesignTokens(unittest.TestCase):
    def setUp(self):
        self.css = (ROOT / "static" / "styles.css").read_text(encoding="utf-8-sig")
        self.tokens = export_tokens.build(self.css)

    def test_exported_file_matches_css(self):
        saved = json.loads((ROOT / "docs" / "design" / "tokens.dtcg.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, json.loads(json.dumps(self.tokens)))

    def test_dtcg_shapes_and_aliases_resolve(self):
        for group, members in self.tokens.items():
            if group.startswith("$"):
                continue
            for name, token in members.items():
                with self.subTest(token=f"{group}.{name}"):
                    value = token["$value"]
                    if isinstance(value, str):
                        target_group, target = re.fullmatch(r"\{([a-z]+)\.([a-z0-9-]+)\}", value).groups()
                        self.assertIn("$value", self.tokens[target_group][target])
                    elif token["$type"] == "color":
                        self.assertEqual(value["colorSpace"], "srgb")
                        self.assertTrue(all(0 <= c <= 1 for c in value["components"]))
                        self.assertEqual(value["hex"], "#" + "".join(f"{round(c * 255):02x}" for c in value["components"]))
                    else:
                        self.assertEqual(token["$type"], "dimension")
                        self.assertIn(value["unit"], ("px", "rem"))

    def test_contrast_script_uses_css_values(self):
        colors = {name: token["$value"]["hex"] for name, token in self.tokens["color"].items() if isinstance(token["$value"], dict)}
        mapping = {"surface": "surface", "primary": "text-primary", "secondary": "text-secondary", "accent": "accent",
                   "accent-secondary": "accent-secondary", "warning": "warning", "danger": "danger"}
        for contrast_name, css_name in mapping.items():
            with self.subTest(token=contrast_name):
                self.assertEqual(check_contrast.TOKENS[contrast_name].lower(), colors[css_name])

    def test_unknown_alias_rejected(self):
        with self.assertRaises(ValueError):
            export_tokens.build(":root { --a:var(--missing); }")


if __name__ == "__main__":
    unittest.main()
