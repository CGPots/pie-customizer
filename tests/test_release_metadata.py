import ast
import unittest
from pathlib import Path

from pie_customizer import ADDON_VERSION, bl_info


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTest(unittest.TestCase):
    def test_legacy_metadata_matches_release_identity(self):
        self.assertEqual(bl_info["name"], "Pie Customizer")
        self.assertEqual(bl_info["author"], "cgPots")
        self.assertEqual(bl_info["version"], (1, 1, 3))
        self.assertEqual(ADDON_VERSION, (1, 1, 3))
        self.assertEqual(bl_info["blender"], (4, 2, 0))

    def test_extension_manifest_contains_release_identity(self):
        manifest = (ROOT / "pie_customizer" / "blender_manifest.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn('id = "pie_customizer"', manifest)
        self.assertIn('version = "1.1.3"', manifest)
        self.assertIn('tags = ["User Interface", "3D View"]', manifest)
        self.assertIn('maintainer = "cgPots"', manifest)
        self.assertIn('"SPDX:GPL-3.0-or-later"', manifest)
        self.assertIn('blender_version_min = "4.2.0"', manifest)
        self.assertIn(
            'website = "https://github.com/CGPots/pie-customizer"',
            manifest,
        )
        self.assertIn(
            'support = "https://github.com/CGPots/pie-customizer/issues"',
            manifest,
        )
        self.assertIn('files = "Import and export JSON presets"', manifest)

    def test_release_package_contains_full_license(self):
        license_text = (ROOT / "pie_customizer" / "LICENSE.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("GNU GENERAL PUBLIC LICENSE", license_text)
        self.assertIn("Version 3, 29 June 2007", license_text)

    def test_release_package_has_no_development_diagnostics(self):
        package = ROOT / "pie_customizer"
        self.assertFalse((package / "diagnostics.py").exists())
        self.assertFalse(any(package.rglob("test_*.py")))

    def test_release_source_has_no_dynamic_code_execution(self):
        forbidden = {"exec", "eval", "compile"}
        for path in (ROOT / "pie_customizer").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            calls = {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            self.assertFalse(
                calls & forbidden,
                f"{path.name} contains forbidden calls: {calls & forbidden}",
            )


if __name__ == "__main__":
    unittest.main()
